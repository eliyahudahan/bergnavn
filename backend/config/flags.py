# backend/config/flags.py

import os

# ניתן לשלוט דרך קובץ env או כאן ישירות
MAX_DUMMY_USERS = int(os.getenv("MAX_DUMMY_USERS", 5))
ENABLE_DUMMY_USERS = os.getenv("ENABLE_DUMMY_USERS", "true").lower() == "true"
