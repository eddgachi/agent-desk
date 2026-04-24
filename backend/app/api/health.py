from app.core.database import test_db_connection
from app.core.redis_client import redis_client
from app.tasks.ping import ping_task
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health():
    db_ok = False
    try:
        await test_db_connection()
        db_ok = True
    except:
        pass
    redis_ok = False
    try:
        await redis_client.client.ping()
        redis_ok = True
    except:
        pass
    return {"status": "ok", "db": db_ok, "redis": redis_ok}


@router.get("/celery-ping")
async def celery_ping():
    result = ping_task.delay("from_api")
    return {"task_id": result.id, "status": result.state}
