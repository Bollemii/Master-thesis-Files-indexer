from datetime import datetime
from typing import Optional
from concurrent.futures import wait
from concurrent.futures import ProcessPoolExecutor
from app.utils.process_documents import run_process_document


class ProcessManager:
    def __init__(self):
        self._future = None
        self._result = None
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._last_run_time: Optional[datetime] = None
        
    def is_running(self) -> bool:
        if self._future is None:
            return False
        else:
            return self._future.running()
            
    def run_process(self, documents, session):            
        self._future = self._executor.submit(run_process_document, documents, session)

    def get_result(self):
        wait([self._future])
        return self._future.result()