from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse

from app.schemas import ChatbotResponse, ChatbotRequest
from app.models import User
from app.utils.security import get_current_user
from app.utils.ai_model import (
    generate_embedding_for_texts,
    answer_question_with_context,
)
from app.utils.background_tasks_manager import (
    create_task,
    update_task,
    fail_task,
    get_task,
    remove_task,
)
from app.database.documents import get_similar_chunks_by_embedding

router = APIRouter()


@router.post(
    "/chatbot/ask",
    status_code=200,
    tags=["Chatbot"],
)
async def answer_question_rag(
    params: ChatbotRequest,
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_user),
):
    try:
        question = params.question
        history = params.conversation_history

        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        task_id = create_task()
        background_tasks.add_task(run_rag_task, question, history, task_id)
        return {"task_id": task_id}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Answer chatbot question : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get("/chatbot/answer/{task_id}", response_model=ChatbotResponse)
def get_answer(task_id: str):
    try:
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] == "pending":
            return JSONResponse(
                status_code=202,
                content={
                    "status": "pending",
                },
            )

        if task["status"] == "error":
            raise HTTPException(status_code=500, detail=task["error"])

        if task["status"] == "done":
            remove_task(task_id)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "done",
                    "answer": task["answer"],
                    "sources": task["sources"],
                },
            )

        raise HTTPException(status_code=500, detail="Unknown task status")
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Get chatbot answer status : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

def run_rag_task(question: str, history: list, task_id: str):
    try:
        question_embedding = generate_embedding_for_texts([question])
        chunks = get_similar_chunks_by_embedding(question_embedding[0])
        if not chunks:
            raise ValueError("No relevant chunks")

        answer = answer_question_with_context(
            question=question,
            context=[c.text for c in chunks],
            history=history,
        )
        sources = list(dict.fromkeys([c.document.filename for c in chunks]))
        update_task(task_id, answer, sources)
    except Exception as e:
        fail_task(task_id, str(e))
