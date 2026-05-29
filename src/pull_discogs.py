"""
    Fetch script for the Discogs api I want to integrate into VinylSage
    
    Searches the masters and releases to provide extra collector context to VinylSage
"""



import json
import time
from pathlib import Path


import requests
from dotenv import load_dotenv
import os


from albums import ANCHOR_ALBUMS


OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "discogs"
RATE_LIMIT_SECONDS = 1.0
DISCOGS_API = "https://api.discogs.com"




def get_headers() -> dict:

    return{"Authorization": f"Discogs token={os.getenv('DISCOGS_TOKEN')}",
           "User-Agent": os.getenv("DISCOGS_USER_AGENT"),
           }





def search_master(artist: str, title: str, year: int = None) -> dict | None:



    params = {
            "artist": artist,
            "release_date": title,
            "type": "master",
            "per_page": 10,
    }

    response = requests.get(
        f"{DISCOGS_API}/database/search",
        headers=get_headers(),
        params=params,
    )


    if response.status_code != 200:
        print(f"  Search error {response.status_code}: {response.text[:100]}")
        return None


    results = response.json().get("results", [])
    if not results:
        print(f"  No results found for {artist} - {title}")
        return None


    masters = [r for r in results if r.get("master_id")]
    if not masters:
        masters = results
    
    if year:
        def year_distance(r):
            try:
                return abs(int(r.get("year", 9999)) - year)
            except (ValueError, TypeError):
                return 9999
        masters = sorted(masters, key=year_distance)


    top = results[0]
    return {
        "master_id": top.get("master_id") or top.get("id"),
        "title": top.get("title"),
        "year": top.get("year"),
        "genre": top.get("genre", []),
        "style": top.get("style", []),
        "thumb": top.get("thumb"),
        "uri": top.get("uri"),
    }






def fetch_master_details(master_id: int) -> dict | None:
    """
    Fetch full master release details including main release info.
    """
    response = requests.get(
        f"{DISCOGS_API}/masters/{master_id}",
        headers=get_headers(),
    )

    if response.status_code != 200:
        print(f"  Master fetch error {response.status_code}")
        return None

    data = response.json()
    

    return {
        "master_id": master_id,
        "title": data.get("title"),
        "year": data.get("year"),
        "artists": [a.get("name") for a in data.get("artists", [])],
        "genres": data.get("genres", []),
        "styles": data.get("styles", []),
        "tracklist": [
            {
                "position": t.get("position"),
                "title": t.get("title"),
                "duration": t.get("duration"),
            }
            for t in data.get("tracklist", [])
        ],
        "lowest_price": data.get("lowest_price"),
        "num_for_sale": data.get("num_for_sale"),
        "main_release": data.get("main_release"),
    }





def fetch_pressings(master_id: int, max_pressings: int = 50) -> list[dict]:
    """
    Fetch all known pressings/variants for a master release.
    Returns list of pressing dicts sorted by year.
    """
    pressings = []
    page = 1

    while len(pressings) < max_pressings:
        response = requests.get(
            f"{DISCOGS_API}/masters/{master_id}/versions",
            headers=get_headers(),
            params={
                "per_page": 25,
                "page": page,
                "sort": "released",
                "sort_order": "asc",
            },
        )

        if response.status_code != 200:
            break

        data = response.json()
        versions = data.get("versions", [])
        if not versions:
            break

    
        for v in versions:
            pressings.append({
                "release_id": v.get("id"),
                "title": v.get("title"),
                "label": v.get("label"),
                "catalog_number": v.get("catno"),
                "country": v.get("country"),
                "year": v.get("released"),
                "format": v.get("format"),
                "major_formats": v.get("major_formats", []),
                "status": v.get("status"),
            })

        pagination = data.get("pagination", {})
        if page >= pagination.get("pages", 1):
            break

        page += 1
        time.sleep(RATE_LIMIT_SECONDS)

    return pressings





def slugify(text: str) -> str:
    """Convert string to safe filename component."""
    
    return (
        text.lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace(".", "")
        .replace("/", "-")
        .replace(":", "")
    )





def save_discogs_data(album: dict, data: dict) -> Path:
    """Save Discogs data as JSON."""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(album['artist'])}_{slugify(album['title'])}.json"

    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath




def process_album(album: dict) -> dict | None:
    artist = album["artist"]
    title = album["title"]

    # Step 1: Resolve master_id
    if album.get("discogs_master_id"):
        master_id = album["discogs_master_id"]
        print(f"  Using hardcoded master_id: {master_id}")
    else:
        print(f"  Searching: {artist} - {title}")
        search_result = search_master(artist, title, year=album.get("year"))
        if not search_result:
            return None
        master_id = search_result["master_id"]
        print(f"  Found master_id: {master_id}")

    time.sleep(RATE_LIMIT_SECONDS)

    # Step 2: Fetch master details — always needed regardless of how we got master_id
    master = fetch_master_details(master_id)
    if not master:
        return None
    time.sleep(RATE_LIMIT_SECONDS)

    # Step 3: Fetch pressings
    print(f"  Fetching pressings...")
    pressings = fetch_pressings(master_id)
    print(f"  Found {len(pressings)} pressings")

    # Step 4: Combine and return
    return {
        "album": title,
        "artist": artist,
        "source": "discogs",
        "master": master,
        "pressings": pressings,
        "pressing_count": len(pressings),
        "countries": sorted(set(
            p["country"] for p in pressings if p.get("country")
        )),
        "years_range": {
            "earliest": min(
                (p["year"] for p in pressings if p.get("year")),
                default=None,
            ),
            "latest": max(
                (p["year"] for p in pressings if p.get("year")),
                default=None,
            ),
        },
    }





def main():
    load_dotenv()

    print("*/" * 30)
    print("VinylSage Discogs Fetcher")
    print("*/" * 30)
    print(f"Fetching data for {len(ANCHOR_ALBUMS)} albums...\n")


    success = 0
    failed = []

    for i, album in enumerate(ANCHOR_ALBUMS, 1):
        
        label = f"{album['artist']} - {album['title']}"
        print(f"[{i}/{len(ANCHOR_ALBUMS)}] {label}")


        data = process_album(album)
        if data:
            filepath = save_discogs_data(album, data)
            print(f"  Saved {filepath.name} ({data['pressing_count']} pressings)\n")
            success += 1

        else:
            print(f"  Failed\n")
            failed.append(label)

        # Rate limit between albums
        time.sleep(RATE_LIMIT_SECONDS)

    print("=" * 60)
    print(f"Done. {success}/{len(ANCHOR_ALBUMS)} succeeded.")
    

    if failed:
        print("\nFailed:")
        for label in failed:
            print(f"  - {label}")






if __name__ == "__main__":
    main()


