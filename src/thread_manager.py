import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal

class ThreadManager(QObject):
    thread_status = pyqtSignal(str)
    
    def __init__(self, max_workers=5):
        super().__init__()
        self._is_shutting_down = False
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
    
    def submit(self, fn, *args, **kwargs):
        if self._is_shutting_down:
            return None
        
        future = self._pool.submit(fn, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def shutdown(self, timeout=3, cancel_futures=True):
        self._is_shutting_down = True
        self.thread_status.emit("Завершение работы потоков...")
        
        if cancel_futures:
            for future in self._futures:
                future.cancel()
        
        if timeout > 0:
            start_time = time.time()
            active_futures = [f for f in self._futures if not f.done()]
            
            if active_futures:
                self.thread_status.emit(f"Ожидание завершения {len(active_futures)} задач...")
                
                for future in active_futures:
                    remaining = timeout - (time.time() - start_time)
                    if remaining <= 0:
                        break
                    try:
                        future.result(timeout=remaining)
                    except:
                        pass
        
        self._pool.shutdown(wait=False)
        self.thread_status.emit("Работа потоков завершена")
    
    def is_shutting_down(self):
        return self._is_shutting_down
    
    def wait_for_futures(self, futures=None, timeout=None):
        if futures is None:
            futures = self._futures
        
        for future in as_completed(futures, timeout=timeout):
            if self._is_shutting_down:
                break
            try:
                future.result(timeout=1)
            except:
                pass