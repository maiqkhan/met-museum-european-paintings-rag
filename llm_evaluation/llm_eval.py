
from openai import OpenAI

from eval_approaches_dict import PROMPT_TEMPLATES
from retrieval_evaluation.retrieval_methods import weighted_fusion_search

openai_client = OpenAI()

def rewrite_query(question: str) -> str:
    prompt = f"""Rewrite this museum visitor's search query 
                    to be clearer and more specific for a retrieval system, 
                    while preserving their original intent. 
                    Expand vague or thematic language into more concrete terms where possible. 
                    Return ONLY the rewritten query, nothing else.

                    Original query: {question}
                    Rewritten query: """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=60,
    )
    return response.choices[0].message.content.strip()


def generate_answer(question: str, approach: dict, retrieval_fn=weighted_fusion_search) -> dict:
    search_query = rewrite_query(question) if approach.get("rewrite_query") else question

    points = retrieval_fn(search_query, approach["top_k"])
    contexts = [p.payload.get("artwork_text", "") for p in points]
    context_str = "\n\n---\n\n".join(contexts)

    prompt = PROMPT_TEMPLATES[approach["prompt_style"]].format(
        context=context_str, question=question   # note: use ORIGINAL question in the prompt, not rewritten
    )

    response = openai_client.chat.completions.create(
        model=approach["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return {
        "question": question,
        "search_query_used": search_query,
        "answer": response.choices[0].message.content,
        "contexts": contexts,
        "retrieved_ids": [p.id for p in points],
    }

