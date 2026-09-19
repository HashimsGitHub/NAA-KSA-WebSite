// Only public, fixed site assets may enter this cache. Pages and API data stay online.
const CACHE_NAME = 'vcnity-static-v1';
const ASSETS = [
  '/app.js',
  '/styles.css',
  '/manifest.json',
  '/offline.html',
  '/assets/vcnity/VCNITY_logo.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/icon-maskable-512.png'
];
const STATIC_PATHS = new Set(ASSETS);

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => Promise.all(
      names.filter((name) => name.startsWith('vcnity-static-') && name !== CACHE_NAME)
        .map((name) => caches.delete(name))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;

  if (request.mode === 'navigate') {
    // Never cache HTML: member/admin pages can contain private information.
    event.respondWith(fetch(request).catch(async () =>
      (await caches.match('/offline.html')) || Response.error()
    ));
    return;
  }

  if (!url.search && STATIC_PATHS.has(url.pathname)) {
    event.respondWith(fetch(request).then((response) => {
      if (response.ok && response.type === 'basic') {
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)));
      }
      return response;
    }).catch(async () => (await caches.match(request)) || Response.error()));
  }
});
