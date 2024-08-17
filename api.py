from typing import Optional, Dict, List

import aiohttp
from aiohttp import ClientSession

import config
import utils
from logger import logger

# 向coj服务端通信的api
# 当前会话
session: Optional[ClientSession] = None


async def get(url: str, params: Dict) -> None:
    global session
    try:
        async with session.get(f"{config.server}{url}", params=params) as r:
            if r.status == 200:
                data = await r.json()
                if data["code"] == 200:
                    return
                else:
                    logger.error(f"请求COJ服务端时发生错误：响应代码异常\nGET {config.server}{url}\n{data}")
            else:
                logger.error(f"请求COJ服务端时发生错误：HTTP响应代码异常\nGET {config.server}{url}\nHTTP响应代码：{r.status}")
    except Exception as e:
        logger.error(f"请求COJ服务端时发生错误：请求异常\nGET {config.server}{url}\n{utils.get_exception_details(e)}")


async def post(url: str, data: Dict) -> None:
    global session
    try:
        async with session.post(f"{config.server}{url}", data=data) as r:
            if r.status == 200:
                data = await r.json()
                if data["code"] == 200:
                    return
                else:
                    logger.error(f"请求COJ服务端时发生错误：响应代码异常\nPOST {config.server}{url}\n{data}")
            else:
                logger.error(f"请求COJ服务端时发生错误：HTTP响应代码异常\nPOST {config.server}{url}\nHTTP响应代码：{r.status}")
    except Exception as e:
        logger.error(f"请求COJ服务端时发生错误：请求异常\nPOST {config.server}{url}\n{utils.get_exception_details(e)}")


# 注册judger到coj中
async def register() -> bool:
    global session
    session = aiohttp.ClientSession(headers={"Authorization": config.key})
    async with session.post(
            "{server}/register".format(server=config.server),
            data={"jid": config.jid, "remote": config.remote, "name": config.name, "type": config.create_type}
    ) as r:
        if r.status == 200:
            data = await r.json()
            if data["code"] == 200:
                return True
            logger.error(data)
        return False


# 向评测记录添加日志
async def log(rid: int, message: str, color: str) -> None:
    await post("/log", data={"rid": rid, "message": f'<div class="mdui-text-color-{color}">{message}</div>'})


# 更新测试点信息
async def update(
        rid: int,
        ids: List[int],
        status: Optional[int] = None,
        message: Optional[str] = None,
        score: Optional[int] = None,
        runTime: Optional[int] = None,
        runMem: Optional[int] = None
) -> None:
    data = {"rid": rid, "ids": utils.array_to_text(ids)}
    if status is not None:
        data["status"] = status
    if message is not None:
        data["message"] = message
    if score is not None:
        data["score"] = score
    if runTime is not None:
        data["runTime"] = runTime
    if runMem is not None:
        data["runMem"] = runMem
    await post("/update", data=data)
