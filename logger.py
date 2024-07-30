import os
from colorama import init, Fore, Style
import logging

from logging.handlers import TimedRotatingFileHandler
# 創建並配置日誌記錄器
init(autoreset=True)
logger = logging.getLogger('ServerLogger')
logger.setLevel(logging.DEBUG)  # 設置日誌級別

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = f"{Fore.GREEN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.DEBUG:
            record.msg = f"{Fore.CYAN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{Fore.LIGHTRED_EX}{record.msg}{Style.RESET_ALL}"
        return super().format(record)
# 創建控制台日誌處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
\
# 創建文件日誌處理器
file_handler = TimedRotatingFileHandler(
        filename=f"server.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
file_handler.setLevel(logging.DEBUG)

# 創建日誌格式器
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 為處理器設置格式器
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 將處理器添加到日誌記錄器
logger.addHandler(console_handler)
logger.addHandler(file_handler)
