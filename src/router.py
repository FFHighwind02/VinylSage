"""
    Router script for selecting the data source, based on query type for VinylSage

    Decides whether a query should be handled by:
        - Discogs lookup (factual pressing/label/catalog questions)
        - RAG retrieval (open-ended, analytical, historical questions)

    Author: Nicholas Kennedy
    05/19/26
"""




import re

from llama_index.llms.google_genai import GoogleGenAI
import os



# Keywords that signal a Discogs query
PRESSING_KEYWORDS = [
    "pressing",
    "pressings",
    "pressing",
    "first pressing",
    "original pressing",
    "uk pressing",
    "us pressing",
    "german pressing",
    "japanese pressing",
    "label",
    "catalog number",
    "catalogue number",
    "catno",
    "vinyl",
    "reissue",
    "repress",
    "release",
    "releases",
    "versions",
    "variants",
    "country",
    "format",
    "rl",
    "rhino",
    "promo",
    "audiophile",
    "180g",
    "180 gram",
    "mint",
    "near mint",
    "how many pressings",
    "what label",
    "which label",
    "when was it released",
    "first released",
    "original release",
]




def classify_query(query: str) -> str:

    llm = GoogleGenAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    prompt = """Classify this music query into exactly one category:

            'discogs' - questions about: pressings, releases, labels, catalog numbers,
                    countries of manufacture, reissues, vinyl formats, release years,
                    how many versions exist, specific release variants

            'rag' - questions about: music history, artistic significance, production style,
                    critical reception, influences, songwriting, band history, comparisons,
                    recommendations, analysis, evolution of an artist

            Query: "{query}"

            Respond with exactly one word: discogs or rag""".format(query=query)

    response = llm.complete(prompt)
    result = str(response).strip().lower()

    # Fallback to rag if response is unexpected
    return "discogs" if "discogs" in result else "rag"




def extract_album_from_query(query: str, albums: list[dict]) -> dict | None:
    """
    Try to identify which album a query is about by matching
    album titles and artist names against the query text.

    Returns the matching album dict or None if no match.
    """
    query_lower = query.lower()


    # Try to match album titles first (more specific)
    for album in albums:

        title_lower = album["title"].lower()
        
        artist_lower = album["artist"].lower()

        # Check title words (skip very short words)
        title_words = [w for w in title_lower.split() if len(w) > 3]
        
        if any(word in query_lower for word in title_words):
            return album

        # Check artist name
        artist_words = [w for w in artist_lower.split() if len(w) > 3]
        
        if any(word in query_lower for word in artist_words):
            return album

    return None








