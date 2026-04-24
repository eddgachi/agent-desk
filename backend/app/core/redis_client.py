import redis.asyncio as redis


class RedisClient:
    def __init__(self):
        self.client = None

    async def initialize(self):
        from app.config import settings

        self.client = await redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        if self.client:
            await self.client.close()


redis_client = RedisClient()
