import atexit
import json
import logging
import logging.config
import queue
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler

from app.core.conf import ENV, LOG_FILE

log_queue = queue.Queue(-1)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context"):
            log_record["context"] = record.context
        return json.dumps(log_record)


json_formatter = JSONFormatter()

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)

file_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    utc=True,
)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(json_formatter)

KAFKA_LOG_FILE = "logs/kafka.log"
kafka_file_handler = TimedRotatingFileHandler(
    KAFKA_LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    utc=True,
)
kafka_file_handler.suffix = "%Y-%m-%d"
kafka_file_handler.setFormatter(json_formatter)

queue_handler = QueueHandler(log_queue)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "json": {
            "format": json.dumps(
                {
                    "time": "%(asctime)s",
                    "level": "%(levelname)s",
                    "logger": "%(name)s",
                    "message": "%(message)s",
                }
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG" if ENV == "dev" else "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "()": TimedRotatingFileHandler,
            "formatter": "json",
            "level": "WARNING",
            "filename": LOG_FILE,
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
        },
        "queue": {
            "()": QueueHandler,
            "queue": log_queue,
        },
        "kafka_file": {
            "()": TimedRotatingFileHandler,
            "formatter": "json",
            "level": "DEBUG",
            "filename": KAFKA_LOG_FILE,
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["queue"],
        "level": "DEBUG" if ENV == "dev" else "INFO",
    },
    "loggers": {
        "aiokafka": {
            "handlers": ["kafka_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "kafka": {
            "handlers": ["kafka_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

listener = QueueListener(log_queue, console_handler, file_handler)
listener.start()
atexit.register(listener.stop)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if ENV == "dev" else logging.INFO)
    logger.addHandler(queue_handler)
    logger.propagate = False
    return logger


def safe_log(logger, msg, **kwargs):
    REDACT_KEYS = {"password", "token", "secret"}
    safe_kwargs = {k: ("***" if k in REDACT_KEYS else v) for k, v in kwargs.items()}
    logger.info(msg, extra={"context": safe_kwargs})
