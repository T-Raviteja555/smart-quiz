import json
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

# Load configuration from config.json
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

# Configure TimedRotatingFileHandler for app logs
rotating_config = logging_config.get('rotating_file_handler', {})
app_log_handler = TimedRotatingFileHandler(
    filename=Path(logging_config.get('logpath', 'app.log')),
    when=rotating_config.get('when', 'midnight'),
    interval=rotating_config.get('interval', 1),
    backupCount=rotating_config.get('backupCount', 7)
)
app_log_handler.setFormatter(
    logging.Formatter(logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
)

# Configure TimedRotatingFileHandler for metrics logs
metrics_log_handler = TimedRotatingFileHandler(
    filename=Path(logging_config.get('metrics_logpath', 'metrics.log')),
    when=rotating_config.get('when', 'midnight'),
    interval=rotating_config.get('interval', 1),
    backupCount=rotating_config.get('backupCount', 7)
)
metrics_log_handler.setFormatter(
    logging.Formatter(logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
)
metrics_log_handler.setLevel(log_level)

# Configure TimedRotatingFileHandler for performance logs
performance_log_handler = TimedRotatingFileHandler(
    filename=Path(logging_config.get('performance_logpath', 'performance.log')),
    when=rotating_config.get('when', 'midnight'),
    interval=rotating_config.get('interval', 1),
    backupCount=rotating_config.get('backupCount', 7)
)
performance_log_handler.setFormatter(
    logging.Formatter(logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
)
performance_log_handler.setLevel(log_level)

# Configure logging for app
logging.basicConfig(
    level=log_level,
    handlers=[
        app_log_handler,
        logging.StreamHandler()
    ]
)

# Configure metrics logger
metrics_logger = logging.getLogger("metrics")
metrics_logger.setLevel(log_level)
metrics_logger.handlers = [metrics_log_handler]

# Configure performance logger
performance_logger = logging.getLogger("performance")
performance_logger.setLevel(log_level)
performance_logger.handlers = [performance_log_handler]

logger.info("Logging configured with level %s, output to %s, rotation when=%s, interval=%s, backupCount=%s",
           logging_config.get('level', 'INFO'),
           logging_config.get('logpath', 'app.log'),
           rotating_config.get('when', 'midnight'),
           rotating_config.get('interval', 1),
           rotating_config.get('backupCount', 7))
logger.info("Metrics logging configured with level %s, output to %s",
           logging_config.get('level', 'INFO'),
           logging_config.get('metrics_logpath', 'metrics.log'))
logger.info("Performance logging configured with level %s, output to %s",
           logging_config.get('level', 'INFO'),
           logging_config.get('performance_logpath', 'performance.log'))