import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
