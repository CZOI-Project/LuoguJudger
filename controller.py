# /info
import json
from dataclasses import asdict
from typing import List

from aiohttp.web_response import Response

import config
import core
import event
import service
import utils
from entity import CheckpointToProblem, Trace, COJException, Robot


async def info(request) -> Response:
    res = await service.robot_list()
    return utils.response_ok([asdict(item) for item in res])


# /submit
async def submit(request) -> Response:
    data = await request.post()
    checkpoints: List[CheckpointToProblem] = [CheckpointToProblem(**item) for item in json.loads(data["checkpoints"])]
    rid: int = data["rid"]
    code: str = data["code"]
    res: List[Trace] = await core.submit(checkpoints, code, rid)
    return utils.response_ok([asdict(item) for item in res])


# /robot/create
async def robot_create(request) -> Response:
    uuid: str = await service.robot_create()
    return utils.response_ok(uuid)


# /robot/verify
async def robot_verify(request) -> Response:
    uuid: str = request.query["uuid"]
    if uuid not in config.robots:
        raise COJException("robot不存在")
    res: str = await event.verify(config.robots[uuid])
    return utils.response_ok(res)


# /robot/login
async def robot_login(request) -> Response:
    uuid: str = request.query["uuid"]
    if uuid not in config.robots:
        raise COJException("目标robot不存在")
    robot: Robot = config.robots[uuid]
    robot.username = request.query["username"]
    robot.password = request.query["password"]
    if "code" in request.query:
        code: str = request.query["code"]
        await event.login(config.robots[uuid], code)
    else:
        await event.login(config.robots[uuid])
    return utils.response_ok()


# /link
async def link(request) -> Response:
    option: int = request.query["option"]
    pid: str = request.query["pid"]
    if option == 0:
        await service.link_all(pid)
    if option == 1:
        robot: str = request.query["robot"]
        await service.link_add(pid, robot)
    if option == 2:
        robot: str = request.query["robot"]
        await service.link_remove(pid, robot)
    if option == 3:
        data: List = await service.link_list(pid)
        return utils.response_ok(data)
    return utils.response_ok()


# /robot/delete
async def robot_delete(request) -> Response:
    uuid = request.query["uuid"]
    if uuid not in config.robots:
        raise COJException("Robot不存在")
    await service.robot_delete(uuid)
    return utils.response_ok()
