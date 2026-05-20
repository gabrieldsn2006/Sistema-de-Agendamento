// src/pages/medicos.js — Lógica completa da tela de Médicos
import { Modal } from 'bootstrap'
import api from '../api/api.js'
import { showToast } from '../utils/toast.js'

// ── Estado ───────────────────────────────────────────────────────────────────
let allDoctors  = []
let editingId   = null
let deletingId  = null
let formModal   = null
let confirmModal = null

// ── Inicialização ─────────────────────────────────────────────────────────────
export function initMedicos() {
  formModal    = new Modal(document.getElementById('formModal'))
  confirmModal = new Modal(document.getElementById('confirmModal'))

  document.getElementById('btn-novo').addEventListener('click', openCreateModal)
  document.getElementById('btn-refresh').addEventListener('click', loadDoctors)
  document.getElementById('submit-btn').addEventListener('click', submitForm)
  document.getElementById('confirm-delete-btn').addEventListener('click', confirmDelete)
  document.getElementById('search').addEventListener('input', filterTable)

  loadDoctors()
}

// ── API ───────────────────────────────────────────────────────────────────────
async function loadDoctors() {
  setTableLoading()
  try {
    const { data } = await api.get('/doctors/', { params: { limit: 500 } })
    allDoctors = data
    renderTable(allDoctors)
    updateStats(allDoctors)
  } catch {
    setTableError()
    showToast('Erro ao conectar na API. Backend está rodando?', 'error')
  }
}

async function submitForm() {
  const form = document.getElementById('doctor-form')
  if (!form.checkValidity()) { form.reportValidity(); return }

  const btn = document.getElementById('submit-btn')
  btn.disabled = true
  btn.textContent = 'Salvando…'

  const payload = {
    name:      document.getElementById('f-name').value.trim(),
    crm:       document.getElementById('f-crm').value.trim(),
    specialty: document.getElementById('f-specialty').value.trim(),
    phone:     document.getElementById('f-phone').value.trim(),
    email:     document.getElementById('f-email').value.trim() || null,
  }

  try {
    if (editingId) {
      // CRM não pode ser atualizado
      const { crm, ...updatePayload } = payload
      await api.put(`/doctors/${editingId}`, updatePayload)
      showToast('Médico atualizado com sucesso!', 'success')
    } else {
      await api.post('/doctors/', payload)
      showToast('Médico cadastrado com sucesso!', 'success')
    }
    formModal.hide()
    loadDoctors()
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 409) showToast('CRM já cadastrado.', 'error')
    else if (status === 422) showToast('Dados inválidos. Verifique os campos.', 'error')
    else showToast(detail || 'Erro ao salvar médico.', 'error')
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
    await api.delete(`/doctors/${deletingId}`)
    showToast('Médico removido.', 'success')
    confirmModal.hide()
    loadDoctors()
  } catch {
    showToast('Erro ao remover médico.', 'error')
  } finally {
    btn.disabled = false
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderTable(doctors) {
  const tbody = document.getElementById('doctors-tbody')

  if (!doctors.length) {
    tbody.innerHTML = `
      <tr><td colspan="7">
        <div class="empty-state">
          <div class="icon">🩺</div>
          <div>Nenhum médico encontrado</div>
        </div>
      </td></tr>`
    return
  }

  tbody.innerHTML = doctors.map(d => `
    <tr style="background: var(--bg);">
      <td style="background: var(--bg);"><span class="badge-id">#${d.id}</span></td>
      <td style="background: var(--bg);"><strong>${escHtml(d.name)}</strong></td>
      <td class="cpf-cell" style="background: var(--bg);">${escHtml(d.crm)}</td>
      <td style="background: var(--bg);"><span class="badge-specialty">${escHtml(d.specialty)}</span></td>
      <td style="background: var(--bg);">${escHtml(d.phone)}</td>
      <td class="text-muted" style="background: var(--bg);">${escHtml(d.email || '—')}</td>
      <td style="background: var(--bg);">
        <div class="d-flex gap-1">
          <button class="btn-edit" data-id="${d.id}">✏️ Editar</button>
          <button class="btn-danger-custom" data-del-id="${d.id}" data-del-name="${escAttr(d.name)}">🗑️</button>
        </div>
      </td>
    </tr>`).join('')

  tbody.querySelectorAll('.btn-edit').forEach(btn =>
    btn.addEventListener('click', () => openEditModal(Number(btn.dataset.id)))
  )
  tbody.querySelectorAll('.btn-danger-custom').forEach(btn =>
    btn.addEventListener('click', () => openDeleteModal(Number(btn.dataset.delId), btn.dataset.delName))
  )
}

function updateStats(doctors) {
  document.getElementById('stat-total').textContent = doctors.length
  const last = doctors.at(-1)
  document.getElementById('stat-last').textContent = last ? last.name : '—'
  // Conta especialidades únicas
  const specs = new Set(doctors.map(d => d.specialty)).size
  document.getElementById('stat-specs').textContent = specs || '—'
}

function filterTable() {
  const q = document.getElementById('search').value.toLowerCase()
  renderTable(allDoctors.filter(d =>
    d.name.toLowerCase().includes(q) ||
    d.crm.toLowerCase().includes(q) ||
    d.specialty.toLowerCase().includes(q)
  ))
}

function setTableLoading() {
  document.getElementById('doctors-tbody').innerHTML = `
    <tr><td colspan="7" class="text-center py-4 text-muted">
      <div class="spinner-border spinner-border-sm text-accent me-2"></div>
      Carregando médicos…
    </td></tr>`
}

function setTableError() {
  document.getElementById('doctors-tbody').innerHTML = `
    <tr><td colspan="7" class="text-center py-4 text-muted">
      ⚠️ Não foi possível conectar ao servidor em <strong>localhost:8000</strong>
    </td></tr>`
}

// ── Modais ────────────────────────────────────────────────────────────────────
function openCreateModal() {
  editingId = null
  document.getElementById('modal-title').textContent = 'Novo Médico'
  document.getElementById('doctor-form').reset()
  document.getElementById('f-crm').disabled = false
  formModal.show()
}

function openEditModal(id) {
  const d = allDoctors.find(x => x.id === id)
  if (!d) return
  editingId = id
  document.getElementById('modal-title').textContent = 'Editar Médico'
  document.getElementById('f-name').value      = d.name
  document.getElementById('f-crm').value       = d.crm
  document.getElementById('f-crm').disabled    = true   // CRM não editável
  document.getElementById('f-specialty').value = d.specialty
  document.getElementById('f-phone').value     = d.phone
  document.getElementById('f-email').value     = d.email || ''
  formModal.show()
}

function openDeleteModal(id, name) {
  deletingId = id
  document.getElementById('confirm-name').textContent = name
  confirmModal.show()
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
function escAttr(s) {
  return String(s ?? '').replace(/'/g, '&#39;').replace(/"/g, '&quot;')
}