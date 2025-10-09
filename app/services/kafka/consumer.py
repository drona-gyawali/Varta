import asyncio
from aiokafka import AIOKafkaConsumer, TopicPartition
from app.core.conf import kafkaHost, kafkaPassword, kafkaUsername, saslKafka
from app.core.logger import setup_logger
from app.core.database import DbInstance

logger = setup_logger("kafka.consumer")

class Consumer:
    def __init__(self):
        self.consumer_client = AIOKafkaConsumer(
            "MESSAGES",
            bootstrap_servers=kafkaHost,
            security_protocol="SASL_SSL",
            sasl_mechanism="PLAIN",
            sasl_plain_username=kafkaUsername,
            sasl_plain_password=kafkaPassword,
            ssl_context=saslKafka,
            group_id="my-group",
            auto_offset_reset="earliest",
        )

        
    async def start(self, class_name, func_name: str):
        await self.consumer_client.start()
        tp = TopicPartition("MESSAGES", 0)
        try:
            async for msg in self.consumer_client:
                try:
                    data = msg.value.decode("utf-8")
                    logger.info(f"Message Received: {data}")
                    await DbInstance.process_db_sockets(class_name, func_name, data)
                except Exception as e:
                    logger.error(f"Processing error: {str(e)}")
                    self.consumer_client.pause(tp)
                    logger.warning("Kafka Consumer paused for 5 seconds")
                    await asyncio.sleep(5)
                    self.consumer_client.resume(tp)
                    logger.info("Kafka Consumer resumed")
        finally:
            await self.consumer_client.stop()



ConsumerClient = Consumer()
