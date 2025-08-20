from asyncio import (
    Semaphore,
    sleep,
    create_task,
    gather,
    run as asyncio_run,
)
import httpx
from typing import List, Dict, Optional
import json
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("museum_fetcher.log"),
    ],
)
logger = logging.getLogger(__name__)


class MetMuseumFetcher:
    """Fetches data from the Met Museum Collection API asynchronously."""

    def __init__(self, max_concurrent_requests: int = 50):
        self.base_url = (
            "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
        )
        self.max_concurrent_requests = max_concurrent_requests
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):

        limits = httpx.Limits(max_keepalive_connections=100, max_connections=100)
        timeout = httpx.Timeout(30.0, connect=10.0)

        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            headers={"User-Agent": "MuseumFetcher/1.0"},
            http2=True,
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.client:
            await self.client.aclose()

    async def fetch_all_objects(
        self, start_id: int = 1, end_id: int = None
    ) -> List[Dict]:
        """Fetches all objects from the Met Museum Collection API."""

        try:
            response = await self.client.get(
                "https://collectionapi.metmuseum.org/public/collection/v1/objects?departmentIds=11"
            )
            if response.status_code == 200:
                collection_data: dict = response.json()
                object_ids = collection_data.get("objectIDs", range(1, 101))

            else:
                print(f"Failed to fetch total objects: {response.status_code}")
                logger.warning(
                    f"Failed to fetch object IDs: HTTP {response.status_code}"
                )
                object_ids = collection_data.get("objectIDs", range(1, 101))
        except Exception as e:
            print(f"Error fetching total objects: {e}")
            logger.error(f"Exception fetching object IDs: {e}")
            object_ids = collection_data.get("objectIDs", range(1, 101))

        requests_per_second = 20
        semaphore = Semaphore(self.max_concurrent_requests)
        rate_limiter = Semaphore(0)
        print(len(object_ids))

        async def reset_rate_limiter():
            while True:
                await sleep(1)

                for _ in range(requests_per_second):
                    try:
                        rate_limiter.release()
                    except ValueError:
                        break

        reset_task = create_task(reset_rate_limiter())

        async def fetch_single(object_id: int) -> Optional[Dict]:
            print(f"Fetching object {object_id}")
            # async with rate_limiter:
            async with semaphore:
                try:
                    response = await self.client.get(f"{self.base_url}{object_id}")

                    if response.status_code != 200:
                        logger.warning(
                            f"Object {object_id}: HTTP {response.status_code}"
                        )
                        return None

                    obj_data = response.json()

                    if object_url := obj_data.get("objectURL"):
                        try:
                            # async with rate_limiter:
                            page_response = await self.client.get(object_url)

                            if page_response.status_code == 200:
                                soup = BeautifulSoup(page_response.text, "html.parser")

                                if gallery_span := soup.find(
                                    "span",
                                    class_="artwork__location--gallery",
                                ):
                                    if location_a := gallery_span.find("a"):
                                        gallery_link = location_a["href"]
                                        if gallery_link:
                                            obj_data["galleryLink"] = gallery_link
                                            logger.info(
                                                f"Object {object_id}: Gallery link found: {gallery_link}"
                                            )
                                            # return obj_data
                                        else:
                                            logger.info(
                                                f"Object {object_id}: Empty gallery link"
                                            )
                                    else:
                                        logger.info(
                                            f"Object {object_id}: location <a> tag not found"
                                        )

                                else:
                                    logger.info(
                                        f"Object {object_id}: Gallery span not found"
                                    )

                                if desc_div := soup.find(
                                    "div",
                                    class_="artwork__intro__desc js-artwork__intro__desc",
                                ):
                                    if desc_p := desc_div.find("p"):
                                        description = desc_p.get_text(strip=True)
                                        print(
                                            f"Found description for object {object_id}: {description}"
                                        )
                                        print("\n")
                                        if description:
                                            obj_data["itemDescription"] = description
                                            logger.info(
                                                f"Object {object_id}: Description found: {description}"
                                            )

                                            obj_data["galleryLink"] = (
                                                ""
                                                if "galleryLink" not in obj_data
                                                else obj_data["galleryLink"]
                                            )
                                            return obj_data
                                        else:
                                            logger.info(
                                                f"Object {object_id}: Empty description found"
                                            )
                                    else:
                                        logger.info(
                                            f"Object {object_id}: Description paragraph not found"
                                        )
                                else:
                                    logger.info(
                                        f"Object {object_id}: Description div not found"
                                    )

                                if gallery_span := soup.find(
                                    "span",
                                    class_="artwork__location--gallery",
                                ):
                                    if location_a := gallery_span.find("a"):
                                        gallery_link = location_a["href"]
                                        if gallery_link:
                                            obj_data["galleryLink"] = gallery_link
                                            logger.info(
                                                f"Object {object_id}: Gallery link found: {gallery_link}"
                                            )
                                            return obj_data
                                        else:
                                            logger.info(
                                                f"Object {object_id}: Empty gallery link"
                                            )
                                    else:
                                        logger.info(
                                            f"Object {object_id}: location <a> tag not found"
                                        )

                                else:
                                    logger.info(
                                        f"Object {object_id}: Gallery span not found"
                                    )

                            else:
                                logger.warning(
                                    f"Object {object_id}: Description page HTTP {page_response.status_code}"
                                )
                                return None

                        except httpx.RequestError as e:
                            print(
                                f"Error fetching description for object {object_id}: {e}"
                            )
                            pass
                    else:
                        logger.info(f"Object {object_id}: No objectURL found")
                        return None

                except httpx.RequestError as e:
                    print(f"Request error for object {object_id}: {e}")
                    return None
                except Exception as e:
                    print(f"Error fetching object {object_id}: {e}")
                    return None

        all_results = []

        batch_size = 25
        delay_between_batches = 60.0

        for i in range(0, len(object_ids), batch_size):
            batch = object_ids[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {batch}")

            tasks = [fetch_single(object_id) for object_id in batch]
            batch_results = await gather(*tasks)
            all_results.extend([obj for obj in batch_results if obj is not None])

            if i + batch_size < len(object_ids):
                logger.info(
                    f"Waiting {delay_between_batches} seconds before next batch"
                )
                await sleep(delay_between_batches)

        return all_results


async def main():
    async with MetMuseumFetcher(max_concurrent_requests=10) as fetcher:
        objects = await fetcher.fetch_all_objects(start_id=1, end_id=2000)

        with open("met_museum_objects_full_test.json", "w", encoding="utf-8") as f:
            json.dump(objects, f, indent=4)

        print(f"Fetched {len(objects)} objects")


if __name__ == "__main__":
    asyncio_run(main())
