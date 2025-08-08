import logging
import os
import time
from logging.handlers import RotatingFileHandler

class WindowsSafeRotatingFileHandler(RotatingFileHandler):
    """
    A RotatingFileHandler that is more Windows-friendly by handling file locking issues.
    
    This handler implements retry logic and uses different file operations to avoid
    the PermissionError that occurs on Windows when trying to rotate log files that
    are still being used by other processes.
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self._retry_count = 3
        self._retry_delay = 0.1  # seconds
    
    def doRollover(self):
        """
        Override the doRollover method to handle Windows file locking issues.
        
        This implementation includes retry logic and more careful file handling
        to avoid PermissionError on Windows.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
            
        if self.backupCount > 0:
            # Try to rename the existing backup files with retry logic
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d" % (self.baseFilename, i)
                dfn = "%s.%d" % (self.baseFilename, i + 1)
                
                # Try multiple times with small delays to handle file locking
                for attempt in range(self._retry_count):
                    try:
                        if os.path.exists(sfn):
                            if os.path.exists(dfn):
                                os.remove(dfn)
                            os.rename(sfn, dfn)
                        break  # Success, break out of retry loop
                    except (OSError, PermissionError) as e:
                        if attempt < self._retry_count - 1:
                            time.sleep(self._retry_delay)
                        else:
                            # If all retries failed, continue without this rotation
                            # This prevents the application from crashing
                            pass
            
            # Try to rename the current log file
            dfn = self.baseFilename + ".1"
            for attempt in range(self._retry_count):
                try:
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(self.baseFilename, dfn)
                    break  # Success, break out of retry loop
                except (OSError, PermissionError) as e:
                    if attempt < self._retry_count - 1:
                        time.sleep(self._retry_delay)
                    else:
                        # If we can't rotate the file, just continue logging to the same file
                        # This prevents the application from crashing
                        pass
        
        # Reopen the log file
        if not self.delay:
            self.stream = self._open()
    
    def emit(self, record):
        """
        Emit a record, with retry logic for Windows file locking issues.
        """
        for attempt in range(self._retry_count):
            try:
                super().emit(record)
                break  # Success, break out of retry loop
            except (OSError, PermissionError) as e:
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    # If all retries failed, we suppress the error to prevent application crash
                    # but we still want to know about it for debugging
                    try:
                        # Try to emit to stderr as a fallback
                        import sys
                        sys.stderr.write(f"Logging error (suppressed): {e}\n")
                    except:
                        pass