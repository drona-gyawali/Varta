import asyncio

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from app.core.conf import RABBITMQ_HOST
from app.core.logger import setup_logger
from app.services.email import EmailService

logger = setup_logger("app.tasks")


def connection():
    rabbitmq_broker = RabbitmqBroker(url=RABBITMQ_HOST)
    dramatiq.set_broker(rabbitmq_broker)


try:
    connection()
    logger.info("Message Queue connection established")
except Exception as e:
    logger.warning(f"Connection Refused | module=tasks| error={e}")


@dramatiq.actor()
def task_email(subject, email, body, html=True):
    try:
        service = EmailService()
        asyncio.run(service.send_mail(subject, email, body, html))
    except Exception as e:
        logger.error(f"Task Falied | Task_Name: task_email | error={e}")
