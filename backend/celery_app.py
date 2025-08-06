from celery import Celery
from celery.schedules import crontab


celery_app = Celery(
    "calendar_backend_tasks",
    broker="redis://localhost:6379/0", 
    backend="redis://localhost:6379/0",
)

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "expire-invitations-every-hour": {
        "task": "tasks.expire_passed_invitations",
        "schedule": crontab(minute=0), 
    },
}