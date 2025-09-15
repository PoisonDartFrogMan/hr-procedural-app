import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// 🔽 Firebase を読み込む
import { app, analytics } from './firebase'

const root = createRoot(document.getElementById('root'))
root.render(<App />)