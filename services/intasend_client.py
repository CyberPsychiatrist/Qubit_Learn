import os
from intasend import APIService

INTASEND_PUB_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
INTASEND_SECRET = os.getenv("INTASEND_SECRET_TOKEN")

intasend = APIService(token=INTASEND_SECRET, publishable_key=INTASEND_PUB_KEY, test=True)
