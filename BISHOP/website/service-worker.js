// BISHOP Website - Service Worker
// Provides offline capabilities and performance improvements

const CACHE_NAME = 'bishop-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.php',
  '/about.php',
  '/pricing.php',
  '/contact.php',
  '/assets/css/style.css',
  '/assets/js/main.js',
  '/assets/img/logo.png',
  '/assets/img/favicon.ico',
  '/assets/img/hero-character.png',
  '/assets/img/about-image.jpg',
  '/assets/img/bot-avatar.png',
  '/offline.html'
];

// Install event - cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  // Skip for API calls and dashboard
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/dashboard/') ||
      event.request.url.includes('/login.php')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        
        // Clone the request
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest)
          .then(response => {
            // Check if valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response
            const responseToCache = response.clone();
            
            // Cache the response
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          })
          .catch(error => {
            // Offline fallback
            if (event.request.mode === 'navigate') {
              return caches.match('/offline.html');
            }
          });
      })
  );
});
