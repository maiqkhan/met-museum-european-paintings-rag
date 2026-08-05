from typing import List
import json, random
from pydantic import BaseModel
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

from openai import OpenAI

def get_all_points(client) -> List:
    """
    Retrieve all points at once. Only use for small collections (<10k points).
    
    Returns:
        List of all point records
    """
    all_points = []
    offset = None
    
    while True:
        records, next_offset = client.scroll(
            collection_name=collection_name,
            #limit=10,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        all_points.extend(records)
        
        if next_offset is None:
            break
        
        offset = next_offset    
    return all_points

openai_client = OpenAI()

client = QdrantClient("http://localhost:6333")
collection_name = "met-museum-euro-artworks"

painting_objects = get_all_points(client)

painting_description_lst = []

for painting_obj in painting_objects:
    painting_description_lst.append({"id": painting_obj.id , "artwork_dense_embedding": painting_obj.payload['artwork_dense_embedding']}) 

def validate_queries(queries: List[str], title_and_artist: str, description: str) -> List[str]:
    valid_queries = []

    for q in queries:
        # tests for valid queries
        if len(q.split()) < 5:
            continue

        if title_and_artist.lower() in q.lower():
            continue

        # simple query overlap
        desc_words = set(description.lower().split())
        query_words = set(q.lower().split())

        overlap = len(desc_words & query_words) / len(query_words)
        if overlap > 0.7:
            continue

        valid_queries.append(q)

    return valid_queries

class QueryResponse(BaseModel):
    queries: List[str]

def generate_ground_truth_questions(num_queries: int,  dense_embedding_text: str) -> List[str]:
    title_artist = dense_embedding_text.split('Medium: ')[0]

    prompt = f"""You are an expert in creating RAG evaluation datasets for museum chatbots. Your task is to generate EXACTLY {num_queries} realistic, diverse user queries that should retrieve information about this specific painting — and ONLY this painting.

        Given this painting information (this is the exact text available to the retrieval system):
        Title and Artist: {title_artist if title_artist else "Not provided"}
        Full indexed content: {dense_embedding_text}

        CONTEXT: These queries will be used to evaluate a RAG system for a Met Museum chatbot. Each query will be scored as correct ONLY if this specific painting is retrieved — not a similar or related one. This means every query, regardless of category, MUST include at least one detail specific enough to distinguish this painting from other similar works in the collection (e.g. a specific visual detail, an unusual combination of subject + style + medium, or a distinctive compositional element) — never rely solely on broad category membership (e.g. artist name, movement, period, or medium alone), since those could equally match many other paintings.

        GENERATE {num_queries} QUERIES WITH THE FOLLOWING DISTRIBUTION:

        1. SPECIFIC ARTWORK QUERIES (35%): Direct questions about this painting using 2-3 specific visual elements from the description
        - Use partial information (no exact title/artist)
        - Example: "painting with water lilies and Japanese bridge"
        - Difficulty: Easy-Medium

        2. THEMATIC QUERIES (25%): Broader themes that should include this painting, ANCHORED by a distinguishing visual or narrative detail
        - Focus on subject matter, symbolism, or narrative — but combined with something specific enough that this painting is the clear best match
        - Example: "mythology painting where a figure is disguised as a swan" (not just "mythology painting")
        - Difficulty: Medium

        3. COMPARATIVE QUERIES (15%): Reference similar works, movements, or styles, ANCHORED by a specific subject or compositional detail
        - Require understanding of art history context, but must include a concrete detail unique to this piece
        - Example: "Caravaggio-style dramatic lighting on a fortune-telling scene" (not just "Caravaggio's style")
        - Difficulty: Medium-Hard

        4. NAVIGATIONAL QUERIES (15%): Time period, culture, medium, or department-specific, ANCHORED by a specific subject detail
        - Example: "17th century Dutch painting of a woman reading a letter by a window" (not just "17th century Dutch paintings")
        - Difficulty: Easy-Medium

        5. EXPLORATORY QUERIES (10%): Mood or color palette, ANCHORED by a specific visual element
        - Example: "a tense, shadowy painting of two men in a dispute over cards" (not just "paintings that feel tense")
        - Difficulty: Medium-Hard

        CRITICAL REQUIREMENTS:

        A. UNIQUENESS RULE (most important): Before finalizing each query, verify it could not equally describe a different painting by a different artist from a similar period/genre. If a query only mentions genre + mood + period with no distinguishing subject detail, add one.

        B. DIFFICULTY CALIBRATION:
        - Easy: Direct visual elements, clear subjects (30% of queries)
        - Medium: Requires semantic understanding or context (50% of queries)
        - Hard: Abstract concepts, multi-hop reasoning, or ambiguous phrasing (20% of queries)

        C. LINGUISTIC DIVERSITY:
        - Vary formality: questions vs. statements vs. keywords
        - Mix specificity: vague → precise
        - Different query lengths: 5-25 words
        - Include natural language variations ("show me", "looking for", "are there any")

        D. EDGE CASES TO INCLUDE (at least 2):
        - Misspellings or informal terms
        - Temporally ambiguous ("Renaissance" vs "1500s")
        - Under-specified queries that still include one distinguishing detail
        - Partial/incomplete descriptions ('that pinting with the blue..')

        E. REALISM PRINCIPLES:
        - Use vocabulary real visitors use (not art historian jargon unless for Hard queries)
        - Include implicit intent ("I want to see..." vs "retrieve documents about...")
        - Add conversational markers occasionally ("I'm interested in...", "Can you help me find...")
        - NO exact title or artist name unless it's a common search pattern

        AVOID:
        - Generic queries that would retrieve 100+ paintings ("famous paintings")
        - Queries relying only on artist/period/movement with no distinguishing subject detail
        - Queries that mention the exact title
        - Queries that only an art expert would ask
        - Repetitive phrasings
        - Overly SEO-like keyword stuffing

        Return ONLY a parsable JSON without using code blocks. Format:
        ["query 1", "query 2", ... "query {num_queries}"]
""".strip()

    response = openai_client.chat.completions.parse(
        model='gpt-4o',
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        response_format=QueryResponse
    )

    queries = json.loads(response.choices[0].message.content)
    valid_queries = validate_queries(queries=queries['queries'], title_and_artist=title_artist, description=dense_embedding_text)

    return valid_queries

random_indexes = random.sample(range(len(painting_description_lst)), 100)

ground_truth_lst = []

for painting in [painting_description_lst[i] for i in random_indexes]:
    print(painting.keys())    
    print(painting['id'])
    query_lst_of_dicts = [{'id': painting['id'],'question': q} for q in generate_ground_truth_questions(5, painting['artwork_dense_embedding'])]

    ground_truth_lst.extend(query_lst_of_dicts)

import csv 

with open('retrieval_evaluation/ground_truth.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'question'])
    writer.writeheader()
    writer.writerows(ground_truth_lst)