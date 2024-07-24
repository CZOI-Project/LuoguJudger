import asyncio
from dataclasses import dataclass
from typing import Optional, List
from aiohttp import ClientSession

from config import robot_status_no_user


@dataclass
class Robot:
    """Robot"""
    """唯一标识符"""
    uuid: str
    """爬虫密码"""
    password: str = ""
    """爬虫账号"""
    username: str = ""
    """当前状态，-3-仅创建，未绑定账号密码
    -2-登录需要验证
    -1-发生错误（登陆时出错，密码错误等）
    0-离线
    1-在线，准备就绪
    2-正在评测
    """
    status: int = robot_status_no_user
    """以下字段仅judger中存在"""
    """judger对应的connection"""
    session: Optional[ClientSession] = None
    """评测队列"""
    queue: Optional[asyncio.Queue] = None


@dataclass
class Trace:
    """Trace"""
    """测试点编号"""
    id: int
    """状态，0-成功被揽收
    1-目标judger未上线
    2-没有可用的robot
    其他错误请通过日志发送，并将测试点置为se
    """
    status: int
    """揽收的robot的用户名，status为0时可用"""
    username: Optional[str] = None
    """揽收的robot的uuid，status为0时可用"""
    uuid: Optional[str] = None
    """status为3时可用"""
    message: Optional[str] = None


# 抛出的信息将会返回给coj服务端
class COJException(Exception):
    pass


@dataclass
class CheckpointToProblem:
    """CheckpointToProblem"""
    """提交给judger时附带信息，一般包含编译器参数等信息"""
    extra: str
    """测试点序号"""
    id: int
    """该测试点所用到的judger的id"""
    jid: str
    """内存限制，单位kb，注意，内存和时间限制需要与远程题目对应的一致，否则无法达到效果"""
    memoryLimit: int
    """远程题目测试点编号"""
    nth: int
    """该测试点分数"""
    score: int
    """远程题目特征"""
    target: str
    """时间限制，单位ms"""
    timeLimit: int


@dataclass
class CheckpointsPackage:
    rid: int
    code: str
    index: List[CheckpointToProblem]
