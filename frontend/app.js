const api = '/api';
let token = localStorage.getItem('naa_token') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');

function authHeaders() {
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const res = await fetch(`${api}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...(options.headers || {}) }
  });
  return await res.json();
}

async function login() {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.value, password: password.value })
  });
  loginStatus.textContent = data.message;
  if (data.success) {
    token = data.data.token;
    currentUser = data.data.user;
    localStorage.setItem('naa_token', token);
    localStorage.setItem('naa_user', JSON.stringify(currentUser));
    showRolePanel();
  }
}

function showRolePanel() {
  const role = currentUser?.role;
  adminPanel.classList.toggle('hidden', !(role === 'admin' || role === 'contributor'));
}

async function loadAlumni() {
  const params = new URLSearchParams({
    name: qName.value,
    city: qCity.value,
    company: qCompany.value,
    skills: qSkills.value
  });
  const data = await request(`/alumni?${params.toString()}`);
  alumniList.innerHTML = (data.data || []).map(a => `
    <article class="item">
      ${a.profile_image_url ? `<img src="${a.profile_image_url}" alt="${a.full_name}">` : ''}
      <h3>${a.full_name || 'Unnamed Alumni'}</h3>
      <span class="badge">${a.graduation_year || 'Alumni'}</span>
      <p>${[a.current_position, a.current_company].filter(Boolean).join(' at ')}</p>
      <p>${[a.city, a.country].filter(Boolean).join(', ')}</p>
      <p>${a.skills || ''}</p>
    </article>`).join('') || '<p>No alumni found.</p>';
}

async function loadContent() {
  const events = await request('/events');
  eventList.innerHTML = renderContent(events.data || []);
  const blogs = await request('/blogs');
  blogList.innerHTML = renderContent(blogs.data || []);
}

function renderContent(items) {
  return items.map(x => `
    <article class="item">
      ${x.cover_image_url ? `<img src="${x.cover_image_url}" alt="${x.title}">` : ''}
      <h3>${x.title}</h3>
      <span class="badge">${x.event_date || x.category || 'post'}</span>
      <p>${x.summary || ''}</p>
      <p>${x.body || ''}</p>
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
  if (file) {
    const uploaded = await request('/media/upload', {
      method: 'POST',
      body: JSON.stringify({
        target: type === 'events' ? 'event' : 'blog',
        file_name: file.name,
        content_base64: await fileToBase64(file)
      })
    });
    if (uploaded.success) cover_image_url = uploaded.data.url;
  }
  const created = await request(`/${type}`, {
    method: 'POST',
    body: JSON.stringify({
      title: newTitle.value,
      summary: newSummary.value,
      body: newBody.value,
      event_date: newEventDate.value,
      cover_image_url,
      status: 'published',
      category: type === 'blogs' ? 'knowledge' : 'event'
    })
  });
  adminStatus.textContent = created.message || (created.success ? 'Created' : 'Failed');
  await loadContent();
}

showRolePanel();
loadAlumni();
loadContent();
