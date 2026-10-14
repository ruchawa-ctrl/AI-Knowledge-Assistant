import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import ChatMessage, SessionLocal, get_db
from app.rag import pipeline
from app.schemas import ChatRequest, ChatResponse, MessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history", response_model=list[MessageOut])
def history(db: Session = Depends(get_db)):
    rows = db.query(ChatMessage).order_by(ChatMessage.created_at.asc()).all()
    out = []
    for r in rows:
        out.append(
            MessageOut(
                id=r.id,
                role=r.role,
                content=r.content,
                sources=json.loads(r.sources) if r.sources else [],
                created_at=r.created_at,
            )
        )
    return out


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db.add(ChatMessage(role="user", content=question))
    db.commit()

    try:
        result = pipeline.answer_question(question, req.top_k)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Query failed: {exc}")

    db.add(
        ChatMessage(
            role="assistant",
            content=result["answer"],
            sources=json.dumps(result["sources"]),
        )
    )
    db.commit()
    return result


@router.post("/stream")
def chat_stream(req: ChatRequest):
    question = req.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    with SessionLocal() as db:
        db.add(ChatMessage(role="user", content=question))
        db.commit()

    def event_stream():
        try:
            context_blocks, sources = pipeline.retrieve_sources(question, req.top_k)
        except Exception as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"
            return

        yield json.dumps({"type": "sources", "sources": sources}) + "\n"

        collected: list[str] = []
        try:
            for token in pipeline.stream_answer(question, context_blocks):
                collected.append(token)
                yield json.dumps({"type": "token", "text": token}) + "\n"
        except Exception as exc:
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"
            return

        answer = "".join(collected)
        with SessionLocal() as db:
            db.add(
                ChatMessage(
                    role="assistant",
                    content=answer,
                    sources=json.dumps(sources),
                )
            )
            db.commit()
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    db.query(ChatMessage).delete()
    db.commit()
    return {"cleared": True}
