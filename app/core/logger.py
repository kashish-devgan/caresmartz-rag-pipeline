import logging
from rich.logging import RichHandler
from app.core.config import settings

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger("rag_sync")
