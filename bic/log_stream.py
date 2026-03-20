import asyncio
import queue

class QueueLogger:
    def __init__(self):
        self.log_queue = asyncio.Queue()

    def write(self, msg):
        if msg.strip(): # Avoid empty lines
            self.log_queue.put_nowait(msg)

    def flush(self):
        pass # No-op

    async def listen(self):
        while True:
            log_entry = await self.log_queue.get()
            yield log_entry

queue_logger = QueueLogger()
