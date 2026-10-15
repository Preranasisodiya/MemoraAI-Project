from app.services.similarity_service import search_similar_chunks


def build_context(db, query: str, user_id: int, top_k: int = 5, document_ids: list = None):
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

    # Filter out results with very low similarity if needed, or take the top relevant chunks
    relevant_results = [r for r in results if r.get("similarity", 0) > 0.15]
    if not relevant_results and results:
        # If all are low, keep at least the top one if similarity > 0.05
        if results[0].get("similarity", 0) > 0.05:
            relevant_results = results[:2]

    context_parts = []
    for index, result in enumerate(relevant_results, start=1):
        context_parts.append(
            f"[Document: {result['filename']}]\n"
            f"{result['content']}"
        )

    context = "\n\n".join(context_parts)

    # Return clean, user-safe source references without exposing internal chunks or raw embeddings
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
                "similarity": round(float(result.get("similarity", 0.0)), 4)
            })



    return {
        "query": query,
        "context": context,
        "sources": sources
    }