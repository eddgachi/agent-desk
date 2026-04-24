from app.core.celery_app import celery_app


@celery_app.task
def ping_task(message: str) -> dict:
    return {"echo": message, "status": "pong"}
