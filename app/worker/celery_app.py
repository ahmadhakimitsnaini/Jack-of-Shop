import os
from celery import Celery
from kombu import Queue

# Memaksa celery membaca URL redis dari environment atau config
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "jaknote_shopee_worker",
    broker=redis_url,
    backend=redis_url
)

# Konfigurasi antrean (Queues)
celery_app.conf.task_queues = (
    Queue("default", routing_key="task.#"),
    Queue("scrape_queue", routing_key="scrape.#"),
    Queue("ai_queue", routing_key="ai.#"),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "tasks"
celery_app.conf.task_default_routing_key = "task.default"

# Memastikan task terdeteksi
celery_app.conf.imports = ("app.worker.tasks",)
