import time
import threading

class ServiceTimer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceTimer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._duration_ms = 0
        self._timer = None
        self._running = False
        self._start_callbacks = []
        self._tick_callbacks = []
        self._end_callbacks = []
        self._tick_interval_ms = 1000  # Default: 1 second
        self._initialized = True
    
    
    def reset_progress(self):
        """Reset timer progress to full duration without stopping the timer"""
        if self._running:
            # Recalculate end time based on current time + full duration
            self._end_time = time.time() + (self._duration_ms / 1000) + 1
        return self
    
    
    def add_time(self, milliseconds):
        """Add milliseconds to the timer's remaining time"""
        if self._running:
            self._end_time += milliseconds / 1000
        else:
            self._duration_ms += milliseconds
        return self

    def subtract_time(self, milliseconds):
        """Subtract milliseconds from the timer's remaining time"""
        if self._running:
            self._end_time = max(time.time(), self._end_time - milliseconds / 1000)
        else:
            self._duration_ms = max(0, self._duration_ms - milliseconds)
        return self
    
    
    def get_duration(self):
        """Return the timer duration in milliseconds"""
        return self._duration_ms
    
    
    def set_duration(self, milliseconds):
        """Set timer duration in milliseconds"""
        self._duration_ms = milliseconds
        return self
        
    def set_tick_interval(self, milliseconds):
        """Set tick interval in milliseconds (minimum 1000ms)"""
        self._tick_interval_ms = max(1000, milliseconds)
        return self
    
    def on_start(self, callback):
        """Register callback to be called when timer starts"""
        self._start_callbacks.append(callback)
        return self
    
    def on_tick(self, callback):
        """Register callback to be called on each tick interval"""
        self._tick_callbacks.append(callback)
        return self
        
    def on_end(self, callback):
        """Register callback to be called when timer ends"""
        self._end_callbacks.append(callback)
        return self
    
    def start(self):
        """Start the timer"""
        if self._running:
            return False
            
        self._running = True
        self._start_time = time.time()
        self._end_time = self._start_time + (self._duration_ms / 1000)
        
        # Call start callbacks
        for callback in self._start_callbacks:
            callback()
        
        # Start the timer thread
        self._timer = threading.Thread(target=self._run)
        self._timer.daemon = True
        self._timer.start()
        
        return True
    
    def reset(self):
        """Reset timer to original duration"""
        was_running = self.stop()
        
        if was_running:
            self.start()
    
    def stop(self):
        """Stop the timer"""
        if not self._running:
            return False
            
        self._running = False
        
        # Wait for timer thread to finish
        if self._timer and self._timer.is_alive():
            self._timer.join(0.1)
        
        return True
    
    def _run(self):
        """Internal method to run the timer"""
        next_tick = time.time() + (self._tick_interval_ms / 1000)
        
        while self._running:
            current_time = time.time()
            
            # Check if timer ended
            if current_time >= self._end_time:
                self._running = False
                for callback in self._end_callbacks:
                    callback()
                break
            
            # Check if it's time for a tick
            if current_time >= next_tick:
                for callback in self._tick_callbacks:
                    callback()
                next_tick = current_time + (self._tick_interval_ms / 1000)
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.01)

    def get_remaining_ms(self):
        """Return the remaining time in milliseconds"""
        if not self._running:
            return self._duration_ms
        
        remaining_seconds = max(0, self._end_time - time.time())
        return int(remaining_seconds * 1000)