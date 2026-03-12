from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import ssl

load_dotenv()

client = AsyncIOMotorClient(
    os.getenv("MONGO_URL"),
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = client[os.getenv("DB_NAME")]