import os
from redis import Redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    # Listen to the 'default' queue
    listen = ['default']
    
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        print("Starting RQ worker...")
        worker.work()
