const API_URL = "https://web-production-6b50.up.railway.app";



// App states
let allAlbums = [];
let filteredAlbums = [];
let isLoading = false;
let activeAlbumIndex = null;


document.addEventListener('DOMContentLoaded', () => {

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
    <div class="album-item ${activeAlbumIndex === i ? 'active' : ''}" data-index="${i}">
      <div class="album-title">${album.title}</div>
      <div class="album-artist">${album.artist}</div>
    </div>
      `).join('');

    
    albumListEl.addEventListener('click', (e) => {
      const item = e.target.closest('.album-item');
      if (item) selectAlbum(parseInt(item.dataset.index));
    });

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
    inputBoxEl.value = `Tell me about ${album.title} by the artist: ${album.artist}`;
    inputBoxEl.focus();

  }


  searchInputEl.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();

    filteredAlbums = q ? allAlbums.filter(a => a.title.toLowerCase().includes(q) || a.artist.toLowerCase().includes(q)) : [...allAlbums];
    activeAlbumIndex = null;
    renderAlbums();
  });



  // Chat fuctionality

  function addMessage(role, content, sources = [], route = null) {
    if (route) {
      routeBadgeEl.className = `route-badge ${route}`;
      routeBadgeEl.textContent = route === 'rag' ? 'Knowledge Base' : 'Discogs Data';
    }

    const msgEl = document.createElement('div');
    msgEl.className = `msg ${role}`;

    const label = role === 'user' ? 'You' : 'VinylSage';


    let html = `
      <div class="msg-label">${label}</div>
      <div class="msg-bubble">${escapeHtml(content)}</div>
    `;

    if (sources && sources.length > 0) {
    html += `<div class="sources">`;
    sources.forEach(source => {
      const pct = Math.round(source.relevance * 100);
      html += `
        <a class="source-item" href="${source.url}" target="_blank" rel="noopener">
          <div class="source-dot"></div>
          <span>${source.artist} — ${source.album}</span>
          <span class="source-score">${pct}%</span>
        </a>
      `;
    });
    html += `</div>`;
  }

    msgEl.innerHTML = html;
    chatEl.appendChild(msgEl);
    chatEl.scrollTop = chatEl.scrollHeight;
  }



  function addTypingIndicator() {
    const el = document.createElement('div');
    el.className = 'msg assistant';
    el.id = 'typing-indicator';
    el.innerHTML = `
      <div class="msg-label">VinylSage</div>
      <div class="msg-bubble">
        <div class="typing">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    chatEl.appendChild(el);
    chatEl.scrollTop = chatEl.scrollHeight;
  }



  function removeTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
  }



  /* Query functionality */

  async function sendQuery() {
    const question = inputBoxEl.value.trim();
    if (!question || isLoading) return;

    inputBoxEl.value = '';
    activeAlbumIndex = null;
    renderAlbums();
    isLoading = true;
    sendBtnEl.disabled = true;


    addMessage('user', question);
    addTypingIndicator();

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 5 }),
      });

      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();

      removeTypingIndicator();
      addMessage('assistant', data.answer, data.sources, data.route);

    } catch (err) {
      removeTypingIndicator();
      addMessage(
        'assistant',
        'Could not reach the VinylSage API. Make sure it is running:\n\nuvicorn src.api:app --reload --port 8000'
      );
    } finally {
      isLoading = false;
      sendBtnEl.disabled = false;
      inputBoxEl.focus();
    }
  }

  // Button and box events

  sendBtnEl.addEventListener('click', sendQuery);

  inputBoxEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  });


  // Auto-resize textarea
  inputBoxEl.addEventListener('input', () => {
    inputBoxEl.style.height = 'auto';
    inputBoxEl.style.height = Math.min(inputBoxEl.scrollHeight, 120) + 'px';
  });



  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }



  addMessage(
    'assistant',
    'Welcome to VinylSage. I know 204 classic rock albums — their histories, influences, critical reception, and pressing variants. Ask me anything, or click an album in the sidebar to get started!'
  );


  loadAlbums();

});
