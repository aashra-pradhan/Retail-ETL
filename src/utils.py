import logging
import os

# Logging setup
def setup_logger(name="ETL_LOGGER", log_file="logs/etl.log"):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger
