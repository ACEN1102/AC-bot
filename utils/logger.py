import logging
import os
from logging.handlers import RotatingFileHandler

# 确保日志目录存在
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 创建日志记录器
logger = logging.getLogger('feishu_bot')
logger.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s')

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 创建文件处理器
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 导出logger供其他模块使用
__all__ = ['logger']
