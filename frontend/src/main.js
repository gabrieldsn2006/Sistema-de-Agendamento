// src/main.js — Entry point do Vite
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './style.css'

import { initPacientes } from './pages/pacientes.js'

// Inicializa a página de pacientes (index)
initPacientes()