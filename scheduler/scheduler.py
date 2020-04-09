from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):

    def __init__(self, ):
        super().__init__()
        self.configure_scheduler()
        self.register_routes()

    def configure_scheduler(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def register_routes(self):
        @self.route('/')
        async def schedule(request):
            self.scheduler.add_job(self.run_job, "interval", seconds=3)
            return JSONResponse(True)

    def run_job(self):
        print(f"Tick! The time is: {datetime.now()}")


scheduler = Scheduler()
