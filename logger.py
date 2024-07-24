import logging
import os
from datetime import datetime

# 获取当前脚本的所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 创建日志文件夹路径
log_dir = os.path.join(current_dir, 'log')

# 如果日志文件夹不存在，则创建它
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建日志文件的完整路径
log_filename = os.path.join(log_dir, datetime.now().strftime('%Y-%m-%d') + '.log')

# 创建一个日志记录器
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# 创建一个日志格式化器
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

# 创建一个控制台处理器并设置其格式
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 创建一个文件处理器并设置其格式
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(formatter)

# 将处理器添加到记录器中
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 确保日志系统只初始化一次
if not hasattr(logger, 'initialized'):
    logger.initialized = True
