
from qdrant_client import models, QdrantClient
from sentence_transformers import CrossEncoder


client = QdrantClient("http://localhost:6333")
client.get_collections()

def dense_only_search(query: str, limit: int = 520) -> list[models.ScoredPoint]:
    results = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(
            text=query,
            model="jinaai/jina-embeddings-v2-small-en",
        ),
        using="jina-small",
        limit=limit,
        with_payload=True,
    )
    return results.points


def bm25_only_search(query: str, limit: int = 50) -> list[models.ScoredPoint]:
    results = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(
            text=query,
            model="Qdrant/bm25",
        ),
        using="bm25",
        limit=limit,
        with_payload=True,
    )
    return results.points


def hybrid_rrf_search(query: str, limit: int = 20) -> list[models.ScoredPoint]:
    results = client.query_points(
        collection_name="met-museum-euro-artworks",
        prefetch=[
            models.Prefetch(
                query=models.Document(text=query, model="jinaai/jina-embeddings-v2-small-en"),
                using="jina-small",
                limit=100 * limit,
            ),
            models.Prefetch(
                query=models.Document(text=query, model="Qdrant/bm25"),
                using="bm25",
                limit=100 * limit,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return results.points

def multi_stage_search(query: str, limit: int = 5) -> list[models.ScoredPoint]:
    results = client.query_points(
        collection_name="met-museum-euro-artworks",
        prefetch=[
            models.Prefetch(
                query=models.Document(
                    text=query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                # Prefetch ten times more results, then
                # expected to return, so we can really rerank
                limit=(100 * limit),
            ),
        ],
        query=models.Document(
            text=query,
            model="jinaai/jina-embeddings-v2-small-en", 
        ),
        using="jina-small",
        limit=limit,
        with_payload=True,
    )

    return results.points

def bm25_recall_then_dense_rerank(query: str, limit: int = 5) -> list[models.ScoredPoint]:
    # Stage 1: sparse recall — get a wide candidate pool
    candidates = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(text=query, model="Qdrant/bm25"),
        using="bm25",
        limit=100 * limit,
        with_payload=False,
    ).points

    candidate_ids = [c.id for c in candidates]
    if not candidate_ids:
        return []

    # Stage 2: dense rerank — restricted to just those candidate ids
    reranked = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(text=query, model="jinaai/jina-embeddings-v2-small-en"),
        using="jina-small",
        query_filter=models.Filter(
            must=[models.HasIdCondition(has_id=candidate_ids)]
        ),
        limit=limit,
        with_payload=True,
    )

    return reranked.points


def weighted_fusion_search(query: str, limit: int = 5, bm25_weight: float = 0.7) -> list[models.ScoredPoint]:
    pool_size = 50 * limit

    bm25_results = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(text=query, model="Qdrant/bm25"),
        using="bm25",
        limit=pool_size,
        with_payload=True,
    ).points

    dense_results = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(text=query, model="jinaai/jina-embeddings-v2-small-en"),
        using="jina-small",
        limit=pool_size,
        with_payload=True,
    ).points

    def normalize(points):
        if not points:
            return {}
        scores = [p.score for p in points]
        lo, hi = min(scores), max(scores)
        span = (hi - lo) or 1.0
        return {p.id: (p.score - lo) / span for p in points}

    bm25_norm = normalize(bm25_results)
    dense_norm = normalize(dense_results)

    all_ids = set(bm25_norm) | set(dense_norm)
    payload_lookup = {p.id: p.payload for p in bm25_results + dense_results}

    combined = []
    for pid in all_ids:
        score = bm25_weight * bm25_norm.get(pid, 0.0) + (1 - bm25_weight) * dense_norm.get(pid, 0.0)
        combined.append(
            models.ScoredPoint(id=pid, version=0, score=score, payload=payload_lookup.get(pid))
        )

    combined.sort(key=lambda p: p.score, reverse=True)
    return combined[:limit]

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def cross_encoder_rerank_search(query: str, limit: int = 5) -> list[models.ScoredPoint]:
    pool_size = 15 * limit

    candidates = client.query_points(
        collection_name="met-museum-euro-artworks",
        query=models.Document(text=query, model="Qdrant/bm25"),
        using="bm25",
        limit=pool_size,
        with_payload=True,
    ).points

    if not candidates:
        return []

    pairs = [(query, c.payload.get("artwork_text", "")[:600]) for c in candidates]
    scores = cross_encoder.predict(pairs, batch_size=64, show_progress_bar=False)

    for c, s in zip(candidates, scores):
        c.score = float(s)

    candidates.sort(key=lambda p: p.score, reverse=True)
    return candidates[:limit]