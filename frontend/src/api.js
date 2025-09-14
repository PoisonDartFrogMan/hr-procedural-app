export async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    credentials: 'same-origin',
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function getPublicKey() {
  const { publicKey } = await fetchJSON('/api/webpush/public_key')
  return publicKey
}

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return null
  return navigator.serviceWorker.register('/sw.js')
}

export async function askNotificationPermission() {
  if (!('Notification' in window)) return 'denied'
  if (Notification.permission === 'default') {
    return Notification.requestPermission()
  }
  return Notification.permission
}

export async function subscribePush(registration, publicKey, employeeDbId = null) {
  if (!registration || !('pushManager' in registration)) return null
  if (!publicKey) return null
  const applicationServerKey = urlB64ToUint8Array(publicKey)
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey,
  })
  await fetchJSON('/api/subscriptions', {
    method: 'POST',
    body: JSON.stringify({ subscription, employee_db_id: employeeDbId }),
  })
  return subscription
}

export async function triggerUpcoming(hours = 24) {
  return fetchJSON('/api/notify/upcoming', {
    method: 'POST',
    body: JSON.stringify({ hours }),
  })
}

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

