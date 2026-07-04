const api = '/api';
let token = localStorage.getItem('naa_token') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');

function authHeaders() {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function isLoggedIn() {
  return Boolean(token && currentUser);
}

async function request(path, options = {}) {
  const res = await fetch(`${api}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {})
    }
  });

  let data = {};
  try {
    data = await res.json();
  } catch (_) {
    data = { success: false, message: 'Invalid API response.' };
  }
  return { httpStatus: res.status, ...data };
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[char]));
}

async function login() {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.value, password: password.value })
  });

  loginStatus.textContent = data.message || '';
  if (data.success) {
    token = data.data.token;
    currentUser = data.data.user;
    localStorage.setItem('naa_token', token);
    localStorage.setItem('naa_user', JSON.stringify(currentUser));
    renderAccessState();
    await loadPrivateContent();
  }
}

function logout() {
  token = '';
  currentUser = null;
  localStorage.removeItem('naa_token');
  localStorage.removeItem('naa_user');
  renderAccessState();
}

function renderAccessState() {
  const loggedIn = isLoggedIn();
  const role = currentUser?.role || '';

  loginBox.classList.toggle('hidden', loggedIn);
  userBox.classList.toggle('hidden', !loggedIn);
  adminPanel.classList.toggle('hidden', !(role === 'admin' || role === 'contributor'));
  alumniSearchBox.classList.toggle('hidden', !loggedIn);

  userSummary.textContent = loggedIn ? `${currentUser.full_name || currentUser.email} (${role})` : '';

  if (!loggedIn) {
    alumniList.innerHTML = '<p class="notice">Login to search alumni.</p>';
    knowledgeList.innerHTML = '<p class="notice">Login to read the Knowledge Base.</p>';
  }
}

async function loadAlumni() {
  if (!isLoggedIn()) {
    alumniList.innerHTML = '<p class="notice">Login to search alumni.</p>';
    return;
  }

  const params = new URLSearchParams({
    name: qName.value,
    city: qCity.value,
    company: qCompany.value,
    skills: qSkills.value
  });

  const data = await request(`/alumni?${params.toString()}`);
  if (!data.success) {
    alumniList.innerHTML = `<p class="error">${escapeHtml(data.message || 'Unable to load alumni.')}</p>`;
    return;
  }

  alumniList.innerHTML = (data.data || []).map(a => `
    <article class="item">
      ${a.profile_image_url ? `<img src="${escapeHtml(a.profile_image_url)}" alt="${escapeHtml(a.full_name)}">` : ''}
      <h3>${escapeHtml(a.full_name || 'Unnamed Alumni')}</h3>
      <span class="badge">${escapeHtml(a.graduation_year || 'Alumni')}</span>
      <p>${escapeHtml([a.current_position, a.current_company].filter(Boolean).join(' at '))}</p>
      <p>${escapeHtml([a.city, a.country].filter(Boolean).join(', '))}</p>
      <p>${escapeHtml(a.skills || '')}</p>
    </article>`).join('') || '<p>No alumni found.</p>';
}

async function loadEvents() {
  const events = await request('/events');
  eventList.innerHTML = events.success ? renderContent(events.data || []) : `<p class="error">${escapeHtml(events.message || 'Unable to load events.')}</p>`;
}

async function loadKnowledge() {
  if (!isLoggedIn()) {
    knowledgeList.innerHTML = '<p class="notice">Login to read the Knowledge Base.</p>';
    return;
  }

  const posts = await request('/knowledge');
  knowledgeList.innerHTML = posts.success ? renderContent(posts.data || []) : `<p class="error">${escapeHtml(posts.message || 'Unable to load knowledge posts.')}</p>`;
}

async function loadPrivateContent() {
  await loadAlumni();
  await loadKnowledge();
}

function renderContent(items) {
  return items.map(x => `
    <article class="item">
      ${x.cover_image_url ? `<img src="${escapeHtml(x.cover_image_url)}" alt="${escapeHtml(x.title)}">` : ''}
      <h3>${escapeHtml(x.title)}</h3>
      <span class="badge">${escapeHtml(x.event_date || x.category || 'post')}</span>
      <p>${escapeHtml(x.summary || '')}</p>
      <p>${escapeHtml(x.body || '')}</p>
    </article>`).join('') || '<p>No posts yet.</p>';
}

async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function createContent() {
  let cover_image_url = '';
  const file = newImage.files[0];
  const type = newType.value;

  adminStatus.textContent = 'Saving...';

  if (file) {
    const uploaded = await request('/media/upload', {
      method: 'POST',
      body: JSON.stringify({
        target: type === 'events' ? 'event' : 'blog',
        file_name: file.name,
        content_base64: await fileToBase64(file)
      })
    });
    if (!uploaded.success) {
      adminStatus.textContent = uploaded.message || 'Image upload failed.';
      return;
    }
    cover_image_url = uploaded.data.url;
  }

  const created = await request(`/${type === 'events' ? 'events' : 'knowledge'}`, {
    method: 'POST',
    body: JSON.stringify({
      title: newTitle.value,
      summary: newSummary.value,
      body: newBody.value,
      event_date: newEventDate.value,
      cover_image_url,
      status: 'published',
      category: type === 'events' ? 'event' : 'knowledge'
    })
  });

  adminStatus.textContent = created.message || (created.success ? 'Created.' : 'Failed.');
  if (created.success) {
    newTitle.value = '';
    newSummary.value = '';
    newBody.value = '';
    newEventDate.value = '';
    newImage.value = '';
    await loadEvents();
    await loadKnowledge();
  }
}

renderAccessState();
loadEvents();
if (isLoggedIn()) loadPrivateContent();
