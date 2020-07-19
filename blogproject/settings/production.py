from .common import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = True

ALLOWED_HOSTS = [
    "hellodjango-blog-tutorial-demo.zmrenwu.com",
    "127.0.0.1",
    "192.168.10.73",
]
HAYSTACK_CONNECTIONS["default"]["URL"] = "http://elasticsearch:9200/"

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "redis://:UJaoRZlNrH40BDaWU6fi@redis:6379/0",
        "OPTIONS": {
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {"max_connections": 50, "timeout": 20},
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    },
}
