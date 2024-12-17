from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

# from app.TopicModeling import topic_modeling_v2
from app.routers import documents, users
from app.database import create_db_and_tables, add_existing_documents

# Initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    add_existing_documents()
    yield

# Initialize FastAPI
app = FastAPI(title="Document Processing API", lifespan=lifespan)

app.include_router(documents.router)
# app.include_router(users.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)