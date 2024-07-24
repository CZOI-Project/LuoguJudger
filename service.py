# 一些业务代码
import asyncio
import random
from dataclasses import asdict

import api
import utils
from entry import COJException, CheckpointsPackage, Robot
import config
from logger import logger
from typing import Dict, List, Optional


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
    if code != "114514":
        raise COJException("验证码错误。")

    # 这里写爬虫发起登录请求

    # 登录成功时此代码必加，将会设置robot登录信息及状态，且robot信息将会被存到数据库中
    if init is False:
        await config.robot_after_login(robot)


# 处理评测请求
async def handle(robot: Robot, pack: CheckpointsPackage) -> None:
    # 关于异常处理：我理想地认为调用coj服务端接口是不会发生错误的
    # 先将该评测包下的测试点都置为judging
    for checkpoint in pack.index:
        await api.update(pack.rid, checkpoint.id, config.checkpoint_status_judging)
    try:
        # 这里写爬虫代码
        await asyncio.sleep(random.randint(5, 8))
        # 置测试点状态为ac
        for checkpoint in pack.index:
            runMem = random.randint(1024, 10240)
            runTime = random.randint(80, 300)
            await api.update(
                pack.rid,
                checkpoint.id,
                config.checkpoint_status_se,
                f"{utils.get_time_text(runTime)}/{utils.get_mem_text(runMem)}",
                100,
                runTime,
                runMem
            )
    except Exception as e:
        # 提交日志
        logger.error(f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n {utils.get_exception_details(e)}。")
        await api.log(
            pack.rid,
            f"[{config.jid}-{robot.username}] 评测测试点时发生错误：\n {utils.get_exception_details(e)}。",
            "red"
        )
        # 置所有测试点状态为se
        for checkpoint in pack.index:
            await api.update(pack.rid, checkpoint.id, config.checkpoint_status_se, "")


# 保活任务
async def keepalive():
    while True:
        await asyncio.sleep(config.keepalive_time)
        for i in config.robots.values():
            if i.status >= 1:
                # 这里可以调爬虫，然后写保活的措施
                pass
