import datetime
import logging

from pythonjsonlogger import jsonlogger

logger = logging.getLogger("custodyLogger")

logger.setLevel(logging.DEBUG)


# logFormatter = logging.Formatter(
#     "LOGGER_NAME=%(name)-12s ASCTIME=%(asctime)s LEVEL=%(levelname)-8s "
#     "SOURCE_FUNC=%(filename)s:%(funcName)s ACTION=%(action)s PACK_UUID=%(pack_uuid)s "
#     "MESSAGE=%(message)s"
# )
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
