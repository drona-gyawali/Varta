import os
import ssl

from dotenv import load_dotenv

load_dotenv()


# Helper fx
def context(certPath):
    return ssl.create_default_context(cafile=certPath)


# Logger configuration
ENV = os.getenv("ENV", "dev")
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")


# Redis configuration
REDISCONF = {
    "redisHost": os.getenv("REDISHOST"),
    "redisPort": os.getenv("REDISPORT"),
    "redisDb": os.getenv("REDISDB"),
    "redisPassword": os.getenv("REDISPASSWORD"),
}


# Database configuration
DATABASE = {
    "DbUrl": os.getenv("DATABASEURL"),
    "SslCertPath": os.getenv("SSL_CERT_PATH"),
}

ssl_context = context(DATABASE.get("SslCertPath"))
DbInit = DATABASE.get("DbUrl")

# Kafka Configuration
KAFKA = {
    "KAFKAHOST": os.getenv("KAFKAHOST"),
    "KAFKAUSERNAME": os.getenv("KAFKAUSERNAME"),
    "KAFKAPASSWORD": os.getenv("KAFKAPASSWORD"),
    "SSL_CERT_PATH_KAFKA": os.getenv("SSL_CERT_PATH_KAFKA"),
}

kafkaHost = KAFKA.get("KAFKAHOST")
kafkaUsername = KAFKA.get("KAFKAUSERNAME")
kafkaPassword = KAFKA.get("KAFKAPASSWORD")
saslKafka = context(KAFKA.get("SSL_CERT_PATH_KAFKA"))


# JWT Configuration
SECRETKEY = os.getenv("SECRETKEY")
ALGORITHM = os.getenv("ALGORITHM")
TOKENEXPIRY = os.getenv("ACCESSTOKENEXPIREMINUTES")


# allowed origins -> only valid for dev purpose
origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://192.168.100.193:5501",
]


MULTI_INSTANCE = os.getenv("MULTI_INSTANCE", "false").lower() == "true"
