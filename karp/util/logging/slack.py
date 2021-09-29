import logging

from slack_log_utils import SlackWebhookFormatter, SlackWebhookHandler


def get_slack_logging_handler(secret):
    slack_formatter = SlackWebhookFormatter()
    slack_handler = SlackWebhookHandler(url=secret, level=logging.ERROR)
    slack_handler.setFormatter(slack_formatter)
    return slack_handler
