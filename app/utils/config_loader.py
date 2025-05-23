import json
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

# Load configuration from config.json
#CONFIG_PATH = Path("E:/smart-quiz/config.json")
CONFIG_PATH = Path("config.json")

try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    # Logger not yet configured, so use print
    print("config.json not found")
    raise
except json.JSONDecodeError:
    print("Invalid JSON in config.json")
    raise

# Configure logging
logger = logging.getLogger(__name__)
logging_config = CONFIG.get('logging', {})
log_level = getattr(logging, logging_config.get('level', 'INFO').upper(), logging.INFO)

# Configure TimedRotatingFileHandler
rotating_config = logging_config.get('rotating_file_handler', {})
log_handler = TimedRotatingFileHandler(
    filename=Path(logging_config.get('logpath', 'app.log')),
    when=rotating_config.get('when', 'midnight'),
    interval=rotating_config.get('interval', 1),
    backupCount=rotating_config.get('backupCount', 7)
)
log_handler.setFormatter(
    logging.Formatter(logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
)

logging.basicConfig(
    level=log_level,
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)

logger.info("Logging configured with level %s, output to %s, rotation when=%s, interval=%s, backupCount=%s",
           logging_config.get('level', 'INFO'),
           logging_config.get('logpath', 'app.log'),
           rotating_config.get('when', 'midnight'),
           rotating_config.get('interval', 1),
           rotating_config.get('backupCount', 7))