// src/pages/pacientes.js — Lógica completa da tela de Pacientes
import { Modal } from 'bootstrap'
import api from '../api/api.js'
import { showToast } from '../utils/toast.js'

// ── Estado ──────────────────────────────────────────────────────────────────
let allPatients = []
let editingId   = null
let deletingId  = null
let formModal   = null
let confirmModal = null

// ── Inicialização ────────────────────────────────────────────────────────────
export function initPacientes() {
  formModal    = new Modal(document.getElementById('formModal'))
  confirmModal = new Modal(document.getElementById('confirmModal'))

  // Botões
  document.getElementById('btn-novo').addEventListener('click', openCreateModal)
  document.getElementById('btn-refresh').addEventListener('click', loadPatients)
  document.getElementById('submit-btn').addEventListener('click', submitForm)
  document.getElementById('confirm-delete-btn').addEventListener('click', confirmDelete)
  document.getElementById('search').addEventListener('input', filterTable)

  // Máscara CPF
  document.getElementById('f-cpf').addEventListener('input', (e) => {
    e.target.value = maskCpf(e.target.value)
  })

  loadPatients()
}

// ── API ──────────────────────────────────────────────────────────────────────
async function loadPatients() {
  setTableLoading(true)
  try {
    const { data } = await api.get('/patients/', { params: { limit: 500 } })
    allPatients = data
    renderTable(allPatients)
    updateStats(allPatients)
  } catch (err) {
    setTableError()
    showToast('Erro ao conectar na API. Backend está rodando?', 'error')
  } finally {
    setTableLoading(false)
  }
}

async function submitForm() {
  const form = document.getElementById('patient-form')
  if (!form.checkValidity()) { form.reportValidity(); return }

  const btn = document.getElementById('submit-btn')
  btn.disabled = true
  btn.textContent = 'Salvando…'

  const payload = {
    name:       document.getElementById('f-name').value.trim(),
    cpf:        document.getElementById('f-cpf').value.trim(),
    phone:      document.getElementById('f-phone').value.trim(),
    email:      document.getElementById('f-email').value.trim() || null,
    birth_date: document.getElementById('f-birth').value,
  }

  try {
    if (editingId) {
      // CPF não pode ser atualizado
      const { cpf, ...updatePayload } = payload
      await api.put(`/patients/${editingId}`, updatePayload)
      showToast('Paciente atualizado com sucesso!', 'success')
    } else {
      await api.post('/patients/', payload)
      showToast('Paciente cadastrado com sucesso!', 'success')
    }
    formModal.hide()
    loadPatients()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (err.response?.status === 409) {
      showToast('CPF já cadastrado.', 'error')
    } else if (err.response?.status === 422) {
      showToast('Dados inválidos. Verifique os campos.', 'error')
    } else {
      showToast(detail || 'Erro ao salvar paciente.', 'error')
    }
  } finally {
    btn.disabled = false
    btn.textContent = 'Salvar'
  }
}

async function confirmDelete() {
  if (!deletingId) return
  const btn = document.getElementById('confirm-delete-btn')
  btn.disabled = true

  try {
    await api.delete(`/patients/${deletingId}`)
    showToast('Paciente removido.', 'success')
    confirmModal.hide()
    loadPatients()
  } catch {
    showToast('Erro ao remover paciente.', 'error')
  } finally {
    btn.disabled = false
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderTable(patients) {
  const tbody = document.getElementById('patients-tbody')

  if (!patients.length) {
    tbody.innerHTML = `
      <tr><td colspan="7">
        <div class="empty-state">
          <div class="icon">👤</div>
          <div>Nenhum paciente encontrado</div>
        </div>
      </td></tr>`
    return
  }

  tbody.innerHTML = patients.map(p => `
    <tr style="background: var(--bg);">
      <td style="background: var(--bg);"><span class="badge-id">#${p.id}</span></td>
      <td style="background: var(--bg);"><strong>${escHtml(p.name)}</strong></td>
      <td class="cpf-cell" style="background: var(--bg);"><|>${escHtml(p.cpf)}</td>
      <td style="background: var(--bg);">${escHtml(p.phone)}</td>
      <td class="text-muted" style="background: var(--bg);">${escHtml(p.email || '—')}</td>
      <td style="background: var(--bg);">${formatDate(p.birth_date)}</td>
      <td style="background: var(--bg);">
        <div class="d-flex gap-1">
          <button class="btn-edit" data-id="${p.id}">✏️ Editar</button>
          <button class="btn-danger-custom" data-del-id="${p.id}" data-del-name="${escAttr(p.name)}">🗑️</button>
        </div>
      </td>
    </tr>`).join('')

  // Eventos nos botões da tabela (delegação)
  tbody.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', () => openEditModal(Number(btn.dataset.id)))
  })
  tbody.querySelectorAll('.btn-danger-custom').forEach(btn => {
    btn.addEventListener('click', () => openDeleteModal(Number(btn.dataset.delId), btn.dataset.delName))
  })
}

function updateStats(patients) {
  document.getElementById('stat-total').textContent = patients.length
  const last = patients.at(-1)
  document.getElementById('stat-last').textContent = last ? last.name : '—'
}

function filterTable() {
  const q = document.getElementById('search').value.toLowerCase()
  renderTable(allPatients.filter(p =>
    p.name.toLowerCase().includes(q) || p.cpf.includes(q)
  ))
}

function setTableLoading(loading) {
  if (!loading) return
  document.getElementById('patients-tbody').innerHTML = `
    <tr><td colspan="7" class="text-center py-4 text-muted">
      <div class="spinner-border spinner-border-sm text-accent me-2"></div>
      Carregando pacientes…
    </td></tr>`
}

function setTableError() {
  document.getElementById('patients-tbody').innerHTML = `
    <tr><td colspan="7" class="text-center py-4 text-muted">
      ⚠️ Não foi possível conectar ao servidor em <strong>localhost:8000</strong>
    </td></tr>`
}

// ── Modais ────────────────────────────────────────────────────────────────────
function openCreateModal() {
  editingId = null
  document.getElementById('modal-title').textContent = 'Novo Paciente'
  document.getElementById('patient-form').reset()
  const cpfInput = document.getElementById('f-cpf')
  cpfInput.disabled = false
  formModal.show()
}

function openEditModal(id) {
  const p = allPatients.find(x => x.id === id)
  if (!p) return
  editingId = id
  document.getElementById('modal-title').textContent = 'Editar Paciente'
  document.getElementById('f-name').value  = p.name
  document.getElementById('f-cpf').value   = p.cpf
  document.getElementById('f-cpf').disabled = true   // CPF não editável
  document.getElementById('f-phone').value = p.phone
  document.getElementById('f-email').value = p.email || ''
  document.getElementById('f-birth').value = p.birth_date
  formModal.show()
}

function openDeleteModal(id, name) {
  deletingId = id
  document.getElementById('confirm-name').textContent = name
  confirmModal.show()
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function formatDate(str) {
  if (!str) return '—'
  const [y, m, d] = str.split('-')
  return `${d}/${m}/${y}`
}

function maskCpf(v) {
  return v.replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
}

function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
function escAttr(s) {
  return String(s ?? '').replace(/'/g, '&#39;').replace(/"/g, '&quot;')
}