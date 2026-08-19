from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "millwater",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.route"],
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.update(
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "health_check_interval": 10,
    },
    beat_schedule={
        "rollover-route-statuses-daily": {
            "task": "app.tasks.route.rollover_route_statuses", 
            "schedule": crontab(hour=6, minute=0),
        },
    },
)