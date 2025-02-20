from colorama import init, Fore, Style
import logging

# 創建並配置日誌記錄器
init(autoreset=True)

HIGHLIGHT_LEVEL = 35
logging.addLevelName(HIGHLIGHT_LEVEL, "HIGHLIGHT")

def highlight(self, message, *args, **kwargs):
    if self.isEnabledFor(HIGHLIGHT_LEVEL):
        self._log(HIGHLIGHT_LEVEL, message, args, **kwargs)

logging.Logger.highlight = highlight 

logger = logging.getLogger('ServerLogger')
logger.setLevel(logging.DEBUG)  # 設置日誌級別
logger.propagate = False

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = f"{Fore.GREEN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.DEBUG:
            record.msg = f"{Fore.CYAN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == HIGHLIGHT_LEVEL:
            record.msg = f"{Fore.LIGHTYELLOW_EX}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{Fore.LIGHTRED_EX}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)



formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
