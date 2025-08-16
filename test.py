import _asyncio
import httpx
from typing import List, Dict, Optional


class MetMuseumFetcher:
    """Fetches data from the Met Museum Collection API asynchronously."""

    def __init__(
        self, max_concurrent_requests: int = 50, delay_between_batches: float = 1.0
    ):
        self.base_url = (
            "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
        )
        self.max_concurrent_requests = max_concurrent_requests
        self.delay_between_batches = delay_between_batches
        self.client = Optional[httpx.AsyncClient] = None
        self.results: List[Dict] = []
