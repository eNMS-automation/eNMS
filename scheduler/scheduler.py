from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncio import get_event_loop
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


class Scheduler(Starlette):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scheduler = AsyncIOScheduler()
        scheduler.start()


async def schedule(request):
    print(request)
    tick = lambda: f"Tick! The time is: {datetime.now()}"
    scheduler.add_job(tick, "interval", seconds=3)
    return JSONResponse({"hello": "world"})



scheduler = Scheduler(debug=True, routes=[Route("/", schedule)])
