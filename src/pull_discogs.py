"""
    Fetch script for the Discogs api I want to integrate into VinylSage
    
    Searches the masters and releases to provide extra collector context to VinylSage


    Author: Nicholas Kennedy
    05/19/26
"""



import json
import time
from pathlib import Path


import requests
from dotenv import load_dotenv
import os


from albums import ANCHOR_ALBUMS


OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "discogs"
RATE_LIMIT = 1.0
DISCOGS_API - "https://api.discogs.com"




def get_headers() -> dict:

    return{"Authorization": f"Discogs token={os.getenv('DISCOGS_TOKEN')}",
           "User-Agent": os.getenv("DISCOGS_USER_AGENT"),
           }





def search_masters(artist: str, title: str) -> dict | None:

    params = {
            "artist": artist,
            "release_date": title,
            "type": "master"
            "per_page": 5,
    }

    response = requests





def save_discogs_data(album: dict) -> Path:
    pass



def process_album(album: dict) -> dict | None
    pass

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
