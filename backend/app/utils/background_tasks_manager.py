from typing import Dict
from uuid import uuid4
from datetime import datetime, timedelta
import threading

tasks_lock = threading.Lock()

def safe_access(func):
    def wrapper(*args, **kwargs):
        with tasks_lock:
            return func(*args, **kwargs)
    return wrapper


tasks: Dict[str, dict] = {}

@safe_access
def create_task():
    _cleanup_old_tasks()
    task_id = str(uuid4())
    tasks[task_id] = {"status": "pending", "answer": None, "sources": [], "expires_at": datetime.now() + timedelta(hours=1)}
    return task_id

@safe_access
def update_task(task_id: str, answer: str, sources: list):
    _cleanup_old_tasks()
    previous_task = tasks.get(task_id)
    if not previous_task:
        raise ValueError(f"Task {task_id} not found")
    tasks[task_id] = {"status": "done", "answer": answer, "sources": sources, "expires_at": previous_task["expires_at"]}

@safe_access
def fail_task(task_id: str, error: str):
    _cleanup_old_tasks()
    previous_task = tasks.get(task_id)
    if not previous_task:
        raise ValueError(f"Task {task_id} not found")
    tasks[task_id] = {"status": "error", "error": error, "expires_at": previous_task["expires_at"]}

@safe_access
def get_task(task_id: str):
    _cleanup_old_tasks()
    return tasks.get(task_id)

@safe_access
def remove_task(task_id: str):
    if task_id in tasks:
        del tasks[task_id]

def _cleanup_old_tasks():
    """Remove tasks older than 1 hour."""
    now = datetime.now()
    for task_id, task in list(tasks.items()):
        if task["expires_at"] < now:
            remove_task(task_id)
