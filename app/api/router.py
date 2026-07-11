from fastapi import APIRouter

from app.api.endpoints import users, products
from app.worker.tasks import dummy_test_task

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])

@api_router.post("/test-worker", tags=["Test"])
async def test_worker(message: str = "Hello Celery"):
    """Endpoint sementara untuk mengetes Celery worker."""
    task = dummy_test_task.delay(message)
    return {"task_id": task.id, "status": "Task submitted to Celery"}

