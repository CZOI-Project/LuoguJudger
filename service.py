# 返回robot信息列表
import asyncio
import json
import uuid
from typing import List

import aiohttp
from aiohttp import TCPConnector

import config
from constants import robot_status_no_user, robot_status_destroy
from entity import RobotDTO, Robot


async def robot_list() -> List:
    res = []
    for i in config.robots.values():
        res.append(RobotDTO(i.status, i.username, i.uuid))
    return res


# 返回新建robot的uuid，同时也注册到config里了
async def robot_create() -> str:
    new_robot = Robot(str(uuid.uuid4()))
    new_robot.queue = asyncio.Queue()
    new_robot.jar = aiohttp.CookieJar(unsafe=True)
    new_robot.session = aiohttp.ClientSession(
        connector=TCPConnector(ssl=False),
        json_serialize=json.dumps,
        cookie_jar=new_robot.jar
    )
    config.robots[new_robot.uuid] = new_robot
    return new_robot.uuid


# 删除一个robot
async def robot_delete(uuid: str) -> None:
    robot = config.robots[uuid]
    if robot.status != robot_status_no_user:
        await config.database_conn.execute("delete from tb_user where username = '{}'".format(robot.username))
        await config.database_conn.commit()
    robot.status = robot_status_destroy
    config.robots.pop(uuid)


# ------------------------题目揽收相关----------------------


# 允许题目被所有robot揽收
async def link_all(pid: str) -> None:
    # 全部删除就相当于都可以揽收
    await config.database_conn.execute("delete from tb_link where pid = '{}'".format(pid))
    await config.database_conn.commit()


# 添加题目可被揽收的robot
async def link_add(pid: str, robot: str) -> None:
    await config.database_conn.execute("insert into tb_link(pid, username) values ({}, {})".format(pid, robot))
    await config.database_conn.commit()


# 删除题目可被揽收的robot
async def link_remove(pid: str, robot: str) -> None:
    await config.database_conn.execute("delete from tb_link where pid = '{}' and username = '{}'".format(pid, robot))
    await config.database_conn.commit()


# 列出题目可被揽收的robot，如果为空则为题目可被所有的robot揽收
async def link_list(pid: str) -> List:
    _list = []
    async with config.database_conn.execute("select * from tb_link where pid = '{}'".format(pid)) as cursor:
        async for item in cursor:
            _list.append(item[1])
    return _list
