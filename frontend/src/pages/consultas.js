// src/pages/consultas.js — Lógica completa da tela de Consultas
import { Modal } from 'bootstrap'
import api from '../api/api.js'
import { showToast } from '../utils/toast.js'

// ── Estado ───────────────────────────────────────────────────────────────────
let allAppointments = []
let editingId       = null
let deletingId      = null
let formModal       = null
let confirmModal    = null

// ── Status config ─────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  scheduled: { label: 'Agendada',  color: '#3b82f6', bg: 'rgba(59,130,246,.15)'  },
  completed:  { label: 'Concluída', color: '#22c55e', bg: 'rgba(34,197,94,.15)'   },
  cancelled:  { label: 'Cancelada', color: '#ef4444', bg: 'rgba(239,68,68,.15)'   },
}

// ── Inicialização ─────────────────────────────────────────────────────────────
export async function initConsultas() {
  formModal    = new Modal(document.getElementById('formModal'))
  confirmModal = new Modal(document.getElementById('confirmModal'))

  document.getElementById('btn-novo').addEventListener('click', openCreateModal)
  document.getElementById('btn-refresh').addEventListener('click', loadAppointments)
  document.getElementById('submit-btn').addEventListener('click', submitForm)
  document.getElementById('confirm-delete-btn').addEventListener('click', confirmDelete)
  document.getElementById('search').addEventListener('input', applyFilters)
  document.getElementById('filter-status').addEventListener('change', applyFilters)

  // Carrega pacientes, médicos e consultas em paralelo
  await Promise.all([loadSelects(), loadAppointments()])
}

// ── Carrega selects de pacientes e médicos ────────────────────────────────────
async function loadSelects() {
  try {
    const [{ data: patients }, { data: doctors }] = await Promise.all([
      api.get('/patients/', { params: { limit: 500 } }),
      api.get('/doctors/',  { params: { limit: 500 } }),
    ])

    const patSel = document.getElementById('f-patient')
    const docSel = document.getElementById('f-doctor')

    patients.forEach(p => {
      patSel.innerHTML += `<option value="${p.id}">${escHtml(p.name)} — ${escHtml(p.cpf)}</option>`
    })

    doctors.forEach(d => {
      docSel.innerHTML += `<option value="${d.id}">${escHtml(d.name)} — ${escHtml(d.specialty)}</option>`
    })
  } catch {
    showToast('Erro ao carregar pacientes/médicos para o formulário.', 'error')
  }
}

// ── API ───────────────────────────────────────────────────────────────────────
async function loadAppointments() {
  setTableLoading()
  try {
    const { data } = await api.get('/appointments/', { params: { limit: 500 } })
    allAppointments = data
    applyFilters()
    updateStats(allAppointments)
  } catch {
    setTableError()
    showToast('Erro ao conectar na API. Backend está rodando?', 'error')
  }
}

async function submitForm() {
  const form = document.getElementById('appointment-form')
  if (!form.checkValidity()) { form.reportValidity(); return }

  const btn = document.getElementById('submit-btn')
  btn.disabled = true
  btn.textContent = 'Salvando…'

  const date = document.getElementById('f-date').value
  const time = document.getElementById('f-time').value
  // Monta datetime com offset local do navegador
  const localDt  = new Date(`${date}T${time}:00`)
  const offset   = -localDt.getTimezoneOffset()
  const sign     = offset >= 0 ? '+' : '-'
  const pad      = n => String(Math.abs(n)).padStart(2, '0')
  const tzOffset = `${sign}${pad(Math.floor(Math.abs(offset) / 60))}:${pad(Math.abs(offset) % 60)}`
  const scheduledAt = `${date}T${time}:00${tzOffset}`

  try {
    if (editingId) {
      const payload = {
        scheduled_at: scheduledAt,
        notes:  document.getElementById('f-notes').value.trim() || null,
        status: document.getElementById('f-status').value,
      }
      await api.put(`/appointments/${editingId}`, payload)
      showToast('Consulta atualizada com sucesso!', 'success')
    } else {
      const payload = {
        patient_id:   Number(document.getElementById('f-patient').value),
        doctor_id:    Number(document.getElementById('f-doctor').value),
        scheduled_at: scheduledAt,
        notes:        document.getElementById('f-notes').value.trim() || null,
      }
      await api.post('/appointments/', payload)
      showToast('Consulta agendada com sucesso!', 'success')
    }
    formModal.hide()
    loadAppointments()
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 409) showToast(detail || 'Conflito de horário detectado.', 'error')
    else if (status === 404) showToast(detail || 'Paciente ou médico não encontrado.', 'error')
    else if (status === 422) showToast('Dados inválidos. Verifique os campos.', 'error')
    else showToast(detail || 'Erro ao salvar consulta.', 'error')
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
    await api.delete(`/appointments/${deletingId}`)
    showToast('Consulta removida.', 'success')
    confirmModal.hide()
    loadAppointments()
  } catch {
    showToast('Erro ao remover consulta.', 'error')
  } finally {
    btn.disabled = false
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderTable(appointments) {
  const tbody = document.getElementById('appointments-tbody')

  if (!appointments.length) {
    tbody.innerHTML = `
      <tr><td colspan="8">
        <div class="empty-state">
          <div class="icon">📅</div>
          <div>Nenhuma consulta encontrada</div>
        </div>
      </td></tr>`
    return
  }

  tbody.innerHTML = appointments.map(a => {
    const cfg = STATUS_CONFIG[a.status] || STATUS_CONFIG.scheduled
    const dt  = formatDatetime(a.scheduled_at)
    return `
      <tr>
        <td><span class="badge-id">#${a.id}</span></td>
        <td><strong>${escHtml(a.patient.name)}</strong></td>
        <td>${escHtml(a.doctor.name)}</td>
        <td><span class="badge-specialty">${escHtml(a.doctor.specialty)}</span></td>
        <td>
          <div style="font-weight:600">${dt.date}</div>
          <div style="font-size:.8rem;color:var(--muted)">${dt.time}</div>
        </td>
        <td>
          <span class="badge-status" style="background:${cfg.bg};color:${cfg.color}">
            ${cfg.label}
          </span>
        </td>
        <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-size:.82rem">
          ${escHtml(a.notes || '—')}
        </td>
        <td>
          <div class="d-flex gap-1">
            <button class="btn-edit" data-id="${a.id}">✏️ Editar</button>
            <button class="btn-danger-custom" data-del-id="${a.id}">🗑️</button>
          </div>
        </td>
      </tr>`
  }).join('')

  tbody.querySelectorAll('.btn-edit').forEach(btn =>
    btn.addEventListener('click', () => openEditModal(Number(btn.dataset.id)))
  )
  tbody.querySelectorAll('.btn-danger-custom').forEach(btn =>
    btn.addEventListener('click', () => openDeleteModal(Number(btn.dataset.delId)))
  )
}

function updateStats(appointments) {
  document.getElementById('stat-total').textContent     = appointments.length
  document.getElementById('stat-scheduled').textContent = appointments.filter(a => a.status === 'scheduled').length
  document.getElementById('stat-completed').textContent = appointments.filter(a => a.status === 'completed').length
  document.getElementById('stat-cancelled').textContent = appointments.filter(a => a.status === 'cancelled').length
}

function applyFilters() {
  const q      = document.getElementById('search').value.toLowerCase()
  const status = document.getElementById('filter-status').value

  const filtered = allAppointments.filter(a => {
    const matchText = !q ||
      a.patient.name.toLowerCase().includes(q) ||
      a.doctor.name.toLowerCase().includes(q) ||
      a.doctor.specialty.toLowerCase().includes(q)
    const matchStatus = !status || a.status === status
    return matchText && matchStatus
  })

  renderTable(filtered)
}

function setTableLoading() {
  document.getElementById('appointments-tbody').innerHTML = `
    <tr><td colspan="8" class="text-center py-4 text-muted">
      <div class="spinner-border spinner-border-sm text-accent me-2"></div>
      Carregando consultas…
    </td></tr>`
}

function setTableError() {
  document.getElementById('appointments-tbody').innerHTML = `
    <tr><td colspan="8" class="text-center py-4 text-muted">
      ⚠️ Não foi possível conectar ao servidor em <strong>localhost:8000</strong>
    </td></tr>`
}

// ── Modais ────────────────────────────────────────────────────────────────────
function openCreateModal() {
  editingId = null
  document.getElementById('modal-title').textContent = 'Nova Consulta'
  document.getElementById('appointment-form').reset()
  document.getElementById('status-group').classList.add('d-none')
  // Selects habilitados na criação
  document.getElementById('f-patient').disabled = false
  document.getElementById('f-doctor').disabled  = false
  formModal.show()
}

function openEditModal(id) {
  const a = allAppointments.find(x => x.id === id)
  if (!a) return
  editingId = id
  document.getElementById('modal-title').textContent = 'Editar Consulta'

  // Paciente e médico não podem ser trocados na edição
  document.getElementById('f-patient').value    = a.patient_id
  document.getElementById('f-patient').disabled = true
  document.getElementById('f-doctor').value     = a.doctor_id
  document.getElementById('f-doctor').disabled  = true

  // Data e hora separadas
  const dt = new Date(a.scheduled_at)
  document.getElementById('f-date').value   = dt.toISOString().slice(0, 10)
  document.getElementById('f-time').value   = dt.toTimeString().slice(0, 5)
  document.getElementById('f-notes').value  = a.notes || ''
  document.getElementById('f-status').value = a.status

  // Mostra campo de status só na edição
  document.getElementById('status-group').classList.remove('d-none')
  formModal.show()
}

function openDeleteModal(id) {
  const a = allAppointments.find(x => x.id === id)
  deletingId = id
  document.getElementById('confirm-label').textContent =
    a ? `${a.patient.name} com ${a.doctor.name}` : `Consulta #${id}`
  confirmModal.show()
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function formatDatetime(isoStr) {
  if (!isoStr) return { date: '—', time: '—' }
  const dt = new Date(isoStr)
  return {
    date: dt.toLocaleDateString('pt-BR'),
    time: dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
  }
}

function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
