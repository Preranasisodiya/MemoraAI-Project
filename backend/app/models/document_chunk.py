from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship(
        "Document",
        back_populates="chunks"
    )