from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import ChatbotResponse, ChatbotRequest
from app.models import User
from app.utils.security import get_current_user
from app.utils.ai_model import (
    generate_embedding_for_texts,
    answer_question_with_context,
)
from app.database.documents import get_similar_chunks_by_embedding

router = APIRouter()

@router.post(
    "/chatbot/ask",
    response_model=ChatbotResponse,
    status_code=200,
    tags=["Chatbot"],
)
async def answer_question_rag(
    params: ChatbotRequest,
    _: User = Depends(get_current_user),
):
    """Answer a question using RAG"""
    question = params.question
    conversation_history = params.conversation_history
    try:
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        question_embedding = generate_embedding_for_texts([question])
        if not question_embedding or len(question_embedding) == 0:
            raise HTTPException(
                status_code=500, detail="Failed to generate question embedding"
            )

        context_chunks = get_similar_chunks_by_embedding(question_embedding[0])
        if not context_chunks:
            raise HTTPException(status_code=404, detail="No relevant documents found")

        answer = answer_question_with_context(
            question=question,
            context=[chunk.text for chunk in context_chunks],
            history=conversation_history,
        )

        return {
            "answer": answer,
            "sources": list(
                dict.fromkeys([chunk.document.filename for chunk in context_chunks])
            ),
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Error 500 - Answering question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
