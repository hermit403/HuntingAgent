import time
import asyncio
from collections import defaultdict
from fastapi import Request, HTTPException
import logging

class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
        
    def limit(self, limit_str: str):
        try:
            count, period = limit_str.split("/")
            limit_count = int(count)
            window_seconds = 60 if period == "minute" else 1
        except:
            limit_count = 2
            window_seconds = 60
            
        return self._make_dependency(limit_count, window_seconds)

    def _make_dependency(self, limit_count: int, window_seconds: int):
        async def dependency(request: Request):
            client_id = request.client.host
            current_time = time.time()
            
            async with self.lock:
                self.requests[client_id] = [
                    t for t in self.requests[client_id] 
                    if current_time - t < window_seconds
                ]

                if len(self.requests[client_id]) >= limit_count:
                    logging.warning(f"Rate limit exceeded for {client_id}")
                    raise HTTPException(
                        status_code=429, 
                        detail="Too Many Requests"
                    )
                
                self.requests[client_id].append(current_time)
            return True
        return dependency

limiter = SimpleRateLimiter()
