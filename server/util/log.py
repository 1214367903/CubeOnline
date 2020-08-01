import logging

# 五大等级:'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
STREAM_LEVEL = logging.INFO
STREAM_FORMAT = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')


def get_logger() -> logging.Logger:
    # 本来的目标是可以创建多种多样的logger的,但是后来发现,没有必要,直接用root就好
    # 最关键的是, 除了root之外的logger全都被tornado接管了
    # 实际上,这里输出的日志也会被记录到tornado的日志文件中
    return _logger


def create_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 添加 StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(STREAM_LEVEL)
    stream_handler.setFormatter(STREAM_FORMAT)
    logger.addHandler(stream_handler)
    return logger


_logger = create_logger()
