import os

from dotenv import load_dotenv

load_dotenv()

ALLOW_ORIGIN_REGEX = os.getenv("ALLOW_ORIGIN_REGEX")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "").split(",")

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
