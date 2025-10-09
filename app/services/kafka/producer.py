from aiokafka import AIOKafkaProducer
from app.core.conf import kafkaHost, kafkaPassword, kafkaUsername, saslKafka
from app.core.logger import setup_logger
import uuid

producer = None

logger = setup_logger("kafka.producer")

class Producer:
    def __init__(self):
        self.producer_client = AIOKafkaProducer(
            bootstrap_servers=kafkaHost,
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            sasl_plain_username=kafkaUsername,
            sasl_plain_password=kafkaPassword,
            ssl_context=saslKafka
        )

    async def create_producer(self):
        global producer

        try:
            if producer:
                return producer
            await self.producer_client.start()
            producer = self.producer_client
            return producer
        
        except Exception as e:
            logger.error(f"Error at creat_producer | error={e}")



    async def produce_message(self, message: str):
        try:
            producer = await self.create_producer()
            await producer.send_and_wait(
                topic="MESSAGES",
                value=message.encode(),
                key=str(uuid.uuid1()).encode()
            )
            logger.info("Message Produced to kafka")
        except Exception as e:
            logger.error(f"Unable to produce message | error={e}")


ProduceClient = Producer()
