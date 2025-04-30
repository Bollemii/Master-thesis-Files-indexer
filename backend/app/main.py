import json
from contextlib import asynccontextmanager

import uvicorn
from anyio.streams.file import FileWriteStream
from app.config import settings
from app.init_database import (
    add_existing_documents,
    create_admin_user,
)
from app.database.main import check_neo4j_connection
from app.routers import documents, users, chatbot
from app.utils.preview import PreviewManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Initialize database
@asynccontextmanager
async def lifespan(appli: FastAPI):
    print("Starting up...")
    if not check_neo4j_connection():
        raise ValueError("Could not connect to Neo4j database. Check your connection.")

    add_existing_documents()
    create_admin_user()
    print("Database initialized")

    try:
        preview_manager = PreviewManager()
        await preview_manager.generate_all_previews()
    except Exception as e:
        print(f"Error generating previews: {e}")

    try:
        path = "./openapi.json"
        async with await FileWriteStream.from_path(path) as stream:
            openapi_schema = appli.openapi()
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
app.include_router(chatbot.router, prefix=settings.API_V1_STR)

@app.get("/", status_code=200, tags=["Healthcheck"])
@app.head("/", status_code=200, tags=["Healthcheck"])
async def healthcheck():
    """
    Healthcheck endpoint to check if the server is running.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
