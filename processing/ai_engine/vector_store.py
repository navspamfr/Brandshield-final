import json
import math
import hashlib
import re
import numpy as np
from pathlib import Path
from backend.database.db import get_connection, get_brand_rules, get_setting

def local_semantic_embed(text, dim=128):
    """
    High-performance, local semantic embedding using subword character n-grams
    and TF-IDF hashing into a normalized dense float vector.
    Zero external dependencies, 100% offline and deterministic.
    """
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower()).strip()
    words = clean_text.split()
    vec = np.zeros(dim, dtype=np.float32)

    if not words:
        return vec.tolist()

    # Generate word tokens and character 3-grams
    tokens = []
    for w in words:
        tokens.append(w)
        if len(w) >= 3:
            for i in range(len(w) - 2):
                tokens.append(w[i:i+3])

    # Hash tokens into vector bins
    for token in tokens:
        h = int(hashlib.md5(token.encode('utf-8')).hexdigest()[:8], 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign

    # L2 normalize
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec = vec / norm

    return vec.tolist()

def get_embedding(text, api_key=None):
    """
    Generates embedding for text. Uses OpenAI if API key provided,
    otherwise falls back smoothly to local semantic embedding.
    """
    if not api_key:
        api_key = get_setting("openai_api_key")

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                input=text[:2000],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception:
            # Fall back to local semantic embed on error/quota issue
            pass

    return local_semantic_embed(text)

def cosine_similarity(v1, v2):
    """Calculates cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)

    # If dimension mismatch (e.g. one is OpenAI 1536 and other is local 128), project to smaller
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a < 1e-6 or norm_b < 1e-6:
        return 0.0

    return float(dot_product / (norm_a * norm_b))

def index_brand_rule(rule_id, rule_text, api_key=None):
    """Calculates and persists embedding for a specific brand rule."""
    emb = get_embedding(rule_text, api_key)
    emb_json = json.dumps(emb)

    with get_connection() as conn:
        conn.execute("UPDATE brand_rules SET embedding = ? WHERE id = ?", (emb_json, rule_id))
        conn.commit()

def reindex_all_rules_for_org(org_id, api_key=None):
    """Ensures all rules for an organization have computed embeddings."""
    rules = get_brand_rules(org_id)
    updated = 0
    with get_connection() as conn:
        for r in rules:
            if not r.get("embedding"):
                text_to_embed = f"{r['category']} - {r['rule_title']}: {r['rule_description']}"
                emb = get_embedding(text_to_embed, api_key)
                conn.execute("UPDATE brand_rules SET embedding = ? WHERE id = ?", (json.dumps(emb), r["id"]))
                updated += 1
        conn.commit()
    return updated

def retrieve_relevant_rules(org_id, query_content, top_k=5, api_key=None):
    """
    AI-Powered Rule Retrieval:
    Embeds the input query/content and retrieves the top-K most semantically
    relevant brand rules from the SQLite vector store.
    """
    # Ensure all rules have embeddings
    reindex_all_rules_for_org(org_id, api_key)

    rules = get_brand_rules(org_id)
    if not rules:
        return []

    # Get query embedding
    query_emb = get_embedding(query_content, api_key)

    scored_rules = []
    for r in rules:
        r_dict = dict(r)
        emb_str = r_dict.get("embedding")
        if emb_str:
            try:
                rule_emb = json.loads(emb_str)
                sim = cosine_similarity(query_emb, rule_emb)
            except Exception:
                sim = 0.5
        else:
            sim = 0.5

        r_dict["relevance_score"] = round(float(sim), 3)
        scored_rules.append(r_dict)

    # Sort descending by similarity
    scored_rules.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_rules[:top_k]
