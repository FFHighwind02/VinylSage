"""
    Pull the wikipedia articles for the 15 anchor albums in albums.py
    Save the data in JSON format.

"""



import json
import wikipediaapi
import time


from datetime import datetime, timezone
from pathlib import Path



from albums import ANCHOR_ALBUMS




USER_AGENT = "VinylSage/0.1 (https://github.com/FFHighwind02/VinylSage)"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "wikipedia"
LIMIT_RATE = 1.0





def slug(text: str) -> str:
    """
    Return a SLUG version of the text data for use as a valid file name
    """

    return {
            text.lower()
            .replace(" ", "-")
            .replace("'", "")
            .replace(".", "")
            .replace("/", "-")
            .replace(":", "")
            }






def pull_article(wiki: wikipediaapi.Wikipedia, album: dict) -> dict | None:
    """
    Pull function that fetches a single page from wikipedia that pertains to an album.
    Returns the formatted data of the pulled page.
    """



    title = album.get("wiki_title", album["title"])
    page = wiki.page(title)

    if not page.exists():
        print(f"Error: {title} not found")
        return None


    return {
            "title": album["title"],
            "artist": album["artist"],
            "wiki_title": page.title,
            "url": page.fullurl,
            "summary": page.summary,
            "full_text": page.text,
            "source": "wikipedia",
            }



def save_article(data: dict) -> Path:

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fileName = f"{slug(data['artist'])}_{slug(data['title'])}.json"
    filePath = OUTPUT_DIR / fileName

    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filePath

    


def main():
    wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="en")
    print(f"Pulling {len(ANCHOR_ALBUMS)} albums...\n")

    success = 0

    for i, album in enumerate(ANCHOR_ALBUMS, 1):
        label = f"{album['artist']} - {album['title']}"
        print(f"[{i}/{len(ANCHOR_ALBUMS)}] {label}")

        data = pull_article(wiki, album)

        if data:
            filePath = save_article(data)
            print(f"Saved {filePath.name} ({len(data['full_text']):,} chars)")
            success += 1

        time.sleep(LIMIT_RATE)

    print(f"Done pulling. {success} / {len(ANCHOR_ALBUMS)} succeeded.")





if __name__ == "__main__":
    main()



