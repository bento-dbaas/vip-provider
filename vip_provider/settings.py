from collections import OrderedDict
from os import getenv


MONGODB_HOST = getenv("MONGODB_HOST", "127.0.0.1")
MONGODB_PORT = int(getenv("MONGODB_PORT", 27017))
MONGODB_DB = getenv("MONGODB_DB", "vip_provider")
MONGODB_USER = getenv("MONGODB_USER", None)
MONGODB_PWD = getenv("MONGODB_PWD", None)
MONGODB_ENDPOINT = getenv("DBAAS_MONGODB_ENDPOINT", None)

MONGODB_PARAMS = {'document_class': OrderedDict}
if MONGODB_ENDPOINT:
    MONGODB_PARAMS["host"] = MONGODB_ENDPOINT
else:
    MONGODB_PARAMS['host'] = MONGODB_HOST
    MONGODB_PARAMS['port'] = MONGODB_PORT
    MONGODB_PARAMS['username'] = MONGODB_USER
    MONGODB_PARAMS['password'] = MONGODB_PWD

APP_USERNAME = getenv("APP_USERNAME", None)
APP_PASSWORD = getenv("APP_PASSWORD", None)

HTTP_PROXY = getenv("DBAAS_HTTP_PROXY", None)
HTTPS_PROXY = getenv("DBAAS_HTTPS_PROXY", None)

AWS_PROXY = getenv("AWS_PROXY", None)
TEAM_API_URL = getenv("TEAM_API_URL", None)
SENTRY_DSN = getenv("SENTRY_DSN", None)
LOGGING_LEVEL = getenv("LOGGING_LEVEL", None)
