from apscheduler.schedulers.asyncio import AsyncIOScheduler
from json import load
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):

    def __init__(self, ):
        super().__init__()
        self.configure_scheduler()
        self.register_routes()

    def configure_scheduler(self):
        with open(Path.cwd().parent / "setup" / "scheduler.json", "r") as file:
            self.scheduler = AsyncIOScheduler(load(file))
        self.scheduler.start()

    def register_routes(self):
        @self.route("/add_job", methods=["POST"])
        async def schedule(request):
            self.scheduler.add_job(self.run_job, "interval", seconds=3)
            return JSONResponse(True)

        @self.route("/delete_job", methods=["POST"])
        async def schedule(request):
            data = await request.json()
            print(data)
            return JSONResponse(True)

    @staticmethod
    def run_job():
        print("test")


scheduler = Scheduler()
