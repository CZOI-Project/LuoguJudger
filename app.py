import aiosqlite
from aiohttp import web
import asyncio
import api
import controller
import config
import event
import utils
from entity import COJException
from logger import logger
from constants import *

app = None


# 异常处理
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 404:
            return utils.response_code(response_status_space)
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
    await event.robot_init_all()
    # 启动judger服务
    logger.info("启动judger服务...")
    if config.port == -1:
        config.port = utils.get_free_port()
    config.remote += ":" + str(config.port)
    logger.info("在 {port} 上监听".format(port=config.port))
    global app
    app = web.Application(middlewares=[error_middleware])
    app.router.add_routes([
        web.get('/info', controller.info),
        web.post('/submit', controller.submit),
        web.get('/robot/create', controller.robot_create),
        web.get('/robot/verify', controller.robot_verify),
        web.get('/robot/login', controller.robot_login),
        web.get('/robot/delete', controller.robot_delete),
        web.get('/link', controller.link),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()
    # 向COJ提交注册请求
    logger.info("注册judger服务...")
    flag = await api.register()
    if not flag:
        logger.error("注册judger服务失败，可能是jid已经被占用")
    # robot保活
    asyncio.gather(event.keepalive())
    # 保持服务器运行
    logger.info("judger服务启动完毕")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logger.info("COJ Judger Powered by Python")
    asyncio.run(main())
