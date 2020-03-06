import logging
# from slacker_log_handler import SlackerLogHandler  # pyre-ignore
from slack_log_utils import SlackWebhookFormatter, SlackWebhookHandler


def get_slack_logging_handler(secret):
    slack_formatter = SlackWebhookFormatter()
    slack_handler = SlackWebhookHandler(url=secret, level=logging.ERROR)
    slack_handler.setFormatter(slack_formatter)
    # slack_handler = SlackerLogHandler(secret, "#karp-tng-log", stack_trace=True)
    # slack_handler.setLevel(logging.ERROR)
    return slack_handler
