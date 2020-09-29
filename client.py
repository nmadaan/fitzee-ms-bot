import aiohttp
import asyncio
import async_timeout
import requests

async def periodic():
    while True:
        print('xxx')
        requests.get("http://localhost:3978/api/notify")
        await asyncio.sleep(5)

def stop():
    task.cancel()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(periodic())
    loop.call_later(25, task.cancel)
    loop.run_until_complete(task)