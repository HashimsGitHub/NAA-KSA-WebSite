const api = '/api';

const el = (id) => document.getElementById(id);
const page = document.body.dataset.page || 'home';

let sessionId = localStorage.getItem('naa_session_id') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');
let adminState = { events: [], knowledge: [], alumni: [] };

function isLoggedIn() {
  return Boolean(sessionId && currentUser);
}

function role() {
  return (currentUser?.role || '').toLowerCase();
}

function canContribute() {
  return ['admin', 'contributor'].includes(role());
}

function isAdmin() {
  return role() === 'admin';
}

function navAllowed(requirement) {
  if (!requirement) return true;
  if (requirement === 'guest') return !isLoggedIn();
  if (requirement === 'user') return isLoggedIn();
  if (requirement === 'contributor') return canContribute();
  if (requirement === 'admin') return isAdmin();
  return true;
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

function setText(id, text) {
  const node = el(id);
  if (node) node.textContent = text;
}

function contentId(item) {
  return item.id || item.event_id || item.post_id || item.alumni_id || '';
}

function renderAuthState() {
  document.querySelectorAll('[data-auth="guest"]').forEach((node) => node.classList.toggle('hidden', isLoggedIn()));
  document.querySelectorAll('[data-auth="user"]').forEach((node) => node.classList.toggle('hidden', !isLoggedIn()));
  document.querySelectorAll('[data-auth="contributor"]').forEach((node) => node.classList.toggle('hidden', !canContribute()));
  document.querySelectorAll('[data-auth="admin"]').forEach((node) => node.classList.toggle('hidden', !isAdmin()));
  document.querySelectorAll('[data-requires]').forEach((node) => {
    const allowed = navAllowed(node.dataset.requires);
    node.classList.toggle('nav-disabled', !allowed);
    node.setAttribute('aria-disabled', allowed ? 'false' : 'true');
    node.tabIndex = allowed ? 0 : -1;
  });
  document.querySelectorAll('[data-user-summary]').forEach((node) => {
    node.textContent = isLoggedIn() ? `${currentUser.full_name || currentUser.email} (${role()})` : '';
  });
}

function renderEvents(items, admin = false) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return '<p class="notice">No events have been published yet.</p>';
  return rows.map((x) => `
    <article class="item">
      ${x.cover_image_url ? `<img src="${escapeHtml(x.cover_image_url)}" alt="${escapeHtml(x.title)}">` : ''}
      <div class="item-body">
        <span class="badge">${escapeHtml(x.event_date || 'Event')}</span>
        <h3>${escapeHtml(x.title || 'Untitled event')}</h3>
        <p>${escapeHtml(x.summary || x.body || '')}</p>
        ${x.venue || x.city ? `<p class="meta">${escapeHtml([x.venue, x.city].filter(Boolean).join(', '))}</p>` : ''}
      </div>
      ${admin ? renderAdminActions('events', contentId(x)) : ''}
    </article>
  `).join('');
}

function renderKnowledge(items, admin = false) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return '<p class="notice">No knowledge-base articles have been published yet.</p>';
  return rows.map((x) => `
    <article class="item">
      ${x.cover_image_url ? `<img src="${escapeHtml(x.cover_image_url)}" alt="${escapeHtml(x.title)}">` : ''}
      <div class="item-body">
        <span class="badge">${escapeHtml(x.tags || 'Knowledge')}</span>
        <h3>${escapeHtml(x.title || 'Untitled article')}</h3>
        <p>${escapeHtml(x.summary || x.body || '')}</p>
      </div>
      ${admin ? renderAdminActions('knowledge', contentId(x)) : ''}
    </article>
  `).join('');
}

function renderAlumni(items, admin = false) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return '<p class="notice">No alumni matched the current filters.</p>';
  return rows.map((a) => `
    <article class="item alumni-item">
      ${a.profile_image_url ? `<img src="${escapeHtml(a.profile_image_url)}" alt="${escapeHtml(a.full_name)}">` : ''}
      <div class="item-body">
        <span class="badge">${escapeHtml(a.graduation_year || 'Alumni')}</span>
        <h3>${escapeHtml(a.full_name || 'Unnamed Alumni')}</h3>
        <p>${escapeHtml([a.degree, a.department].filter(Boolean).join(' - '))}</p>
        <p>${escapeHtml([a.current_position, a.current_company].filter(Boolean).join(' at '))}</p>
        <p class="meta">${escapeHtml([a.city, a.country].filter(Boolean).join(', '))}</p>
        ${a.skills ? `<p>${escapeHtml(a.skills)}</p>` : ''}
        ${a.linkedin_url ? `<p><a href="${escapeHtml(a.linkedin_url)}" target="_blank" rel="noopener">LinkedIn</a></p>` : ''}
      </div>
      ${admin ? renderAdminActions('alumni', a.alumni_id) : ''}
    </article>
  `).join('');
}

function renderAdminActions(type, id) {
  return `
    <div class="actions">
      <button type="button" class="secondary" data-edit="${escapeHtml(type)}" data-id="${escapeHtml(id)}">Edit</button>
      <button type="button" class="danger" data-delete="${escapeHtml(type)}" data-id="${escapeHtml(id)}">Delete</button>
    </div>
  `;
}

async function loadEvents(target = 'eventList') {
  const data = await request('/events');
  setHtml(target, data.success ? renderEvents(data.data, page === 'admin') : `<p class="error">${escapeHtml(data.message || 'Unable to load events.')}</p>`);
  if (data.success && page === 'admin') adminState.events = data.data;
}

async function loadKnowledge(target = 'knowledgeList') {
  if (!isLoggedIn()) {
    setHtml(target, '<p class="notice">Please login to read the Knowledge Base.</p>');
    return;
  }
  const data = await request('/knowledge');
  setHtml(target, data.success ? renderKnowledge(data.data, page === 'admin') : `<p class="error">${escapeHtml(data.message || 'Unable to load knowledge articles.')}</p>`);
  if (data.success && page === 'admin') adminState.knowledge = data.data;
}

function alumniParams() {
  return new URLSearchParams({
    name: el('qName')?.value || '',
    graduation_year: el('qGraduationYear')?.value || '',
    degree: el('qDegree')?.value || '',
    department: el('qDepartment')?.value || '',
    company: el('qCompany')?.value || '',
    country: el('qCountry')?.value || '',
    city: el('qCity')?.value || '',
    skills: el('qSkills')?.value || '',
  });
}

async function loadAlumni(target = 'alumniList') {
  if (!isLoggedIn()) {
    setHtml(target, '<p class="notice">Please login to search alumni.</p>');
    return;
  }
  const data = await request(`/alumni?${alumniParams().toString()}`);
  setHtml(target, data.success ? renderAlumni(data.data, page === 'admin') : `<p class="error">${escapeHtml(data.message || 'Unable to load alumni.')}</p>`);
  if (data.success && page === 'admin') adminState.alumni = data.data;
}

async function login() {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: el('email').value, password: el('password').value })
  });
  setText('loginStatus', data.message || '');
  if (!data.success) return;
  sessionId = data.data.session_id;
  currentUser = data.data.user;
  localStorage.setItem('naa_session_id', sessionId);
  localStorage.setItem('naa_user', JSON.stringify(currentUser));
  renderAuthState();
  const next = new URLSearchParams(window.location.search).get('next');
  window.location.href = next || '/';
}

async function logout() {
  if (sessionId) await request('/auth/logout', { method: 'POST' });
  sessionId = '';
  currentUser = null;
  localStorage.removeItem('naa_session_id');
  localStorage.removeItem('naa_user');
  renderAuthState();
  if (page !== 'home') window.location.href = '/';
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
    body: JSON.stringify({ target, file_name: file.name, content_base64: await fileToBase64(file) })
  });
  if (!uploaded.success) throw new Error(uploaded.message || 'Image upload failed.');
  return uploaded.data.url;
}

function contentPayload() {
  return {
    title: el('contentTitle').value,
    summary: el('contentSummary').value,
    body: el('contentBody').value,
    event_date: el('contentEventDate').value,
    venue: el('contentVenue').value,
    city: el('contentCity').value,
    tags: el('contentTags').value,
    status: el('contentStatus').value || 'published',
  };
}

async function saveContent() {
  try {
    setText('contentStatusText', 'Saving...');
    const type = el('contentType').value;
    const id = el('contentId').value;
    const payload = contentPayload();
    const upload = await uploadSelectedImage(el('contentImage').files[0], type === 'events' ? 'event' : 'knowledge');
    if (upload) payload.cover_image_url = upload;
    const data = await request(id ? `/${type}/${id}` : `/${type}`, {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(payload)
    });
    setText('contentStatusText', data.message || '');
    if (data.success) {
      resetContentForm();
      await refreshAdmin();
    }
  } catch (err) {
    setText('contentStatusText', err.message || 'Failed to save content.');
  }
}

function alumniPayload() {
  return {
    full_name: el('aFullName').value,
    email: el('aEmail').value,
    mobile: el('aMobile').value,
    graduation_year: el('aGraduationYear').value,
    degree: el('aDegree').value,
    department: el('aDepartment').value,
    current_company: el('aCompany').value,
    current_position: el('aPosition').value,
    city: el('aCity').value,
    country: el('aCountry').value,
    skills: el('aSkills').value,
    linkedin_url: el('aLinkedin').value,
    bio: el('aBio').value,
    status: el('aStatus').value || 'active',
    visibility: el('aVisibility').value || 'visible',
  };
}

async function saveAlumni() {
  const id = el('aId').value;
  const data = await request(id ? `/alumni/${id}` : '/alumni', {
    method: id ? 'PUT' : 'POST',
    body: JSON.stringify(alumniPayload())
  });
  setText('alumniAdminStatus', data.message || '');
  if (data.success) {
    resetAlumniForm();
    await refreshAdmin();
  }
}

async function deleteAdminItem(type, id) {
  if (!id) return;
  const data = await request(`/${type}/${id}`, { method: 'DELETE' });
  setText('adminStatus', data.message || '');
  if (data.success) await refreshAdmin();
}

function editContent(type, id) {
  const item = adminState[type].find((x) => contentId(x) === id);
  if (!item) return;
  el('contentType').value = type;
  el('contentId').value = id;
  el('contentTitle').value = item.title || '';
  el('contentSummary').value = item.summary || '';
  el('contentBody').value = item.body || '';
  el('contentEventDate').value = item.event_date || '';
  el('contentVenue').value = item.venue || '';
  el('contentCity').value = item.city || '';
  el('contentTags').value = item.tags || '';
  el('contentStatus').value = item.status || 'published';
  setText('contentStatusText', `Editing ${item.title || id}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function editAlumni(id) {
  const item = adminState.alumni.find((x) => x.alumni_id === id);
  if (!item) return;
  el('aId').value = id;
  el('aFullName').value = item.full_name || '';
  el('aEmail').value = item.email || '';
  el('aMobile').value = item.mobile || '';
  el('aGraduationYear').value = item.graduation_year || '';
  el('aDegree').value = item.degree || '';
  el('aDepartment').value = item.department || '';
  el('aCompany').value = item.current_company || '';
  el('aPosition').value = item.current_position || '';
  el('aCity').value = item.city || '';
  el('aCountry').value = item.country || '';
  el('aSkills').value = item.skills || '';
  el('aLinkedin').value = item.linkedin_url || '';
  el('aBio').value = item.bio || '';
  el('aStatus').value = item.status || 'active';
  el('aVisibility').value = item.visibility || 'visible';
  setText('alumniAdminStatus', `Editing ${item.full_name || id}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetContentForm() {
  ['contentId', 'contentTitle', 'contentSummary', 'contentBody', 'contentEventDate', 'contentVenue', 'contentCity', 'contentTags'].forEach((id) => { if (el(id)) el(id).value = ''; });
  if (el('contentImage')) el('contentImage').value = '';
  if (el('contentStatus')) el('contentStatus').value = 'published';
}

function resetAlumniForm() {
  ['aId', 'aFullName', 'aEmail', 'aMobile', 'aGraduationYear', 'aDegree', 'aDepartment', 'aCompany', 'aPosition', 'aCity', 'aCountry', 'aSkills', 'aLinkedin', 'aBio'].forEach((id) => { if (el(id)) el(id).value = ''; });
  if (el('aStatus')) el('aStatus').value = 'active';
  if (el('aVisibility')) el('aVisibility').value = 'visible';
}

function updateAdminCounts() {
  setText('countAlumni', adminState.alumni.length);
  setText('countEvents', adminState.events.length);
  setText('countKnowledge', adminState.knowledge.length);
}

async function refreshAdmin() {
  if (!canContribute()) {
    setHtml('adminWorkspace', '<p class="notice">Contributor or admin access is required for this page.</p>');
    return;
  }
  const tasks = [loadEvents('adminEventList'), loadKnowledge('adminKnowledgeList')];
  if (isAdmin()) tasks.push(loadAlumni('adminAlumniList'));
  await Promise.all(tasks);
  if (isAdmin()) updateAdminCounts();
}

function wireEvents() {
  el('loginButton')?.addEventListener('click', login);
  el('logoutButton')?.addEventListener('click', logout);
  el('searchButton')?.addEventListener('click', () => loadAlumni());
  el('saveContentButton')?.addEventListener('click', saveContent);
  el('resetContentButton')?.addEventListener('click', resetContentForm);
  el('saveAlumniButton')?.addEventListener('click', saveAlumni);
  el('resetAlumniButton')?.addEventListener('click', resetAlumniForm);
  document.addEventListener('click', (event) => {
    const disabledNav = event.target.closest('[data-requires].nav-disabled');
    if (disabledNav) {
      event.preventDefault();
      return;
    }
    const edit = event.target.closest('[data-edit]');
    const del = event.target.closest('[data-delete]');
    if (edit) {
      const type = edit.dataset.edit;
      if (type === 'alumni') editAlumni(edit.dataset.id);
      else editContent(type, edit.dataset.id);
    }
    if (del) deleteAdminItem(del.dataset.delete, del.dataset.id);
  });
}

async function init() {
  renderAuthState();
  wireEvents();
  if (page === 'home' || page === 'events') await loadEvents();
  if (page === 'knowledge') await loadKnowledge();
  if (page === 'alumni') await loadAlumni();
  if (page === 'admin') await refreshAdmin();
}

init();
