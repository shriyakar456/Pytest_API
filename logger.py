# logger.py
import logging

def setup_logger(name, log_file='app.log'):
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()  # ← for GitHub Actions logs
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger
