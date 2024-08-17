# judger的内置功能
import asyncio
import uuid
from dataclasses import asdict
from typing import List, Dict, Optional
import config
import event
from constants import *
from entity import CheckpointToProblem, Trace, CheckpointsPackage, Robot
from logger import logger


# 分配一个robot
# wait_list为在指定名单里选择，wait_list为None则为任意选择
# 返回uuid，或者None，此时为没有满足要求的
async def submit_select_robot(wait_list=None):
    # 准备ok_list
    ok_list = []
    if wait_list is None:
        # 可以随便选
        for robot in config.robots.values():
            if robot.status >= robot_status_ok:
                ok_list.append(robot)
    else:
        for robot in config.robots.values():
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
    async with config.database_conn.execute(f"SELECT username FROM tb_link WHERE pid = '{pid}'") as cursor:
        async for row in cursor:
            data2.append(row[0])
    return data2


# 提交评测服务
# 返回trace列表
# 一个评测触发流程 coj->controller->submit->submit_get_wait_list->submit_select_robot->
async def submit(checkpoints: List[CheckpointToProblem], code: str, rid: int) -> List[Trace]:
    # 将要返回的数据
    data: List[Trace] = []
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
        ids: List[int] = []
        for checkpoint in index[target]:
            ids.append(checkpoint.id)
        # 先按照target找wait_list
        wait_list: List[str] = await submit_get_wait_list(target)
        # 匹配合适的robot
        uuid: Optional[str] = await submit_select_robot(wait_list=(wait_list if len(wait_list) > 0 else None))
        # 没有合适的就寄了
        if uuid is None:
            data.append(Trace(ids, trace_status_robot_failed))
            continue
        # 投递，把一个评测包投递过去
        await config.robots[uuid].queue.put(CheckpointsPackage(rid, code, index[target]))
        data.append(Trace(ids, trace_status_ok, uuid=uuid, username=config.robots[uuid].username))
    return data


# ------------------------robot相关----------------------

# robot的处理循环
async def robot_loop(robot: Robot) -> None:
    while robot.status != robot_status_destroy:  # 当前状态不为准备销毁
        pack: CheckpointsPackage = await robot.queue.get()
        robot.status = robot_status_working  # 置robot状态为正在评测
        logger.info("评测包：{}".format(asdict(pack)))
        await event.handle(robot, pack)
        await asyncio.sleep(2)  # 评测完毕后最好robot有个冷却时间防止频繁请求
        robot.status = robot_status_ok  # 置robot状态为准备就绪
        logger.info("{} 评测结束".format(pack.rid))
