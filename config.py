# 关于judger的配置
import asyncio
import uuid
from dataclasses import asdict

import aiohttp

import utils
from logger import logger
import aiosqlite
from typing import Optional, List, Dict

import service
from entry import Robot, Trace, CheckpointToProblem, CheckpointsPackage

jid: str = "my"  # judger的id
name: str = "我的judger"  # judger的name
remote: str = "http://localhost:5000"  # 访问该judger需要使用的地址
port: int = 5000  # 监听端口
host: str = "0.0.0.0"  # 监听ip
key: str = "coj443523"  # 用于与coj服务端通信的密钥
server: str = "http://localhost:8080/judger"  # coj服务端的请求地址
create_type: int = 1  # 添加robot的时候的类型
keepalive_time: int = 60 * 60  # 每一个小时执行一次保活任务
ping_time: int = 30  # 每30秒向coj服务端ping一次

# coj的全局变量
robots: Dict[str, Robot] = {}
database_conn: Optional[aiosqlite.Connection] = None

# 一些常量
robot_status_destroy: int = -4  # robot准备销毁，该状态仅用在judger代码里
robot_status_no_user: int = -3  # robot已经创建，但未绑定账号密码
robot_status_offline: int = 0  # robot离线，一般是judger刚启动时已经保存的robot没能登录
robot_status_ok: int = 1  # robot准备就绪
robot_status_working: int = 2  # robot正在评测

trace_status_ok: int = 0  # 投递成功
trace_status_error: int = 2  # 投递时发生错误

response_status_ok: int = 200
response_status_space: int = 100
response_status_msg: int = 102
response_status_error: int = 105

"""
0-waiting，正在等待
1-judging，正在评测
2-accepted，AC
3-wrong answer，WA
4-time limit error，TLE
5-memory limit error，MLE
6-runtime error，RE
7-unknown error，UKE
8-partial correct，PC，部分正确，仅得部分分
9-system error，执行过程中发生错误，错误信息可在message中查看
10-compiler error，CE，编译错误
"""
checkpoint_status_waiting: int = 0
checkpoint_status_judging: int = 1
checkpoint_status_ac: int = 2
checkpoint_status_wa: int = 3
checkpoint_status_tle: int = 4
checkpoint_status_mle: int = 5
checkpoint_status_re: int = 6
checkpoint_status_uke: int = 7
checkpoint_status_pc: int = 8
checkpoint_status_se: int = 9
checkpoint_status_ce: int = 10


# judger的内置功能


# 分配一个robot
# wait_list为在指定名单里选择，wait_list为None则为任意选择
# 返回uuid，或者None，此时为没有满足要求的
async def submit_select_robot(wait_list=None):
    # 准备ok_list
    ok_list = []
    if wait_list is None:
        # 可以随便选
        for robot in robots.values():
            if robot.status >= robot_status_ok:
                ok_list.append(robot)
    else:
        for robot in robots.values():
            if robot.status < robot_status_ok:
                continue
            if robot.username not in wait_list:
                continue
            ok_list.append(robot)
    # 现在ok_list里的robot理论上都是满足要求的
    # 我们选择最优的那个
    minn = 999999999
    uuid = None
    for robot in ok_list:
        if robot.queue.qsize() < minn:
            uuid = robot.uuid
        # 这里将来可能再加个优化什么的
    return uuid


# 根据pid找wait_list
async def submit_get_wait_list(pid: str) -> List[str]:
    data2 = []
    async with database_conn.cursor() as cursor:
        await cursor.execute(f"SELECT username FROM tb_link WHERE pid = '{pid}'")
        data1 = await cursor.fetchall()
        for row in data1:
            data2.append(row[0])
    return data2


# 提交评测服务
# 返回trace列表
async def submit(checkpoints: List[CheckpointToProblem], code: str, rid: int) -> List[Trace]:
    # 将要返回的数据
    data: List[Trace] = List[Trace]([])
    # 先把checkpoint按pid分组
    index: Dict[str, List[CheckpointToProblem]] = {}
    for checkpoint in checkpoints:
        if checkpoint.target in index:
            index[checkpoint.target].append(checkpoint)
        else:
            index[checkpoint.target] = [checkpoint]
    # 按分组投递
    # 一个分组就会引发一个评测请求
    for target in index.keys():
        # 先按照target找wait_list
        wait_list: List[str] = await submit_get_wait_list(target)
        uuid: Optional[str] = await submit_select_robot(wait_list=(wait_list if len(wait_list) > 0 else None))
        if uuid is None:
            for checkpoint in index[target]:
                data.append(Trace(checkpoint.id, trace_status_error, message="没有找到可用的robot。"))
            continue
        # 投递，把一个评测包投递过去
        await robots[uuid].queue.put(CheckpointsPackage(rid, code, index[target]))
        for checkpoint in index[target]:
            data.append(Trace(checkpoint.id, trace_status_ok, uuid=uuid, username=robots[uuid].username))
    return data


# ------------------------robot相关----------------------

# robot的处理循环
async def robot_loop(robot: Robot) -> None:
    while robot.status != robot_status_destroy:  # 当前状态不为准备销毁
        pack: CheckpointsPackage = await robot.queue.get()
        # ids = []  # 把当前评测包里的测试点编号取出
        # for checkpoint in pack["index"]:
        #   nths.append(checkpoint["nth"])
        robot.status = robot_status_working  # 置robot状态为正在评测
        logger.info("评测包：{}".format(asdict(pack)))
        await service.handle(robot, pack)
        await asyncio.sleep(2)  # 评测完毕后最好robot有个冷却时间防止频繁请求
        robot.status = robot_status_ok  # 置robot状态为准备就绪
        logger.info("{} 评测结束".format(pack.rid))


# 初始化已经存在的robot
async def robot_init_all() -> None:
    async with database_conn.cursor() as cursor:
        await cursor.execute("select * from tb_user")
        _robots = await cursor.fetchall()
        # logger.info(robots)
        for robot in _robots:
            _robot = Robot(str(uuid.uuid4()))
            _robot.username = robot[0]
            _robot.password = robot[1]
            robots[_robot.uuid] = _robot
            logger.info("初始化 {} - {}".format(_robot.uuid, _robot.username))
            try:
                await service.login(_robot, init=True)
                robot.status = robot_status_ok
                asyncio.gather(robot_loop(_robot))
            except Exception as e:
                logger.error(utils.get_exception_details(e))
                robot.status = robot_status_offline


# 将会更新robot状态并保存登录信息
async def robot_after_login(robot: Robot) -> None:
    robot.status = robot_status_ok
    # 登录成功后将robot信息写入数据库
    async with database_conn.cursor() as cursor:
        await cursor.execute("replace into tb_robot (username,password) values ('{}','{}')".format(robot.username, robot.password))
    asyncio.gather(robot_loop(robot))


# 返回robot信息列表
async def robot_list() -> List:
    res = []
    for i in robots.values():
        res.append({"uuid": i.uuid, "status": i.status, "username": i.username})
    return res


# 返回新建robot的uuid
async def robot_create() -> str:
    new_robot = Robot(str(uuid.uuid4()))
    new_robot.queue = asyncio.Queue()
    new_robot.session = aiohttp.ClientSession()
    robots[new_robot.uuid] = new_robot
    return new_robot.uuid


# 删除一个robot
async def robot_delete(uuid: str) -> None:
    robot = robots[uuid]
    if robot.status != robot_status_no_user:
        async with database_conn.cursor() as cursor:
            await cursor.execute("delete from tb_robot where username = '{}'".format(robot.username))
    robot.status = robot_status_destroy
    robots.pop(uuid)


# ------------------------题目揽收相关----------------------


# 允许题目被所有robot揽收
async def link_all(pid: str) -> None:
    async with database_conn.cursor() as cursor:
        # 全部删除就相当于都可以揽收
        await cursor.execute("delete from tb_link where pid = '{}'".format(pid))


# 添加题目可被揽收的robot
async def link_add(pid: str, robot: str) -> None:
    async with database_conn.cursor() as cursor:
        await cursor.execute("insert into tb_link(pid, username) values ({}, {})".format(pid, robot))


# 删除题目可被揽收的robot
async def link_remove(pid: str, robot: str) -> None:
    async with database_conn.cursor() as cursor:
        await cursor.execute("delete from tb_link where pid = '{}' and username = '{}'".format(pid, robot))


# 列出题目可被揽收的robot，如果为空则为题目可被所有的robot揽收
async def link_list(pid: str) -> List:
    _list = []
    async with database_conn.cursor() as cursor:
        items = await cursor.execute("select * from tb_link where pid = '{}'".format(pid))
        for item in items:
            _list.append(item[1])
    return _list



