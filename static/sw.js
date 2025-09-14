const CACHE_NAME = 'loyalty-app-v2';
const DYNAMIC_CACHE_NAME = 'loyalty-app-dynamic-v2';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/app.js',
  '/static/qr-scanner.js',
  '/auth/login',
  '/auth/register',
  '/dashboard/',
  '/transactions/issue',
  '/transactions/transfer',
  '/transactions/redeem',
  'https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css'
];

// Install service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate service worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - network first strategy
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).then(response => {
      // Check if we received a valid response
      if (!response || response.status !== 200 || response.type !== 'basic') {
        return response;
      }

      var responseToCache = response.clone();

      caches.open(DYNAMIC_CACHE_NAME)
        .then(cache => {
          cache.put(event.request, responseToCache);
        });

      return response;
    }).catch(() => {
      return caches.match(event.request);
    })
  );
});
