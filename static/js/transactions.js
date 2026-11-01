/**
 * Transactions JavaScript: Filtering, Search, Date Grouping, and Actions
 */

let searchDebounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  initFilters();
  loadTransactions();

  window.addEventListener('expenseUpdated', () => {
    loadTransactions();
  });
});

function initFilters() {
  const searchInput = document.getElementById('txSearchInput');
  const catSelect = document.getElementById('txCategorySelect');

  searchInput.addEventListener('input', () => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      loadTransactions();
    }, 250);
  });

  catSelect.addEventListener('change', () => {
    loadTransactions();
  });
}

async function loadTransactions() {
  const search = document.getElementById('txSearchInput').value.trim();
  const category = document.getElementById('txCategorySelect').value;

  const url = new URL('/api/transactions', window.location.origin);
  if (category) url.searchParams.set('category', category);
  if (search) url.searchParams.set('search', search);

  try {
    const res = await fetch(url);
    const data = await res.json();
    renderTransactions(data);
  } catch (err) {
    console.error('Error fetching transactions:', err);
  }
}

function renderTransactions(data) {
  const subtitle = document.getElementById('txSummarySubtitle');
  const container = document.getElementById('transactionsListContainer');

  subtitle.textContent = `${data.entries_count} entries • ${data.formatted_total_spent} spent`;

  const groups = data.grouped_transactions || [];
  if (groups.length === 0) {
    container.innerHTML = `
      <div class="empty-state card">
        <p style="font-size: 15px; font-weight: 500; color: var(--text-secondary);">
          No transactions match your search or filter.
        </p>
      </div>
    `;
    return;
  }

  let html = '';
  groups.forEach(group => {
    html += `
      <div class="date-group" style="margin-bottom: 24px;">
        <div class="date-group-header" style="margin-bottom: 10px;">
          <span class="date-group-title" style="font-size: 12px;">${group.date_label}</span>
          <span class="date-group-total" style="font-size: 13px;">${group.formatted_day_total}</span>
        </div>
        <div class="date-group-items">
    `;

    group.transactions.forEach(tx => {
      html += `
        <div class="tx-item" id="tx-${tx.id}">
          <div class="tx-left">
            <div class="tx-icon-box ${tx.bg_class}">
              <svg><use href="#icon-${tx.icon}"></use></svg>
            </div>
            <div class="tx-info">
              <span class="tx-note">${escapeHtml(tx.note || tx.category)}</span>
              <span class="tx-category">${escapeHtml(tx.category)}</span>
            </div>
          </div>
          <div class="tx-right">
            <span class="tx-amount">-${tx.formatted_amount}</span>
            <div class="tx-actions">
              <button type="button" class="btn-icon-action" title="Edit" onclick='openEditModal(${JSON.stringify(tx)})'>
                <svg><use href="#icon-pencil"></use></svg>
              </button>
              <button type="button" class="btn-icon-action delete" title="Delete" onclick="openDeleteModal(${tx.id})">
                <svg><use href="#icon-trash"></use></svg>
              </button>
            </div>
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
