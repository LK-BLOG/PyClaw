// PyClaw Service Worker
// 简单的缓存策略 - 仅用于避免注册失败

self.addEventListener('install', (event) => {
  console.log('PyClaw Service Worker 已安装');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('PyClaw Service Worker 已激活');
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // 简单的网络优先策略
  event.respondWith(
    fetch(event.request).catch(() => {
      // 网络失败时返回基本响应
      return new Response('PyClaw Service Worker', {
        status: 200,
        statusText: 'OK',
        headers: { 'Content-Type': 'text/plain' }
      });
    })
  );
});
