from app.services.similarity_service import search_similar_chunks


def build_context(db, query: str, user_id: int, top_k: int = 5):
    results = search_similar_chunks(
        db=db,
        query=query,
        user_id=user_id,
        top_k=top_k
    )

    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"[Source {index}]\n"
            f"Filename: {result['filename']}\n"
            f"Similarity: {result['similarity']:.4f}\n"
            f"Content:\n{result['content']}"
        )

    context = "\n\n".join(context_parts)

    return {
        "query": query,
        "context": context,
        "sources": [
            {
                "filename": result["filename"],
                "similarity": result["similarity"],
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "content": result["content"],
            }
            for result in results
        ],
    }