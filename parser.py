import os
from datetime import datetime

def get_logger(feature_name: str):
    import logging

    logger = logging.getLogger(feature_name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        os.makedirs("logs", exist_ok=True)
        date_str = datetime.now().strftime("%d-%m-%y_%H%M")
        log_file = f"logs/{date_str}_{feature_name}.md"

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
