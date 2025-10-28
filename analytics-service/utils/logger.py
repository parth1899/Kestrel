# analytics-service/utils/logger.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

log = logging.getLogger("analytics")