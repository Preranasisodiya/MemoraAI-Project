import os
from pathlib import Path
from app.database.database import SessionLocal
import app.models
from app.models.document import Document
from app.models.conversation import ChatMessage
from sqlalchemy.orm.attributes import flag_modified

def migrate_document_names():
    db = SessionLocal()
    try:
        # 1. Build a lookup of file_hash -> (filename, title, file_path) from known records or physical files
        # Check User 2 documents (which were scanned directly from D:\MemoraAI_Knowledge)
        known_map = {}
        for doc in db.query(Document).filter(Document.user_id == 2).all():
            if doc.file_hash:
                # Calculate relative path if under D:\MemoraAI_Knowledge
                fp = doc.file_path
                prefix = "D:\\MemoraAI_Knowledge\\"
                if fp.startswith(prefix):
                    rel = fp[len(prefix):].replace("\\", "/")
                else:
                    rel = Path(fp).name
                known_map[doc.file_hash] = {
                    "filename": rel,
                    "title": doc.title or Path(rel).stem,
                    "file_path": fp
                }

        print(f"Loaded {len(known_map)} known document hashes.")

        # 2. Update documents that have hash names
        all_docs = db.query(Document).all()
        updated_docs = 0

        for doc in all_docs:
            # Check if filename is a hash (e.g. len >= 64 and matches file_hash)
            is_hash_name = bool(
                doc.file_hash 
                and (doc.filename.startswith(doc.file_hash[:20]) or len(Path(doc.filename).stem) == 64)
            )


            if doc.file_hash in known_map:
                info = known_map[doc.file_hash]
                doc.filename = info["filename"]
                doc.title = info["title"]
                doc.file_path = info["file_path"]
                updated_docs += 1
            elif is_hash_name and doc.file_path and not Path(doc.file_path).name.startswith(doc.file_hash[:20]):
                # Fallback to file_path name if different from hash
                p = Path(doc.file_path)
                doc.filename = p.name
                doc.title = p.stem
                updated_docs += 1

        db.commit()
        print(f"Updated {updated_docs} documents with original names and paths.")

        # 3. Update any ChatMessage sources that contained hash filenames
        updated_msgs = 0
        messages = db.query(ChatMessage).filter(ChatMessage.sources.isnot(None)).all()
        for msg in messages:
            if not msg.sources:
                continue
            new_sources = []
            changed = False
            for s in msg.sources:
                doc_id = s.get("document_id")
                old_fn = s.get("filename", "")
                if doc_id:
                    matched_doc = db.query(Document).filter(Document.id == doc_id).first()
                    if matched_doc and matched_doc.filename != old_fn:
                        s["filename"] = matched_doc.filename
                        s["file_path"] = matched_doc.file_path
                        changed = True
                new_sources.append(s)

            if changed:
                msg.sources = new_sources
                flag_modified(msg, "sources")
                updated_msgs += 1


        db.commit()
        print(f"Updated {updated_msgs} chat messages with clean source names.")


    finally:
        db.close()

if __name__ == "__main__":
    migrate_document_names()
