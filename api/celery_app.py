"""Celery application configuration for async task processing.

This module creates and configures the Celery instance used by:
- API routes (to enqueue jobs)
- Worker processes (to execute jobs)
- Flower (to monitor jobs)
"""
import os
from celery import Celery


def make_celery() -> Celery:
    """Create and configure Celery instance.

    Returns:
        Configured Celery application instance
    """
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    celery = Celery(
        'scraper_tasks',
        broker=broker_url,
        backend=result_backend,
        include=[
            'api.src.tasks.scraper_tasks',
            'api.src.tasks.image_analysis_tasks',
            'api.src.tasks.rebrand_tasks'
        ]
    )

    # Update configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_send_sent_event=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=10,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        result_expires=3600,  # Results expire after 1 hour
    )

    return celery


# Create global Celery instance
celery_app = make_celery()
