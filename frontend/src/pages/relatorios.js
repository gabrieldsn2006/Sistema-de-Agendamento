// src/pages/relatorios.js — Lógica completa da tela de Relatórios
import { Modal } from 'bootstrap'
import api from '../api/api.js'
import { showToast } from '../utils/toast.js'

const API_BASE = 'http://localhost:8000'

let pdfModal = null

// ── Inicialização ─────────────────────────────────────────────────────────────
export async function initRelatorios() {
  pdfModal = new Modal(document.getElementById('pdfModal'))

  // Expõe funções para o HTML (onclick inline)
  window.generateCSV  = generateCSV
  window.openPdfModal = openPdfModal
  window.generatePDF  = generatePDF
  window.loadFiles    = loadFiles

  await Promise.all([loadDoctorSelect(), loadFiles()])
}

// ── Carrega select de médicos ─────────────────────────────────────────────────
async function loadDoctorSelect() {
  try {
    const { data } = await api.get('/doctors/', { params: { limit: 500 } })
    const sel = document.getElementById('f-doctor-pdf')
    sel.innerHTML = '<option value="">Selecione o médico…</option>'
    data.forEach(d => {
      sel.innerHTML += `<option value="${d.id}">${escHtml(d.name)} — ${escHtml(d.specialty)}</option>`
    })
  } catch {
    showToast('Erro ao carregar médicos.', 'error')
  }
}

// ── Gerar CSV ─────────────────────────────────────────────────────────────────
async function generateCSV() {
  const btn      = document.getElementById('btn-csv')
  const progress = document.getElementById('csv-progress')
  const msg      = document.getElementById('csv-progress-msg')

  btn.disabled = true
  progress.classList.remove('d-none')
  msg.textContent = 'Enfileirando tarefa…'

  try {
    const { data } = await api.post('/reports/csv')
    const taskId = data.task_id
    msg.textContent = `Gerando CSV (task: ${taskId})…`
    showToast('CSV iniciado! Aguarde…', 'info')

    // Polling até concluir
    const result = await pollTask(taskId, (attempt) => {
      msg.textContent = `Gerando CSV… (tentativa ${attempt})`
    })

    if (result.status === 'ok') {
      const downloadUrl = `${API_BASE}${result.download_url}`
      msg.textContent = `✓ CSV gerado! ${result.registros} registros.`
      showToast(`CSV gerado com ${result.registros} registros!`, 'success')
      triggerDownload(downloadUrl, result.arquivo?.split(/[\\/]/).pop())
      loadFiles()
    } else {
      msg.textContent = `Erro: ${result.erro}`
      showToast('Erro ao gerar CSV.', 'error')
    }
  } catch (err) {
    msg.textContent = 'Erro ao conectar na API.'
    showToast('Erro ao gerar CSV.', 'error')
  } finally {
    btn.disabled = false
    setTimeout(() => progress.classList.add('d-none'), 4000)
  }
}

// ── Gerar PDF ─────────────────────────────────────────────────────────────────
function openPdfModal() {
  pdfModal.show()
}

async function generatePDF() {
  const doctorId = document.getElementById('f-doctor-pdf').value
  if (!doctorId) { showToast('Selecione um médico.', 'error'); return }

  const btn      = document.getElementById('submit-pdf-btn')
  const progress = document.getElementById('pdf-progress')
  const msg      = document.getElementById('pdf-progress-msg')

  btn.disabled = true
  pdfModal.hide()
  progress.classList.remove('d-none')
  msg.textContent = 'Enfileirando tarefa…'

  try {
    const { data } = await api.post(`/reports/pdf/doctor/${doctorId}`)
    const taskId = data.task_id
    msg.textContent = `Gerando PDF (task: ${taskId})…`
    showToast('PDF iniciado! Aguarde…', 'info')

    const result = await pollTask(taskId, (attempt) => {
      msg.textContent = `Gerando PDF… (tentativa ${attempt})`
    })

    if (result.status === 'ok') {
      const downloadUrl = `${API_BASE}${result.download_url}`
      msg.textContent = `✓ PDF gerado! Médico: ${result.medico}, ${result.consultas} consulta(s).`
      showToast(`PDF de ${result.medico} gerado!`, 'success')
      triggerDownload(downloadUrl, result.arquivo?.split(/[\\/]/).pop())
      loadFiles()
    } else {
      msg.textContent = `Erro: ${result.erro}`
      showToast('Erro ao gerar PDF.', 'error')
    }
  } catch {
    msg.textContent = 'Erro ao conectar na API.'
    showToast('Erro ao gerar PDF.', 'error')
  } finally {
    btn.disabled = false
    setTimeout(() => progress.classList.add('d-none'), 5000)
  }
}

// ── Polling de task ───────────────────────────────────────────────────────────
async function pollTask(taskId, onAttempt, maxAttempts = 20, intervalMs = 800) {
  for (let i = 1; i <= maxAttempts; i++) {
    onAttempt(i)
    await sleep(intervalMs)
    const { data } = await api.get(`/reports/task/${taskId}`)
    if (data.status === 'done') return data.result
  }
  throw new Error('Timeout ao aguardar geração do relatório.')
}

// ── Lista arquivos gerados ────────────────────────────────────────────────────
async function loadFiles() {
  const tbody = document.getElementById('files-tbody')
  tbody.innerHTML = `
    <tr><td colspan="5" class="text-center py-4 text-muted">
      <div class="spinner-border spinner-border-sm text-accent me-2"></div>
      Carregando arquivos…
    </td></tr>`

  try {
    const { data } = await api.get('/reports/list')
    const files = data.arquivos

    if (!files.length) {
      tbody.innerHTML = `
        <tr><td colspan="5">
          <div class="empty-state">
            <div class="icon">📁</div>
            <div>Nenhum relatório gerado ainda</div>
          </div>
        </td></tr>`
      return
    }

    tbody.innerHTML = files.map(f => {
      const isPdf = f.tipo === 'PDF'
      const icon  = isPdf ? '📄' : '📊'
      const color = isPdf ? '#ef4444' : '#22c55e'
      const date  = new Date(f.criado_em * 1000).toLocaleString('pt-BR')
      const downloadUrl = `${API_BASE}${f.download_url}`

      return `
        <tr style="background: var(--bg);">
          <td style="background: var(--bg);">
            <div class="d-flex align-items-center gap-2">
              <span style="font-size:1.2rem">${icon}</span>
              <span style="font-size:.82rem;font-family:monospace;color:var(--muted)">${escHtml(f.nome)}</span>
            </div>
          </td>
          <td style="background: var(--bg);">
            <span class="badge-status" style="background:${isPdf ? 'rgba(239,68,68,.15)' : 'rgba(34,197,94,.15)'};color:${color}">
              ${f.tipo}
            </span>
          </td>
          <td style="background: var(--bg); color:var(--muted);font-size:.875rem">${f.tamanho_kb} KB</td>
          <td style="background: var(--bg); color:var(--muted);font-size:.82rem">${date}</td>
          <td style="background: var(--bg);">
            <a href="${downloadUrl}" target="_blank" download="${escHtml(f.nome)}"
               class="btn-edit" style="text-decoration:none">
              ⬇️ Baixar
            </a>
          </td>
        </tr>`
    }).join('')
  } catch {
    tbody.innerHTML = `
      <tr><td colspan="5" class="text-center py-4 text-muted">
        ⚠️ Não foi possível conectar ao servidor em <strong>localhost:8000</strong>
      </td></tr>`
  }
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function triggerDownload(url, filename) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'relatorio'
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}