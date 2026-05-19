// src/api/api.js — Instância centralizada do Axios
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 8000,
})

export default api