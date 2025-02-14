from contextlib import asynccontextmanager
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from anyio.streams.file import FileWriteStream
import uvicorn

# from app.TopicModeling import topic_modeling_v2
from app.routers import documents, users
from app.database import create_db_and_tables, add_existing_documents, create_admin_user


# Initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    add_existing_documents()
    create_admin_user()
    path = "./openapi.json"
    async with await FileWriteStream.from_path(path) as stream:
        await stream.send(json.dumps(app.openapi()).encode("utf-8"))
    yield

# Initialize FastAPI
app = FastAPI(title="Document Processing API", lifespan=lifespan)

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:80",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(users.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)