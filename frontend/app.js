const api = '/api';
let sessionId = localStorage.getItem('naa_session_id') || '';
let currentUser = JSON.parse(localStorage.getItem('naa_user') || 'null');

function authHeaders() {
  return sessionId ? { 'X-Session-Id': sessionId } : {};
}

function isLoggedIn() {
  return Boolean(sessionId && currentUser);
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

function formValue(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}

async function login() {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.value, password: password.value })
  });

  loginStatus.textContent = data.message || '';

  if (data.success) {
    sessionId = data?.data?.session_id || data?.data?.token || '';
    currentUser = data?.data?.user || { email: email.value, role: 'alumni', full_name: email.value };

    localStorage.setItem('naa_session_id', sessionId);
    localStorage.setItem('naa_user', JSON.stringify(currentUser));
    localStorage.removeItem('naa_token');

    renderAccessState();
    await loadPrivateContent();
    await loadEvents();
  }
}

function logout() {
  sessionId = '';
  currentUser = null;
  localStorage.removeItem('naa_session_id');
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
  alumniAdminPanel.classList.toggle('hidden', role !== 'admin');
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
    name: formValue('qName'),
    graduation_year: formValue('qGraduationYear'),
    department: formValue('qDepartment'),
    country: formValue('qCountry'),
    city: formValue('qCity'),
    company: formValue('qCompany'),
    skills: formValue('qSkills')
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
      <p>${escapeHtml([a.degree, a.department].filter(Boolean).join(' - '))}</p>
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
  if (!isLoggedIn()) {
    alumniList.innerHTML = '<p class="notice">Login to search alumni.</p>';
    knowledgeList.innerHTML = '<p class="notice">Login to read the Knowledge Base.</p>';
    return;
  }

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

async function uploadImage(file, target) {
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
  const type = newType.value;
  adminStatus.textContent = 'Saving...';

  try {
    const cover_image_url = await uploadImage(newImage.files[0], type === 'events' ? 'event' : 'blog');
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
  } catch (err) {
    adminStatus.textContent = err.message;
  }
}

async function createAlumni() {
  alumniAdminStatus.textContent = 'Saving alumni...';

  try {
    const profile_image_url = await uploadImage(alumniImage.files[0], 'profile');
    const payload = {
      full_name: alumniFullName.value,
      email: alumniEmail.value,
      city: alumniCity.value,
      country: alumniCountry.value,
      degree: alumniDegree.value,
      department: alumniDepartment.value,
      graduation_year: alumniGraduationYear.value,
      current_company: alumniCompany.value,
      current_position: alumniPosition.value,
      skills: alumniSkills.value,
      profile_image_url,
      visibility: 'visible',
      status: 'active'
    };

    const created = await request('/alumni', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    alumniAdminStatus.textContent = created.message || (created.success ? 'Alumni created.' : 'Failed.');
    if (created.success) {
      ['alumniFullName','alumniEmail','alumniCity','alumniCountry','alumniDegree','alumniDepartment','alumniGraduationYear','alumniCompany','alumniPosition','alumniSkills'].forEach(id => document.getElementById(id).value = '');
      alumniImage.value = '';
      await loadAlumni();
    }
  } catch (err) {
    alumniAdminStatus.textContent = err.message;
  }
}

renderAccessState();
loadEvents();
if (isLoggedIn()) loadPrivateContent();
