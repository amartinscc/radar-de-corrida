// Service worker mínimo do gerador de links: permite instalar na tela inicial
// (e aparecer no menu Compartilhar do Android). Não guarda nada em cache.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
