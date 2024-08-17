import asyncio
import random
import api
import constants
import core
import service
import utils
from constants import robot_status_ok
from entity import COJException, CheckpointsPackage, Robot
import config
from logger import logger
from typing import Optional, List


# 这里写爬虫获取验证码
# 返回验证码图片的链接
async def verify(robot: Robot) -> str:
    return ""


# 爬虫的登录实现
# code为验证码，如果你的judger的type不为1可以忽略
# init为是否为judger初始化时执行的
async def login(robot: Robot, code: Optional[str] = None, init: bool = False) -> None:
    if robot.username == 'test':
        raise COJException("密码错误。")
    # 初始化judger执行该函数的时候不提供code，所以会直接命中该条件
    if code != "114514" and init is False:
        raise COJException("验证码错误。")

    # 这里写爬虫发起登录请求

    # 存数据库啥的
    if init is False:
        # 置状态
        robot.status = robot_status_ok
        # 写入数据库
        await config.database_conn.execute(
            "replace into tb_user (username,password) values ('{}','{}')".format(robot.username, robot.password)
        )
        await config.database_conn.commit()
        # 开事件循环
        asyncio.gather(core.robot_loop(robot))


# 处理评测请求
async def handle(robot: Robot, pack: CheckpointsPackage) -> None:
    # 关于异常处理：我理想地认为调用coj服务端接口是不会发生错误的
    # 先将该评测包下的测试点都置为judging
    ids: List[int] = []
    for checkpoint in pack.index:
        ids.append(checkpoint.id)
    await api.update(pack.rid, ids, constants.checkpoint_status_judging)
    try:
        # 这里写爬虫代码
        await asyncio.sleep(random.randint(5, 8))
        # 置测试点状态为ac
        for checkpoint in pack.index:
            await asyncio.sleep(1)
            runMem = random.randint(1024, 10240)
            runTime = random.randint(80, 300)
            await api.update(
                pack.rid,
                [checkpoint.id],
                constants.checkpoint_status_ac,
                f"Accepted,very ok!",
                100,
                runTime,
                runMem
            )
            ids.remove(checkpoint.id)
    except Exception as e:
        # 提交日志
        log = f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n {utils.get_exception_details(e)}，如下测试点将收到影响：{utils.array_to_text(ids)}"
        logger.error(log)
        await api.log(
            pack.rid,
            log,
            "red"
        )
        # 置所有测试点状态为se
        await api.update(pack.rid, ids, constants.checkpoint_status_se)


# 初始化已经存在的robot
async def robot_init_all() -> None:
    async with config.database_conn.execute("select * from tb_user") as cursor:
        async for robot in cursor:
            # 创建robot实体
            _uuid = await service.robot_create()
            _robot = config.robots[_uuid]
            _robot.username = robot[0]
            _robot.password = robot[1]
            logger.info("初始化 {} - {}".format(_robot.uuid, _robot.username))
            try:
                _robot.status = robot_status_ok
                asyncio.gather(core.robot_loop(_robot))
            except Exception as e:
                logger.error(utils.get_exception_details(e))
                _robot.status = constants.robot_status_offline


# 保活任务
async def keepalive():
    while True:
        await asyncio.sleep(config.keepalive_time)
        for i in config.robots.values():
            if i.status >= 1:
                # 这里可以调爬虫，然后写保活的措施
                pass
