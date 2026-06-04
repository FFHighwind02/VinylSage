const URL = "https://localhost:8000";



// App states
let allAlbums = [];
let filteredAlbums = [];
let isLoading = false;
let albumIndex = null;


const albumListEl = document.getElementById('albumList');
const albumCountEl = document.getElementById('albumCount');
const searchInputEl = document.getElementById('searchInput');
const chatEl = document.getElementById('chat');
const inputBoxEl = document.getElementById('inputBox');
const sendBtnEl = document.getElementById('sendBtn');
const routeBadgeEl = document.getElementById('routeBadge');




// render the albums in the sidebar of the page
function renderAlbums() {
  albumListEl.innerHTML = filteredAlbums.map((album, i) => `
    
        <div class="album-item ${activeAlbumIndex === i ? 'active' : ''}"
         onclick="selectAlbum(${i})">
      
         <div class="album-title">${album.title}</div>
      
         <div class="album-artist">${album.artist}</div>
    
         </div>

  `).join('');

  albumCountEl.textContent = `${filteredAlbums.length} of ${allAlbums.length} albums indexed`;
}





// load album options from albums data file
async function loadAlbums() {
  try {
    const res = await fetch(`${API_URL}/albums`);
    const data = await res.json();
    allAlbums = data.albums || [];
    filteredAlbums = [...allAlbums];
    renderAlbums();

  } catch {
    albumCountEl.textContent = 'API is offline';
  }
}


// When selecting an album from the sidebar panel, fill the chats input box with demo data
function selectAlbum(i) {
  activeAlbumIndex = i;
  renderAlbums();

  const album = filteredAlbums[i];
  inputBoxEl.value = "Tell me about ${album.title} by the artist: ${album.artist}";
  inputBoxEl.focus();

}


searchInputEl.addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase();

  filteredAlbums = q ? allAlbums.filter(a => a.title.toLowerCase().includes(q) || a.artist.toLowerCase().includes(q)) : [...allAlbums];
  activeAlbumIndex = null;
  renderAlbums();
});



// Chat fuctionality















