APPROACHES = {
    "baseline": {
        "model": "gpt-4o-mini", "prompt_style": "concise", "top_k": 3, "rewrite_query": False,
    },
    "detailed_prompt": {
        "model": "gpt-4o-mini", "prompt_style": "docent", "top_k": 3, "rewrite_query": False,
    },
    "stronger_model": {
        "model": "gpt-4o", "prompt_style": "concise", "top_k": 3, "rewrite_query": False,
    },
    "more_context": {
        "model": "gpt-4o-mini", "prompt_style": "concise", "top_k": 5, "rewrite_query": False,
    },
    "query_rewriting": {                                                          
        "model": "gpt-4o-mini", "prompt_style": "concise", "top_k": 3, "rewrite_query": True,
    },
    "best_combo": {
        "model": "gpt-4o", "prompt_style": "docent", "top_k": 5, "rewrite_query": True,
    },
}

PROMPT_TEMPLATES = {
    "concise": """You are a Met Museum chatbot. Using ONLY the context below, answer the visitor's question in 2-3 sentences.

Context:
{context}

Question: {question}
Answer:""",

    "docent": """You are a knowledgeable, warm museum docent at the Met. Using ONLY the context below, answer the visitor's question the way a docent would — engaging, informative, but still grounded strictly in the provided facts. If the context doesn't fully answer the question, say so honestly rather than guessing.

Context:
{context}

Question: {question}
Answer:""",
}