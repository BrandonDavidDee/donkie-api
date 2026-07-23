import logging

LOG_COLORS = {
    "DEBUG": "\033[94m",
    "INFO": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "CRITICAL": "\033[95m",
}


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_color: str = LOG_COLORS.get(record.levelname, "\033[0m")
        reset_color: str = "\033[0m"
        record.msg = f"{log_color}{record.msg}{reset_color}"
        return super().format(record)


def setup_logger() -> logging.Logger:
    donkie_logger = logging.getLogger("event_run_logger")
    donkie_logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    donkie_logger.addHandler(console_handler)
    return donkie_logger


logger = setup_logger()
