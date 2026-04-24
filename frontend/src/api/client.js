import axios from 'axios'

// We use the absolute URL to reach the backend directly on port 8000 from the browser.
// This bypasses the Vite proxy on port 5173.
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export default apiClient
