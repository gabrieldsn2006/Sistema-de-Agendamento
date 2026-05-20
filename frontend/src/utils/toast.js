// src/utils/toast.js — Helper de toast usando Bootstrap Toast
import { Toast } from 'bootstrap'

/**
 * Exibe um toast flutuante.
 * @param {string} msg  - Mensagem a exibir
 * @param {'success'|'error'|'info'} type
 */
export function showToast(msg, type = 'info') {
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'

  const el = document.createElement('div')
  el.className = `toast toast-custom toast-${type} align-items-center border-0`
  el.setAttribute('role', 'alert')
  el.setAttribute('aria-live', 'assertive')
  el.innerHTML = `
    <div class="d-flex align-items-center gap-2 px-1">
      <span>${icon}</span>
      <div class="toast-body p-0">${msg}</div>
    </div>`

  document.getElementById('toast-container').appendChild(el)

  const t = new Toast(el, { delay: 3500 })
  t.show()
  el.addEventListener('hidden.bs.toast', () => el.remove())
}