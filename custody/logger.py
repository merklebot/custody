import logging

from pythonjsonlogger import jsonlogger

logger = logging.getLogger("custodyLogger")

logger.setLevel(logging.DEBUG)

# logFormatter = logging.Formatter(
#     "LOGGER_NAME=%(name)-12s ASCTIME=%(asctime)s LEVEL=%(levelname)-8s "
#     "SOURCE_FUNC=%(filename)s:%(funcName)s ACTION=%(action)s PACK_UUID=%(pack_uuid)s "
#     "MESSAGE=%(message)s"
# )
formatter = jsonlogger.JsonFormatter()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
