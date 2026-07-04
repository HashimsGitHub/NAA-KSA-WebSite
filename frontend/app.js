const api = '/api';

const el = (id) => document.getElementById(id);

let sessionId = localStorage.getItem('naa_session_id') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');

function isLoggedIn() {
  return Boolean(sessionId && currentUser);
}

function role() {
  return (currentUser?.role || '').toLowerCase();
}

function sessionHeaders() {
  return sessionId ? { 'X-Session-Id': sessionId } : {};
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}), ...sessionHeaders() };
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(`${api}${path}`, { ...options, headers });
  let data;
  try {
    data = await res.json();
  } catch (_) {
    data = { success: false, message: `Invalid API response. HTTP ${res.status}` };
  }
  return { httpStatus: res.status, ...data };
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

function setHtml(id, html) {
  const node = el(id);
  if (node) node.innerHTML = html;
}

function show(id, visible) {
  const node = el(id);
  if (node) node.classList.toggle('hidden', !visible);
}

function renderAccessState() {
  const loggedIn = isLoggedIn();
  const r = role();
  show('loginBox', !loggedIn);
  show('userBox', loggedIn);
  show('alumniSearchBox', loggedIn);
  show('adminPanel', loggedIn && ['admin', 'contributor'].includes(r));
  show('adminAlumniBox', loggedIn && r === 'admin');

  if (loggedIn) {
    el('userSummary').textContent = `${currentUser.full_name || currentUser.email} (${r})`;
    el('loginStatus').textContent = 'Login successful.';
  } else {
    el('loginStatus').textContent = '';
    setHtml('alumniList', '<p class="notice">Login to search alumni.</p>');
    setHtml('knowledgeList', '<p class="notice">Login to read the Knowledge Base.</p>');
  }
}

async function login() {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: el('email').value, password: el('password').value })
  });
  el('loginStatus').textContent = data.message || '';
  if (!data.success) return;

  sessionId = data.data.session_id;
  currentUser = data.data.user;
  localStorage.setItem('naa_session_id', sessionId);
  localStorage.setItem('naa_user', JSON.stringify(currentUser));
  renderAccessState();
  await loadPrivateContent();
}

async function logout() {
  if (sessionId) await request('/auth/logout', { method: 'POST' });
  sessionId = '';
  currentUser = null;
  localStorage.removeItem('naa_session_id');
  localStorage.removeItem('naa_user');
  renderAccessState();
}

function renderContent(items, emptyText) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return `<p>${escapeHtml(emptyText)}</p>`;
  return rows.map((x) => `
    <article class="item">
      ${x.cover_image_url ? `<img src="${escapeHtml(x.cover_image_url)}" alt="${escapeHtml(x.title)}">` : ''}
      <h3>${escapeHtml(x.title || 'Untitled')}</h3>
      <span class="badge">${escapeHtml(x.event_date || x.category || 'post')}</span>
      <p>${escapeHtml(x.summary || '')}</p>
      <p>${escapeHtml(x.body || '')}</p>
    </article>
  `).join('');
}

function renderAlumni(items) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return '<p>No alumni found.</p>';
  return rows.map((a) => `
    <article class="item">
      ${a.profile_image_url ? `<img src="${escapeHtml(a.profile_image_url)}" alt="${escapeHtml(a.full_name)}">` : ''}
      <h3>${escapeHtml(a.full_name || 'Unnamed Alumni')}</h3>
      <span class="badge">${escapeHtml(a.graduation_year || 'Alumni')}</span>
      <p>${escapeHtml([a.degree, a.department].filter(Boolean).join(' - '))}</p>
      <p>${escapeHtml([a.current_position, a.current_company].filter(Boolean).join(' at '))}</p>
      <p>${escapeHtml([a.city, a.country].filter(Boolean).join(', '))}</p>
      <p>${escapeHtml(a.skills || '')}</p>
      ${a.linkedin_url ? `<p><a href="${escapeHtml(a.linkedin_url)}" target="_blank" rel="noopener">LinkedIn</a></p>` : ''}
    </article>
  `).join('');
}

async function loadEvents() {
  const data = await request('/events');
  setHtml('eventList', data.success ? renderContent(data.data, 'No events yet.') : `<p class="error">${escapeHtml(data.message || 'Unable to load events.')}</p>`);
}

async function loadKnowledge() {
  if (!isLoggedIn()) {
    setHtml('knowledgeList', '<p class="notice">Login to read the Knowledge Base.</p>');
    return;
  }
  const data = await request('/knowledge');
  setHtml('knowledgeList', data.success ? renderContent(data.data, 'No knowledge articles yet.') : `<p class="error">${escapeHtml(data.message || 'Unable to load knowledge articles.')}</p>`);
}

async function loadAlumni() {
  if (!isLoggedIn()) {
    setHtml('alumniList', '<p class="notice">Login to search alumni.</p>');
    return;
  }
  const params = new URLSearchParams({
    name: el('qName').value,
    graduation_year: el('qGraduationYear').value,
    degree: el('qDegree').value,
    department: el('qDepartment').value,
    company: el('qCompany').value,
    country: el('qCountry').value,
  });
  const data = await request(`/alumni?${params.toString()}`);
  setHtml('alumniList', data.success ? renderAlumni(data.data) : `<p class="error">${escapeHtml(data.message || 'Unable to load alumni.')}</p>`);
}

async function loadPrivateContent() {
  if (!isLoggedIn()) return;
  await loadAlumni();
  await loadKnowledge();
}

async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function uploadSelectedImage(file, target) {
  if (!file) return '';

  const uploaded = await request('/media/upload', {
    method: 'POST',
    body: JSON.stringify({
      target,
      file_name: file.name,
      content_base64: await fileToBase64(file)
    })
  });

  if (!uploaded.success) throw new Error(uploaded.message || 'Image upload failed.');

  return uploaded.data.url;
}

async function createContent() {
  try {
    el('adminStatus').textContent = 'Saving...';

    const type = el('newType').value; // expected: "events" or "knowledge"
    const isEvent = type === 'events';

    const cover_image_url = await uploadSelectedImage(
      el('newImage').files[0],
      isEvent ? 'event' : 'knowledge'
    );

    const data = await request(isEvent ? '/events' : '/knowledge', {
      method: 'POST',
      body: JSON.stringify({
        title: el('newTitle').value,
        summary: el('newSummary').value,
        body: el('newBody').value,
        event_date: el('newEventDate').value,
        cover_image_url: cover_image_url || '',
        category: isEvent ? 'event' : 'knowledge',
        status: 'published'
      })
    });

    el('adminStatus').textContent = data.message || (data.success ? 'Created.' : 'Failed.');

    if (data.success) {
      ['newTitle', 'newSummary', 'newBody', 'newEventDate'].forEach((id) => {
        el(id).value = '';
      });
      el('newImage').value = '';

      await loadEvents();

      if (isLoggedIn()) {
        await loadKnowledge();
      }
    }
  } catch (err) {
    el('adminStatus').textContent = err.message || 'Failed to create content.';
  }
}

async function createAlumni() {
  const data = await request('/alumni', {
    method: 'POST',
    body: JSON.stringify({
      full_name: el('aFullName').value,
      email: el('aEmail').value,
      graduation_year: el('aGraduationYear').value,
      degree: el('aDegree').value,
      department: el('aDepartment').value,
      current_company: el('aCompany').value,
      current_position: el('aPosition').value,
      city: el('aCity').value,
      country: el('aCountry').value,
      skills: el('aSkills').value,
      bio: el('aBio').value,
      status: 'active',
      visibility: 'visible'
    })
  });
  el('alumniAdminStatus').textContent = data.message || (data.success ? 'Created.' : 'Failed.');
  if (data.success) {
    ['aFullName', 'aEmail', 'aGraduationYear', 'aDegree', 'aDepartment', 'aCompany', 'aPosition', 'aCity', 'aCountry', 'aSkills', 'aBio'].forEach((id) => { el(id).value = ''; });
    await loadAlumni();
  }
}

function wireEvents() {
  el('loginButton')?.addEventListener('click', login);
  el('logoutButton')?.addEventListener('click', logout);
  el('searchButton')?.addEventListener('click', loadAlumni);
  el('createPostButton')?.addEventListener('click', createContent);
  el('createAlumniButton')?.addEventListener('click', createAlumni);
}

wireEvents();
renderAccessState();
loadEvents();
if (isLoggedIn()) loadPrivateContent();
