from PyQt6.QtCore import QThread, pyqtSignal

class DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)
    
    def __init__(self, download_manager, version_tag):
        super().__init__()
        self.download_manager = download_manager
        self.version_tag = version_tag
        self.is_cancelled = False
    
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        def progress_callback(value, text):
            self.progress.emit(value, text)
        
        def is_cancelled_callback():
            return self.is_cancelled
        
        success, message = self.download_manager.download_version(
            self.version_tag,
            progress_callback,
            is_cancelled_callback
        )
        
        self.finished.emit(success, message)