import os

from pathlib import Path

from .prod import *  # noqa

# Use file rankie/settings/env for setting environment variables:
# - SECRET_KEY
# - SOCIAL_AUTH_TELEGRAM_BOT_TOKEN
ENV_PATH = Path(__file__).resolve().parent / "env"

if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f.readlines():
            sep = line.find("=")
            key = line[:sep].strip()
            val = line[sep + 1 :].strip()
            os.environ[key] = val

ALLOWED_HOSTS = []
DEBUG = True
