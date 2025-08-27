from qdrant_client import QdrantClient, models
from pathlib import Path
import json
from typing import Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def prepare_painting_description(painting_obj: Dict) -> Dict:
    """Prepare formatted description of painting from museum data object list for ingestion into vector database"""

    painting_data = painting_obj

    intro_statement = f"{painting_data.get('title', '')} by {painting_data.get('artistDisplayName')}"
    artist_bio = f"{painting_data.get('artistDisplayName')} is {painting_data.get('artistNationality')}, their bio is: '{painting_data.get('artistDisplayBio')}'. {painting_data.get('artistDisplayName')} lived from {painting_data.get('artistBeginDate')} to {painting_data.get('artistEndDate')}"
    
    artwork_origin = f"The source/origin of the artwork is {painting_data.get('creditLine')[:-7]}, the Metropolitan Museum of Art acquired the artwork in {painting_data.get('creditLine')[-4:]}"

    medium_dimensions = f"The medium for the painting is {painting_data.get('medium', 'canvas')}, and the dimensions are {painting_data.get('dimensions', 'unknown')}"

    gallery_location = f"The artwork is presented at gallery {painting_data.get("GalleryNumber")}, located on the map here {painting_data.get("galleryLink")}" if painting_data.get("GalleryNumber") != ""  else "The artwork is currently not showcased at the museum"

    artwork_description = f"The description of the artwork is: '{painting_data.get("itemDescription")}'"

    #tags
    tags_lst = []
    tags_text = ""
    try:
        if len(painting_data.get("tags")) > 0:
            for tag in painting_data.get("tags"):
                try:
                    tags_lst.append(tag['term'])
                except:
                    continue
            tags_text = f"The following tags are related to {painting_data.get('title', '')} : {tags_lst}"
        else:
            tags_text = ""
    except:
        tags_text = ""

    #artists
    artist_lst = []
    artist_text = ""
    try:
        if len(painting_data.get("constituents")) > 0:
            for constituent in painting_data.get("constituents"):
                try:
                    artist_lst.append(constituent['name'])
                except:
                    continue
            artist_text = f"The following artists are related to {painting_data.get('title', '')} : {artist_lst}"
        else:
            artist_text = ""
    except:
        artist_text = ""

    #painting work
    painting_work_duration = ""
    if painting_data.get('objectBeginDate', 0) == painting_data.get('objectEndDate', 0):
        painting_work_duration = f"The painting was started and completed in {painting_data.get('objectBeginDate', 0)}"
    else:
        painting_work_duration = f"The painting was started in {painting_data.get('objectBeginDate', 0)} and completed in {painting_data.get('objectEndDate', 0)}"

    public_importance = f"and {'is' if painting_data.get('isHighlight') == False else 'is not'} a popular and important artwork in {painting_data.get('artistDisplayName')}'s collection, {'and is currently in the public domain' if painting_data.get('isHighlight') == False else 'is not currently in the public domain'}"

    text = f"""
    {intro_statement}. {artwork_description}. {artwork_origin}. {medium_dimensions}. {gallery_location}. {artist_bio}. {painting_work_duration}, {public_importance}. {artist_text}. {tags_text}.
    """.strip()

    data_dict = {
        'artwork_id': painting_data.get('objectID'),
        'artwork_text': text,
        'primary_image_url': painting_data.get('primaryImage', ''),
        'artist_bio_url': painting_data.get('artistWikidata_URL', ''),
        'artwork_url': painting_data.get('objectURL', '')
    }

    return data_dict 

logger.info("Ingesting musuems object json file.")
json_path = Path('src/met_museum_objects_full.json')
with open(json_path) as f:
    data = json.load(f)


artwork_obj_lst = []


logger.info("Generating parsed museum artwork knowledge base.")
for obj in data:
    try:
        artwork_obj = prepare_painting_description(obj)
        artwork_obj_lst.append(artwork_obj)
    except:
        print(artwork_obj)


client = QdrantClient("http://localhost:6333")
client.get_collections()


client.create_collection(
    collection_name="met-museum-euro-artworks",
    vectors_config={
        "jina-small": models.VectorParams(
            size=512,
            distance=models.Distance.COSINE
        ),
    },
    sparse_vectors_config={
        "bm25": models.SparseVectorParams(
            modifier=models.Modifier.IDF,
        )
    }
)


logger.info("Upserting museum artwork knowledge base into qdrant vector database.")
client.upsert(
    collection_name="met-museum-euro-artworks",
    points = [
        models.PointStruct(
            id=artwork_obj['artwork_id'],
            vector = {
                "jina-small": models.Document(
                    text = artwork_obj['artwork_text'],
                    model="jinaai/jina-embeddings-v2-small-en"
                ),
                "bm25": models.Document(
                    text=artwork_obj['artwork_text'],
                    model="Qdrant/bm25"

                )
            },
            payload={
                "artwork_text": artwork_obj['artwork_text'],
                'artwork_image_url': artwork_obj['primary_image_url'],
                'artist_url': artwork_obj['artist_bio_url'],
                'artwork_bio_url': artwork_obj['artwork_url']
                    }
        )
     for artwork_obj in artwork_obj_lst
    ] 
)

logger.info('Ingestion of museum artwork knowledge base into vector database complete!')