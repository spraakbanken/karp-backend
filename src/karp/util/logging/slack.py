import logging
from slacker_log_handler import SlackerLogHandler  # pyre-ignore


def get_slack_logging_handler(secret):
    slack_handler = SlackerLogHandler(secret, "#karp-tng-log", stack_trace=True)
    slack_handler.setLevel(logging.ERROR)
    return slack_handler
