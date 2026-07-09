const api = '/api';

const el = (id) => document.getElementById(id);
const page = document.body.dataset.page || 'home';

let sessionId = localStorage.getItem('naa_session_id') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');
let adminState = { events: [], knowledge: [], alumni: [] };
const alumniPaging = {
  alumniList: { page: 1, pageSize: 24, items: [] },
  adminAlumniList: { page: 1, pageSize: 12, items: [] },
};

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
  document.querySelectorAll('[data-admin-only-controls]').forEach((node) => {
    const disabled = !isAdmin();
    node.classList.toggle('is-disabled', disabled);
    node.querySelectorAll('input, select, textarea, button').forEach((control) => {
      control.disabled = disabled;
      control.setAttribute('aria-disabled', disabled ? 'true' : 'false');
    });
  });
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
  const disableActions = page === 'admin' && !isAdmin();
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
      ${admin ? renderAdminActions('alumni', a.alumni_id, disableActions) : ''}
    </article>
  `).join('');
}

function alumniPageSize(target) {
  return target === 'adminAlumniList' ? 12 : 24;
}

function alumniTargetLabel(target) {
  return target === 'adminAlumniList' ? 'admin alumni records' : 'alumni profiles';
}

function setAlumniPage(target, pageNumber) {
  const state = alumniPaging[target];
  if (!state) return;
  const pageCount = Math.max(1, Math.ceil(state.items.length / state.pageSize));
  state.page = Math.min(Math.max(1, pageNumber), pageCount);
  renderAlumniPage(target);
}

function renderAlumniPager(target, page, pageCount, total, from, to) {
  const label = alumniTargetLabel(target);
  if (!total) return '';
  return `
    <div class="pagination" aria-label="${escapeHtml(label)} pagination">
      <p class="pagination-summary">Showing ${from}-${to} of ${total} ${escapeHtml(label)}</p>
      <div class="pagination-actions">
        <button type="button" class="secondary" data-alumni-page-target="${escapeHtml(target)}" data-alumni-page="first" ${page <= 1 ? 'disabled' : ''}>First</button>
        <button type="button" class="secondary" data-alumni-page-target="${escapeHtml(target)}" data-alumni-page="prev" ${page <= 1 ? 'disabled' : ''}>Previous</button>
        <span class="page-indicator">Page ${page} of ${pageCount}</span>
        <button type="button" class="secondary" data-alumni-page-target="${escapeHtml(target)}" data-alumni-page="next" ${page >= pageCount ? 'disabled' : ''}>Next</button>
        <button type="button" class="secondary" data-alumni-page-target="${escapeHtml(target)}" data-alumni-page="last" ${page >= pageCount ? 'disabled' : ''}>Last</button>
      </div>
    </div>
  `;
}

function renderAlumniPage(target) {
  const state = alumniPaging[target];
  if (!state) return;
  const total = state.items.length;
  const pageCount = Math.max(1, Math.ceil(total / state.pageSize));
  state.page = Math.min(Math.max(1, state.page), pageCount);

  if (!total) {
    setHtml(target, renderAlumni([], page === 'admin'));
    return;
  }

  const start = (state.page - 1) * state.pageSize;
  const pageItems = state.items.slice(start, start + state.pageSize);
  const from = start + 1;
  const to = start + pageItems.length;
  setHtml(target, `${renderAlumniPager(target, state.page, pageCount, total, from, to)}${renderAlumni(pageItems, page === 'admin')}${renderAlumniPager(target, state.page, pageCount, total, from, to)}`);
}

function renderAdminActions(type, id, disabled = false) {
  const disabledAttributes = disabled ? 'disabled aria-disabled="true"' : '';
  return `
    <div class="actions">
      <button type="button" class="secondary" data-edit="${escapeHtml(type)}" data-id="${escapeHtml(id)}" ${disabledAttributes}>Edit</button>
      <button type="button" class="danger" data-delete="${escapeHtml(type)}" data-id="${escapeHtml(id)}" ${disabledAttributes}>Delete</button>
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
  if (!data.success) {
    setHtml(target, `<p class="error">${escapeHtml(data.message || 'Unable to load alumni.')}</p>`);
    return;
  }

  if (!alumniPaging[target]) alumniPaging[target] = { page: 1, pageSize: alumniPageSize(target), items: [] };
  alumniPaging[target].items = Array.isArray(data.data) ? data.data : [];
  alumniPaging[target].pageSize = alumniPageSize(target);
  alumniPaging[target].page = 1;
  renderAlumniPage(target);
  if (page === 'admin') adminState.alumni = alumniPaging[target].items;
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
    role: el('aRole').value || 'alumni',
    visibility: 'visible',
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
  el('aRole').value = item.role || 'alumni';
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
  if (el('aRole')) el('aRole').value = 'alumni';
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
  const tasks = [loadEvents('adminEventList'), loadKnowledge('adminKnowledgeList'), loadAlumni('adminAlumniList')];
  await Promise.all(tasks);
  updateAdminCounts();
  renderAuthState();
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
    const pageControl = event.target.closest('[data-alumni-page]');
    if (pageControl && !pageControl.disabled) {
      const target = pageControl.dataset.alumniPageTarget;
      const state = alumniPaging[target];
      if (!state) return;
      const pageCount = Math.max(1, Math.ceil(state.items.length / state.pageSize));
      const nextPage = {
        first: 1,
        prev: state.page - 1,
        next: state.page + 1,
        last: pageCount,
      }[pageControl.dataset.alumniPage];
      if (nextPage) setAlumniPage(target, nextPage);
      return;
    }
    if (edit?.disabled || del?.disabled) return;
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
