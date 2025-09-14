/* global self */
self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  self.clients.claim()
})

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data.json()
  } catch (e) {
    data = { title: '通知', body: event.data && event.data.text ? event.data.text() : '' }
  }
  const title = data.title || '通知'
  const body = data.body || ''
  const options = { body, data: data.data || {} }
  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({ includeUncontrolled: true })
    const url = '/'
    if (allClients.length > 0) {
      allClients[0].focus()
    } else {
      self.clients.openWindow(url)
    }
  })())
})

