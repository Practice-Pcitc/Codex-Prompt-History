import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.workbench import router as workbench_router
from app.api.v1.router import router
from app.core.database import initialize_prompt_history_database
from app.core.http import register_http_handlers
from app.services.collector import collector
from app.services.workbench import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_prompt_history_database()
    settings()
    stop = asyncio.Event()

    async def collect():
        while not stop.is_set():
            await asyncio.to_thread(collector.sync)
            try:
                await asyncio.wait_for(stop.wait(), timeout=5)
            except TimeoutError:
                pass

    task = asyncio.create_task(collect())
    try:
        yield
    finally:
        stop.set()
        await task


app = FastAPI(title="Codex Prompt History API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
register_http_handlers(app)
app.include_router(router, prefix="/api/v1")
app.include_router(workbench_router, prefix="/api/v1")
app.include_router(router, prefix="/api", include_in_schema=False)
