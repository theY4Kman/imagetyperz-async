import logging
from typing import TypeVar

T = TypeVar('T')


###
# Add a TRACE log level, if one does not already exist
#
TRACE = logging.getLevelName('TRACE')
if not isinstance(TRACE, int):
    TRACE = 5
    logging.addLevelName(TRACE, 'TRACE')


def getLogger(name: str) -> 'Logger':
    logger = logging.getLogger(name)
    logger.__class__ = Logger
    return logger


class Logger(logging.Logger):
    """Logger supporting TRACE level, and convenient sub-logger creation
    """
    def subLogger(self: T, name: str) -> T:
        return getLogger(f'{self.name}.{name}')

    sub_logger = subLogger

    def trace(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'TRACE'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.trace("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        if self.isEnabledFor(TRACE):
            self._log(TRACE, msg, args, **kwargs)


class ClassLoggingProperty:
    """A class-level property declaration exposing a logger with the class's name
    """
    def __init__(self, parent: Logger):
        self.parent = parent

    def __get__(self, obj, cls) -> Logger:
        try:
            return cls._logger
        except AttributeError:
            cls._logger = self.parent.subLogger(cls.__name__)
            return cls._logger
