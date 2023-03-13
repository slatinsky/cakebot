import os
import logging
import sys
import time

from logging.handlers import RotatingFileHandler
from utils import Config


class LogController:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(Config.LOG_LEVEL)

        if not self.logger.hasHandlers():
            formatter = logging.Formatter(
                "[%(levelname)s] %(asctime)s: %(filename)s | %(message)s",
                "%Y-%m-%d %H:%M:%S")
            formatter.converter = time.gmtime

            if not os.path.exists("logs"):
                os.makedirs("logs")

            file_handler = RotatingFileHandler("logs/discord.log", maxBytes=Config.LOG_MAX_SIZE * 1000000,
                                               backupCount=Config.LOG_MAX_FILES)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
