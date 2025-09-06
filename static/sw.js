const CACHE_NAME = 'loyalty-app-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/app.js',
  '/auth/login',
  '/dashboard/',
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

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Background sync for form submissions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Handle background sync for offline form submissions
  return caches.open('form-cache').then(cache => {
    return cache.keys().then(requests => {
      return Promise.all(
        requests.map(request => {
          return cache.match(request).then(response => {
            // Attempt to submit cached form data
            return fetch(request.url, {
              method: 'POST',
              body: response.body,
              headers: response.headers
            });
          });
        })
      );
    });
  });
}

// Activate service worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
