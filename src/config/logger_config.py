import logging
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def get_logger(name):
    """
    Get a logger configured for the specified module.
    Args:
        name: The name of the module (typically __name__)
    Returns:
        A configured logger instance
    """
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        if COLORLOG_AVAILABLE:
            handler = colorlog.StreamHandler()
            handler.setFormatter(colorlog.ColoredFormatter(
                '[%(log_color)s%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d) | %(message)s\n',
                log_colors={
                    'DEBUG':    'cyan',
                    'INFO':     'green',
                    'WARNING':  'yellow',
                    'ERROR':    'red',
                    'CRITICAL': 'bold_red',
                }
            ))
            root_logger.addHandler(handler)
            root_logger.setLevel(logging.DEBUG)
        else:
            logging.basicConfig(
                level=logging.DEBUG,
                format='[%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d) | %(message)s\n'
            )
    return logging.getLogger(name)

# For backward compatibility
logger = get_logger(__name__)

# Suppress noisy loggers from third-party libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)