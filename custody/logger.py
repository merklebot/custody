import logging
from sys import stdout

logger = logging.getLogger("custodyLogger")

logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter(
    "LOGGER_NAME=%(name)-12s ASCTIME=%(asctime)s LEVEL=%(levelname)-8s "
    "SOURCE_FUNC=%(filename)s:%(funcName)s ACTION=%(action)s PACK_UUID=%(pack_uuid)s "
    "MESSAGE=%(message)s"
)
consoleHandler = logging.StreamHandler(stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
