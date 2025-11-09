import logging

from app.core.conf import ENV


def setup_logger(name: str) -> logging.Logger:
    """
    Simple logger setup for async-friendly apps.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        level = logging.DEBUG if ENV == "dev" else logging.INFO
        logger.setLevel(level)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(ch)

        logger.propagate = False

    return logger


def safe_log(logger, msg, **kwargs):
    """
    Logs safely with sensitive info redacted.
    """
    REDACT_KEYS = {"password", "token", "secret"}
    safe_kwargs = {k: ("***" if k in REDACT_KEYS else v) for k, v in kwargs.items()}
    logger.info(msg, extra={"context": safe_kwargs})
