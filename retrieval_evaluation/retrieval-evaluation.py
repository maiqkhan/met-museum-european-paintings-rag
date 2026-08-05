import pandas as pd
from typing import List, Dict, Callable
from qdrant_client import models, QdrantClient

from retrieval_methods import multi_stage_search, dense_only_search, bm25_only_search, hybrid_rrf_search, bm25_recall_then_dense_rerank, cross_encoder_rerank_search, weighted_fusion_search

client = QdrantClient("http://localhost:6333")
client.get_collections()

class Retrieval_Metrics:
    def __init__(self, ground_truth_lst: List[Dict], retrieval_function: Callable[[str, int], List[models.ScoredPoint]], k: int):

        self.retrieval_function = retrieval_function
        self.ground_truth_lst = ground_truth_lst
        self.k = k

    def hit_rate_at_k(self, retrieved_points: List[models.ScoredPoint], k: int, question_id: int):
        k = k or self.k 

        top_k_retrieved_ids = {point.id for point in retrieved_points[:k]}
        return 1.0 if question_id in top_k_retrieved_ids else 0.0
    
    def mean_reciprocal_rank(self, retrieved_points: List[models.ScoredPoint], question_id: int):

        for rank, point in enumerate(retrieved_points, start=1):
            if question_id == point.id:
                return 1.0 / rank 
            
        return 0.0
    
    def evaluate(self) -> Dict[str, float]:
        hit_rates = []
        mrrs = []

        for item in self.ground_truth_lst:
            query = item['question']
            q_id = item['id']

            retrieved_points = self.retrieval_function(query, self.k)

            hit_rates.append(self.hit_rate_at_k(retrieved_points, self.k, q_id))
            mrrs.append(self.mean_reciprocal_rank(retrieved_points, q_id))

        n = len(hit_rates)
        if n == 0:
            return {
                f'hit_rate@{self.k}': 0.0,
                'mrr': 0.0,
                'num_queries': 0
            }
        else:
            return {
                f'hit_rate@{self.k}': sum(hit_rates) / n,
                'mrr': sum(mrrs) / n,
                'num_queries': n
            }



ground_truth_df = pd.read_csv('retrieval_evaluation/ground_truth_v2.csv')
ground_truth_dict = ground_truth_df.to_dict(orient='records')

methods = {
    "dense_only": dense_only_search,
    "bm25_only": bm25_only_search,
    "hybrid_rrf": hybrid_rrf_search,
    "dense_prefetch_bm25_rerank": multi_stage_search,
    "bm25_recall_then_dense_rerank": bm25_recall_then_dense_rerank,
    "weighted_fusion": weighted_fusion_search,
    #"cross_encoder_rank": cross_encoder_rerank_search
}

results = {}
for name, fn in methods.items():
    evaluator = Retrieval_Metrics(ground_truth_dict, fn, k=5)
    results[name] = evaluator.evaluate()

comparison_df = pd.DataFrame(results).T
print(comparison_df)