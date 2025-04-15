import json
from contextlib import asynccontextmanager

import uvicorn
from anyio.streams.file import FileWriteStream
from app.config import settings
from app.database import (
    add_existing_documents,
    create_admin_user,
    create_db_and_tables,
    get_session,
)
from app.routers import documents, users
from app.utils.preview import PreviewManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_and_tables()
    add_existing_documents()
    create_admin_user()
    print("Database initialized")

    with next(get_session()) as session:
        try:
            preview_manager = PreviewManager()
            await preview_manager.generate_all_previews(session)
        except Exception as e:
            print(f"Error generating previews: {e}")

    try:
        path = "./openapi.json"
        async with await FileWriteStream.from_path(path) as stream:
            openapi_schema = app.openapi()
            await stream.send(json.dumps(openapi_schema).encode("utf-8"))
        print(f"OpenAPI spec saved to {path}")
    except Exception as e:
        print(f"Error writing OpenAPI spec: {e}")

    yield
    print("Shutting down...")


# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
