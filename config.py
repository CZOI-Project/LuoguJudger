# 关于judger的配置
import aiosqlite
from typing import Optional, Dict
from entity import Robot

jid: str = "luogu"  # judger的id
name: str = "洛谷"  # judger的name
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

# 验证码存到这里
folder: str = "F:\\CZOI Project\\COJ\\COJ-Core\\resources\\code"
re_info = [
    {
      "name": "SIGHUP",
      "value": 1,
      "description": "挂起检测到控制终端或控制进程死亡"
    },
    {
      "name": "SIGINT",
      "value": 2,
      "description": "键盘中断"
    },
    {
      "name": "SIGQUIT",
      "value": 3,
      "description": "从键盘退出"
    },
    {
      "name": "SIGILL",
      "value": 4,
      "description": "非法指令"
    },
    {
      "name": "SIGTRAP",
      "value": 5,
      "description": "跟踪/断点陷阱"
    },
    {
      "name": "SIGABRT",
      "value": 6,
      "description": "中止"
    },
    {
      "name": "SIGBUS",
      "value": 7,
      "description": "总线错误（不良内存访问）"
    },
    {
      "name": "SIGFPE",
      "value": 8,
      "description": "浮点异常"
    },
    {
      "name": "SIGKILL",
      "value": 9,
      "description": "终止信号"
    },
    {
      "name": "SIGUSR1",
      "value": 10,
      "description": "用户定义信号 1"
    },
    {
      "name": "SIGSEGV",
      "value": 11,
      "description": "分段故障带有无效的内存引用"
    },
    {
      "name": "SIGUSR2",
      "value": 12,
      "description": "用户定义信号 2"
    },
    {
      "name": "SIGPIPE",
      "value": 13,
      "description": "破碎管道：写入无读取者的管道；参见 `pipe(7)`"
    },
    {
      "name": "SIGALRM",
      "value": 14,
      "description": "定时器触发"
    },
    {
      "name": "SIGTERM",
      "value": 15,
      "description": "终止信号"
    },
    {
      "name": "SIGSTKFLT",
      "value": 16,
      "description": "协处理器堆栈故障"
    },
    {
      "name": "SIGCHLD",
      "value": 17,
      "description": "子进程停止或终止"
    },
    {
      "name": "SIGCONT",
      "value": 18,
      "description": "若停止则继续"
    },
    {
      "name": "SIGSTOP",
      "value": 19,
      "description": "停止进程"
    },
    {
      "name": "SIGTSTP",
      "value": 20,
      "description": "终端停止"
    },
    {
      "name": "SIGTTIN",
      "value": 21,
      "description": "后台进程的终端输入"
    },
    {
      "name": "SIGTTOU",
      "value": 22,
      "description": "后台进程的终端输出"
    },
    {
      "name": "SIGURG",
      "value": 23,
      "description": "套接字紧急条件"
    },
    {
      "name": "SIGXCPU",
      "value": 24,
      "description": "CPU 时间限制超出"
    },
    {
      "name": "SIGXFSZ",
      "value": 25,
      "description": "文件大小限制超出"
    },
    {
      "name": "SIGVTALRM",
      "value": 26,
      "description": "虚拟报警钟"
    },
    {
      "name": "SIGPROF",
      "value": 27,
      "description": "性能分析定时器到期"
    },
    {
      "name": "SIGWINCH",
      "value": 28,
      "description": "窗口大小改变信号"
    },
    {
      "name": "SIGIO",
      "value": 29,
      "description": "I/O 现在可能"
    },
    {
      "name": "SIGPWR",
      "value": 30,
      "description": "电源故障（System V）"
    },
    {
      "name": "SIGSYS",
      "value": 31,
      "description": "不良系统调用"
    }
]
