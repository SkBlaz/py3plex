"""
Celery application configuration
"""
from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "py3plex_gui",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
    result_expires=3600,
)

if __name__ == '__main__':
    celery_app.start()
