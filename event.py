import asyncio
import uuid

import aiohttp
from bs4 import BeautifulSoup

import api
import constants
import core
import service
import utils
from constants import robot_status_ok
from entity import COJException, CheckpointsPackage, Robot, RefList, CheckpointToProblem
import config
from logger import logger
from typing import Optional, Dict


# 这里写爬虫获取验证码
# 返回验证码图片的链接
async def verify(robot: Robot) -> str:
    async with robot.session.get("https://www.luogu.com.cn/auth/login") as resp:
        logger.info(f"[Login Action - {robot.uuid}]" + str(resp.status))
        logger.info(f"[Login Action - {robot.uuid}]" + str(resp.cookies))
        html = await resp.text()
        soup = BeautifulSoup(html, "lxml")
        tags = soup.find_all("meta")
        for tag in tags:
            if "name" in tag.attrs:
                if tag.attrs["name"] == "csrf-token":
                    token = tag.attrs["content"]
                    robot.token = token
                    logger.info(f"[Login Action - {robot.uuid}]token:" + token)
    name = "{name}.png".format(name=utils.get_md5_hash(str(uuid.uuid4())))
    async with robot.session.get("https://www.luogu.com.cn/api/verify/captcha") as resp:
        f = open(config.folder + "\\" + name, "wb")
        f.write(await resp.read())
        f.close()
    return "http://localhost:8080/resources/code/" + name


# 爬虫的登录实现
# code为验证码，如果你的judger的type不为1可以忽略
# init为是否为judger初始化时执行的
async def login(robot: Robot, code: Optional[str] = None, init: bool = False) -> None:
    async with robot.session.post(
            # url="https://www.luogu.com.cn/do-auth/password",
            url="https://www.luogu.com.cn/api/auth/userPassLogin",
            json={"username": robot.username, "password": robot.password, "captcha": code},
            headers={"x-csrf-token": robot.token, "origin": "https://www.luogu.com.cn",
                     "referer": "https://www.luogu.com.cn/auth/login"}) as resp:
        data = await resp.json()
        if "errorMessage" in data:
            raise COJException(data["errorMessage"])
    cookies = robot.session.cookie_jar.filter_cookies(aiohttp.client.URL("https://www.luogu.com.cn/")).items()
    client_id = cookies.mapping['__client_id'].value
    uid = cookies.mapping['_uid'].value
    # 应用
    robot.client_id = client_id
    robot.uid = uid
    # 存储
    await config.database_conn.execute(
        "replace into tb_user (username,password,client_id,uid) values ('{}','{}','{}','{}')".format(robot.username, robot.password, client_id, uid)
    )
    await config.database_conn.commit()
    # 开事件循环
    asyncio.gather(core.robot_loop(robot))
    # 置状态
    robot.status = robot_status_ok


# 处理评测请求
async def handle(robot: Robot, pack: CheckpointsPackage) -> None:
    # 关于异常处理：我理想地认为调用coj服务端接口是不会发生错误的
    # 先将该评测包下的测试点都置为judging
    still: RefList = RefList([])  # 没有完成的测试点
    mapp: Dict[int, CheckpointToProblem] = {}  # 远程题目的测试点编号对应的coj测试点实体
    for checkpoint in pack.index:
        # 建立一个远程测试点与本地测试点的映射
        mapp[checkpoint.nth] = checkpoint
        still.data.append(checkpoint.id)
    await api.update(pack.rid, still.data, constants.checkpoint_status_judging)
    try:
        # 首先获得html中的token
        async with robot.session.get(
                url=f"https://www.luogu.com.cn/problem/{pack.index[0].target}",
                cookies={"__client_id": robot.client_id, "_uid": robot.uid}
        ) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            tags = soup.find_all("meta")
            for tag in tags:
                if "name" in tag.attrs:
                    if tag.attrs["name"] == "csrf-token":
                        token = tag.attrs["content"]
                        robot.token = token
                        logger.info(f"[Submit Action - {robot.uuid}]token:" + token)
        # 再发起请求
        async with robot.session.post(
                url="https://www.luogu.com.cn/fe/api/problem/submit/{pid}".format(pid=pack.index[0].target),
                json={
                    "enableO2": True,
                    "lang": 28,
                    "code": pack.code
                },
                cookies={"__client_id": robot.client_id, "_uid": robot.uid},
                headers={"x-csrf-token": robot.token, "origin": "https://www.luogu.com.cn",
                         "referer": f"https://www.luogu.com.cn/problem/{pack.index[0].target}"}
        ) as resp:
            data = await resp.json()
            logger.info(data)
            rid = data["rid"]
        # 然后监听
        loop = True  # 是否切换为轮询状态
        # TODO 暂时没搞明白洛谷的ws，不过也无所谓了，轮询和websocket也差不多
        """
        try:
            async with robot.session.ws_connect(
                    url="https://ws.luogu.com.cn/ws?host=www.luogu.com.cn",
                    headers={
                        'Cookie': f'__client_id={robot.client_id};_uid={robot.uid}'
                    }
            ) as ws:
                # 监听评测记录
                join_channel = {
                    "type": "join_channel",
                    "channel": "record.track",
                    "channel_param": rid,
                    "exclusive_key": None
                }
                # 接收服务器的响应
                await ws.send_json(join_channel)
                while True:
                    msg = await ws.receive()
                    # 检查消息类型
                    if msg.type == aiohttp.WSMsgType.PING:
                        await ws.pong(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        data = await msg.json()
                        if data["_ws_type"] == "heartbeat":
                            await ws.send_json(data)
                        if data["_ws_type"] == "join_result":
                            await deal_record(data["welcome_message"]["record"], still, mapp, pack.rid, robot)
                            if len(still) == 0:
                                break
                        if data["_ws_type"] == "server_broadcast":
                            if data["type"] == "status_push":
                                await deal_record(data["record"], still, mapp, pack.rid, robot)
                                if len(still) == 0:
                                    break
                            if data["type"] == "flush":
                                # 评测记录结束
                                break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(
                            f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n 追踪评测状态时发生错误，切换为轮询方式。\n {utils.get_exception_details(ws.exception())}")
                        await api.log(
                            pack.rid,
                            f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n 追踪评测状态时发生错误，切换为轮询方式。\n {utils.get_exception_details(ws.exception())}",
                            "red"
                        )
                        loop = True
        except Exception as e:
            logger.error(
                f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n 追踪评测状态时发生错误，切换为轮询方式。\n {utils.get_exception_details(e)}"
            )
            await api.log(
                pack.rid,
                f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n 追踪评测状态时发生错误，切换为轮询方式。\n {utils.get_exception_details(e)}",
                "red"
            )
            loop = True
        """
        # 判断是否需要轮询
        while loop:
            async with robot.session.get(
                    url=f"https://www.luogu.com.cn/record/{rid}?_contentOnly=1",
                    cookies={"__client_id": robot.client_id, "_uid": robot.uid}
            ) as resp:
                data = await resp.json()
                await deal_record(data["currentData"]["record"], still, mapp, pack.rid, robot)
                if len(still.data) == 0:
                    loop = False
            await asyncio.sleep(2)
    except Exception as e:
        # 提交日志
        log = f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n {utils.get_exception_details(e)}，如下测试点将收到影响：{utils.array_to_text(still.data)}"
        logger.error(log)
        await api.log(
            pack.rid,
            log,
            "red"
        )
        # 置所有测试点状态为se
        await api.update(pack.rid, still.data, constants.checkpoint_status_se)


# 处理洛谷的record实体
async def deal_record(record: Dict, still: RefList, mapp: Dict[int, CheckpointToProblem], rid: int,
                      robot: Robot) -> None:
    if record["status"] == 0:
        return
    if record["status"] == 11:  # 整个评测记录都uke了
        ids = []
        for i in still.data:
            ids.append(i)
        await api.update(rid, ids, constants.checkpoint_status_uke, message="远程题目评测UKE")
        still.data = []
        return
    detail = record["detail"]
    # 先判断是否编译成功
    if not detail["compileResult"]["success"]:
        # 提交日志 + 置ce
        await api.log(
            rid,
            f"[{config.jid}-{robot.username}] 编译错误，这些测试点收到影响：{str(still.data)}\n {detail["compileResult"]["message"]}",
            "brown"
        )
        ids = []
        for i in still.data:
            ids.append(i)
        await api.update(rid, ids, constants.checkpoint_status_ce)
        still.data = []
        return
    # 编译成功，获取测试点信息
    _subtasks = detail["judgeResult"]["subtasks"]
    if type(_subtasks) is list:  # 洛谷的响应有可能是list有可能是dict
        if len(_subtasks) == 0:
            return
        subtasks = _subtasks
    else:
        subtasks = _subtasks.values()
    for subtask in subtasks:
        for chk in subtask["testCases"].values():
            remote_id = chk["id"]  # 远程题目的测试点
            status = chk["status"]
            if remote_id not in mapp:  # 不提取该测试点
                continue
            if mapp[remote_id].id not in still.data:  # 该测试点信息已经更新
                continue
            if status == 0 or status == 1:  # waiting 或 judging
                continue
            if status == 3:  # ole
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_wa,
                                 message="输出的内容过多！"
                                 )
            if status == 4:  # mle
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_mle,
                                 runTime=chk["time"],
                                 runMem=chk["memory"]
                                 )
            if status == 5:  # tle
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_tle,
                                 runTime=chk["time"],
                                 runMem=chk["memory"]
                                 )
            if status == 6:  # wa
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_wa,
                                 message=chk["description"],
                                 runTime=chk["time"],
                                 runMem=chk["memory"]
                                 )
            if status == 7:  # re
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_re,
                                 message=f"错误代码: {str(chk['signal'])}, {config.re_info[chk['signal']-1]["name"]} {config.re_info[chk['signal']-1]["description"]}",
                                 )
            if status == 11:  # uke
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_uke,
                                 message=chk["description"],
                                 )
            if status == 12:  # ac
                await api.update(rid, [mapp[remote_id].id], constants.checkpoint_status_ac,
                                 message=chk["description"],
                                 runTime=chk["time"],
                                 runMem=chk["memory"],
                                 score=100
                                 )
            still.data.remove(mapp[remote_id].id)


# 初始化已经存在的robot
async def robot_init_all() -> None:
    async with config.database_conn.execute("select * from tb_user") as cursor:
        async for robot in cursor:
            # 创建robot实体
            _uuid = await service.robot_create()
            _robot = config.robots[_uuid]
            _robot.username = robot[0]
            _robot.password = robot[1]
            _robot.client_id = robot[2]
            _robot.uid = robot[3]
            logger.info("初始化 {} - {}".format(_robot.uuid, _robot.username))
            try:
                # 验证cookie
                cookies = {"__client_id": _robot.client_id, "_uid": _robot.uid}
                async with _robot.session.get("https://www.luogu.com.cn/record/169520371?_contentOnly=1",
                                              cookies=cookies) as resp:
                    data = await resp.json()
                    if data["currentTemplate"] == "AuthLogin":
                        raise Exception("Cookie过期")
                    else:
                        # 验证通过
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
                try:
                    async with i.session.get(
                            url="https://www.luogu.com.cn",
                            cookies={"__client_id": i.client_id, "_uid": i.uid}
                    ) as resp:
                        if resp.status != 200:
                            logger.error("{}-{} 保活错误，http错误代码：{}".format(i.username, i.uuid, resp.status))
                except Exception as e:
                    logger.error(utils.get_exception_details(e))
