import logging
import os

log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log.log')
if not os.path.exists(os.path.dirname(log_file)):
    os.makedirs(os.path.dirname(log_file))


def clear_log_file() -> bool:
    try:
        with open(log_file, 'w') as f:
            return True
    except:
        return False


log_format = '[%(asctime)s] [%(levelname)s] %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
file_handler = logging.FileHandler(log_file, mode='a')

logging.basicConfig(level=logging.DEBUG, format=log_format, datefmt=date_format)

logger_instance = logging.getLogger(__name__)
logger_instance.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger_instance.addHandler(file_handler)


class MyLogger:
    @classmethod
    def debug(cls, *msg):
        logger_instance.debug(' '.join([str(m) for m in msg]))

    @classmethod
    def info(cls, *msg):
        logger_instance.info(' '.join([str(m) for m in msg]))

    @classmethod
    def warning(cls, *msg):
        logger_instance.warning(' '.join([str(m) for m in msg]))

    warn = warning

    @classmethod
    def error(cls, *msg):
        logger_instance.error(' '.join([str(m) for m in msg]))

    @classmethod
    def critical(cls, *msg):
        logger_instance.critical(' '.join([str(m) for m in msg]))

    fatal = critical

    @classmethod
    def exception(cls, *msg):
        logger_instance.exception(' '.join([str(m) for m in msg]))

    @classmethod
    def log(cls, level, *msg):
        logger_instance.log(level, ' '.join([str(m) for m in msg]))

    @classmethod
    def setLevel(cls, level):
        logger_instance.setLevel(level)


logger = MyLogger
