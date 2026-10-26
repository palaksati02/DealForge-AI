import logging
import sys
import contextvars
from app.core.config import settings

# Thread-safe and async-safe request/correlation ID tracking
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get("-")
        return True


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [req:%(request_id)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Silence overly verbose third party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.DB_ECHO else logging.WARNING)

    dealforge_logger = logging.getLogger("dealforge")
    dealforge_logger.addFilter(RequestIdFilter())
    return dealforge_logger


logger = setup_logging()
