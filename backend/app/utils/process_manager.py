import asyncio
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from app.utils.process_documents import run_process_document


class ProcessManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._is_running = False
        self._last_run_time: Optional[datetime] = None
        
    async def is_process_running(self) -> bool:
        async with self._lock:
            return self._is_running
            
    async def get_status(self):
        async with self._lock:
            return {
                "is_running": self._is_running,
                "last_run_time": self._last_run_time,
            }
            
    async def run_process(self, documents, session):
        if await self.is_process_running():
            raise HTTPException(
                status_code=409,
                detail="Process is already running"
            )
            
        try:
            async with self._lock:
                self._is_running = True
                
            run_process_document(documents, session)
            
        finally:
            async with self._lock:
                self._is_running = False
                self._last_run_time = datetime.now()