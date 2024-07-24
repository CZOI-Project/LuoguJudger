import json
import uuid
from dataclasses import asdict
from typing import List

import aiohttp
import aiosqlite

from aiohttp import web
import asyncio

from aiohttp.web_response import Response

import api
import config
import service
import utils
from entry import Robot, COJException, CheckpointToProblem, Trace
from logger import logger

app = None


# /info
async def info(request) -> Response:
    res = await config.robot_list()
    return utils.response_ok(res)


# /submit
async def submit(request) -> Response:
    data = await request.post()
    checkpoints: List[CheckpointToProblem] = [CheckpointToProblem(**item) for item in json.loads(data["checkpoints"])]
    rid: int = data["rid"]
    code: str = data["code"]
    res: List[Trace] = await config.submit(checkpoints, code, rid)
    return utils.response_ok([asdict(item) for item in res])


# /robot/create
async def robot_create(request) -> Response:
    uuid: str = await config.robot_create()
    return utils.response_ok(uuid)


# /robot/verify
async def robot_verify(request) -> Response:
    uuid: str = request.query["uuid"]
    if uuid not in config.robots:
        raise COJException("robot不存在")
    res: str = await service.verify(config.robots[uuid])
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
        await service.login(config.robots[uuid], code)
    else:
        await service.login(config.robots[uuid])
    return utils.response_ok()


# /link
async def link(request) -> Response:
    option: int = request.query["option"]
    pid: str = request.query["pid"]
    if option == 0:
        await config.link_all(pid)
    if option == 1:
        robot: str = request.query["robot"]
        await config.link_add(pid, robot)
    if option == 2:
        robot: str = request.query["robot"]
        await config.link_remove(pid, robot)
    if option == 3:
        data: List = await config.link_list(pid)
        return utils.response_ok(data)
    return utils.response_ok()


# /robot/delete
async def robot_delete(request) -> Response:
    uuid = request.query["uuid"]
    if uuid not in config.robots:
        raise COJException("目标Judger不存在")
    await config.robot_delete(uuid)
    return utils.response_ok()


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 404:
            return utils.response_code(config.response_status_space)
        return response
    except COJException as e:
        return utils.response_message(str(e))
    except Exception as e:
        logger.error(utils.get_exception_details(e))
        return utils.response_message(utils.get_exception_details(e))


async def main():
    # 连接数据库并初始化数据库
    logger.info("连接数据库...")
    config.database_conn = await aiosqlite.connect('database.db')
    with open('init.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
        await config.database_conn.executescript(sql)
        await config.database_conn.commit()  # 提交更改
    # judger 启动后需要把之前已经添加的robot初始化
    logger.info("初始化robots...")
    await service.init_all_robots()
    # 启动judger服务
    logger.info("启动judger服务...")
    global app
    app = web.Application(middlewares=[error_middleware])
    app.router.add_routes([
        web.get('/info', info),
        web.post('/submit', submit),
        web.get('/robot/create', robot_create),
        web.get('/robot/verify', robot_verify),
        web.get('/robot/login', robot_login),
        web.get('/robot/delete', robot_delete),
        web.get('/link', link),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()
    # 向COJ提交注册请求
    logger.info("注册judger服务...")
    flag = await api.register()
    if not flag:
        logger.error("注册judger服务失败")
        exit()
    # robot保活
    asyncio.gather(config.keepalive())
    # 保持服务器运行
    logger.info("judger服务启动完毕")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logger.info("COJ Judger Powered by Python")
    asyncio.run(main())
