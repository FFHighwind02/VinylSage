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
const inbutBoxEl = document.getElementById('inputBox');
const sendBtnEl = document.getElementById('sendBtn');
const routeBadgeEl = document.getElementById('routeBadge');


async function loadAlbums() {
  try {
    const res = await fetch(`${API_URL}/albums`);
    const data = await res.json();
    

  }



};