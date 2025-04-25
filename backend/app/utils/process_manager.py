from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.utils.process_documents import run_process_document


class ProcessStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessManager:
    def __init__(self):
        self._future: Optional[Future] = None
        self._result: Any = None
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._last_run_time: Optional[datetime] = None
        self._status = ProcessStatus.IDLE

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self.shutdown()

    def __del__(self):
        self.shutdown()

    def shutdown(self) -> None:
        """Safely shuts down the process executor and cancels any running process."""
        if self._future and not self._future.done():
            self._future.cancel()
            self._status = ProcessStatus.CANCELLED
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def is_running(self) -> bool:
        try:
            if self._future is None:
                return False
            return not self._future.done()
        except Exception:
            return False

    def run_process(self) -> None:
        if self.is_running():
            raise RuntimeError("Process already running")

        try:
            print("Process starting")
            self._last_run_time = datetime.now()
            if self._executor is None:
                self._executor = ProcessPoolExecutor(max_workers=1)
            self._status = ProcessStatus.RUNNING
            self._future = self._executor.submit(run_process_document)
            self._future.add_done_callback(self._process_completed)
        except Exception as e:
            self.shutdown()
            self._status = ProcessStatus.FAILED
            raise RuntimeError(f"Failed to start process: {str(e)}")

    def _process_completed(self, future: Future) -> None:
        """Callback handler for process completion."""
        try:
            if future.cancelled():
                self._status = ProcessStatus.CANCELLED
                self.shutdown()
            elif future.exception() is not None:
                print(f"Process failed with error: {future.exception()}")
                self._status = ProcessStatus.FAILED
                self.shutdown()
            else:
                result = future.result()
                self._status = ProcessStatus.COMPLETED
                self._result = result
                self.shutdown()
        except Exception as e:
            self.shutdown()
            print(f"Error in process completion handler: {str(e)}")
            self._status = ProcessStatus.FAILED

    @property
    def status(self) -> ProcessStatus:
        """Returns the current status of the process."""
        return self._status

    @property
    def last_run_time(self) -> Optional[datetime]:
        """Returns the timestamp of the last process execution."""
        return self._last_run_time
