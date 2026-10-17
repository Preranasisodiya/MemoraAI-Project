
from app.services.similarity_service import search_similar_chunks


MIN_SIMILARITY = 0.30


def build_context(
    db,
    query: str,
    user_id: int,
    top_k: int = 5,
    document_ids: list = None
):
    results = search_similar_chunks(
        db=db,
        query=query,
        user_id=user_id,
        top_k=top_k,
        document_ids=document_ids
    )

    if not results:
        return {
            "query": query,
            "context": "",
            "sources": []
        }

    relevant_results = [
        result
        for result in results
        if result.get("similarity", 0.0) >= MIN_SIMILARITY
    ]

    context_parts = []

    for result in relevant_results:
        context_parts.append(
            f"[Document: {result['filename']}]\n"
            f"{result['content']}"
        )

    context = "\n\n".join(context_parts)

    seen_files = set()
    sources = []

    for result in relevant_results:
        filename = result.get("filename")

        if filename and filename not in seen_files:
            seen_files.add(filename)
            sources.append({
                "filename": filename,
                "file_path": result.get("file_path", filename),
                "document_id": result.get("document_id"),
                "similarity": round(
                    float(result.get("similarity", 0.0)), 4
                )
            })

    return {
        "query": query,
        "context": context,
        "sources": sources
    }
