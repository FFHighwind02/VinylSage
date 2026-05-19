"""
    Additional script for dynamically adding new albums to the training data,
    in the event a user inputs one that 
    VinylSage doesn't recognize.

Author: Nicholas Kennedy
05/18/2026
"""



from albums import ANCHOR_ALBUMS

import wikipediaapi





WIKI = wikipediaapi.Wikipedia(user_agent='VinylSage (https://github.com/FFHighwind02/VinylSage)', language='en')



def check_valid(title: str, artist: str) -> bool:
    """
        Validates the title and artist provided by the user to ensure the page exists
    """

    page_ex = WIKI.page(title)
    print("Page exists: %s" % page_ex.exists())
    
    page_al = WIKI.page(title + " (album)")
    print("Page exists plus album: %s" % page_al.exists())

    if(page_ex.exists() == False and page_al.exists() == False):
        return False
        
    
    # only run if the wiki check passes
    for i in range(len(ANCHOR_ALBUMS)):
        
        # Check if the artist and title have a shared entry in the list already
        if(ANCHOR_ALBUMS[i].get("title") == title and ANCHOR_ALBUMS[i].get("artist") == artist):
            return False
        


    return True
            




#def verifyInput -- TODO: make a more verbose func to verify that a user isn't uploading junk data, and so that verification
#                           can be automatic




def process_add_album() -> None:

    title = input("Provide the album title you wish to add: ")
    artist = input("Provide the artist name attached to the album: ")


    if check_valid(title, artist):
        
        print("Album name appears valid.\nDouble check summary and answer 'y' to add, or 'n' to skip\n\n")
        
        print(WIKI.title)
        print(WIKI.summary)

        isAdd = input("Approve the addition?")
        
        if(isAdd == True):
            ANCHOR_ALBUMS.append({"title": title,"artist": artist})
            print("Add approved, run the pull_wikipedia script with build index to have access to the new album!\n")
            return
        
        else:
            return None
        
    else:

        return



