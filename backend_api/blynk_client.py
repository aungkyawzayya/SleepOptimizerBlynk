import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

BLYNK_AUTH_TOKEN = os.getenv("BLYNK_AUTH_TOKEN")