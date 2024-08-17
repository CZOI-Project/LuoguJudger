# 关于judger的配置
import aiosqlite
from typing import Optional, Dict
from entity import Robot

jid: str = "my"  # judger的id
name: str = "我的judger"  # judger的name
remote: str = "http://localhost"  # 访问该judger需要使用的地址，不要包含端口号，judger会自动处理
port: int = -1  # 监听端口，如果设置为-1就不用配置了，judger启动时会直接给你随机分配一个
host: str = "0.0.0.0"  # 监听ip
key: str = "coj443523"  # 用于与coj服务端通信的密钥
server: str = "http://localhost:8080/judger"  # coj服务端的请求地址
create_type: int = 1  # 添加robot的时候的类型
keepalive_time: int = 60 * 60  # 每一个小时执行一次保活任务
ping_time: int = 30  # 每30秒向coj服务端ping一次

# coj的全局变量
robots: Dict[str, Robot] = {}
database_conn: Optional[aiosqlite.Connection] = None
