import os
from intasend import APIService


INTASEND_PUB_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
INTASEND_SECRET = os.getenv("INTASEND_SECRET_TOKEN")
# Load test mode from env (default True for safety)
INTASEND_TEST_MODE = os.getenv("INTASEND_TEST_MODE", "true").lower() in ("1", "true", "yes")

intasend = APIService(token=INTASEND_SECRET, publishable_key=INTASEND_PUB_KEY, test=INTASEND_TEST_MODE)
