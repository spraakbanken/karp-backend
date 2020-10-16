import logging

from . import config


def setup_logging():
    logger = logging.getLogger("karp")
    # if app.config.get("LOG_TO_SLACK"):
    #     slack_handler = slack_logging.get_slack_logging_handler(
    #         app.config.get("SLACK_SECRET")
    #     )
    #     logger.addHandler(slack_handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.setLevel(config.CONSOLE_LOG_LEVEL)
    logger.addHandler(console_handler)
    return logger
