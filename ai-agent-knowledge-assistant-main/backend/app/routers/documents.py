import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import Document, get_db
from app.rag import pipeline, vectorstore
from app.schemas import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    doc_id = uuid.uuid4().hex
    try:
        num_chunks, num_chars = pipeline.ingest_document(
            doc_id, file.filename or "untitled", file.content_type or "", raw
        )
    except Exception as exc:  # surface ingestion/LLM errors to the client
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {exc}")

    if num_chunks == 0:
        raise HTTPException(
            status_code=422, detail="Could not extract any text from this file"
        )

    doc = Document(
        id=doc_id,
        filename=file.filename or "untitled",
        content_type=file.content_type or "",
        num_chunks=num_chunks,
        num_chars=num_chars,
        status="ready",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    vectorstore.delete_document(document_id)
    db.delete(doc)
    db.commit()
    return {"deleted": document_id}
