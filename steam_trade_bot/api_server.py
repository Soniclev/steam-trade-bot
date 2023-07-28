from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import RedirectResponse

from steam_trade_bot.containers import Container
from steam_trade_bot.settings import BotSettings
import steam_trade_bot.api.routes
from steam_trade_bot.api.routes import router as routes_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/api/v1")
router.include_router(routes_router)


@router.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(
        app.docs_url,
        status_code=status.HTTP_302_FOUND)


app.include_router(router)

container = Container()
container.config.from_pydantic(BotSettings())
container.wire(packages=[steam_trade_bot.api.routes])
container.wire(modules=[__name__])
