/**
 * Budget JavaScript: Radial progress gauge, budget updating, presets, and category breakdown
 */

document.addEventListener('DOMContentLoaded', () => {
  initBudgetSettings();
  loadBudgetData();

  window.addEventListener('expenseUpdated', () => {
    loadBudgetData();
  });
});

function initBudgetSettings() {
  const form = document.getElementById('budgetSettingsForm');
  const input = document.getElementById('budgetLimitInput');
  const presetPills = document.querySelectorAll('.preset-pill');

  presetPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const val = pill.getAttribute('data-amount');
      input.value = val;
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const limit = parseFloat(input.value);
    if (isNaN(limit) || limit < 0) {
      showToast('Please enter a valid budget amount', 'error');
      return;
    }

    try {
      const res = await fetch('/api/update-budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monthly_limit: limit })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Monthly budget updated!');
        loadBudgetData();
      } else {
        showToast(data.error || 'Failed to update budget', 'error');
      }
    } catch (err) {
      showToast('Error connecting to server', 'error');
    }
  });
}

async function loadBudgetData() {
  try {
    const res = await fetch('/api/budget');
    const data = await res.json();
    renderBudget(data);
  } catch (err) {
    console.error('Error fetching budget data:', err);
  }
}

function renderBudget(data) {
  // 1. Stats
  document.getElementById('budgetStatSpent').textContent = data.formatted_total_spent;
  document.getElementById('budgetStatLimit').textContent = data.formatted_monthly_limit;
  document.getElementById('budgetLimitInput').value = data.monthly_limit;

  const remEl = document.getElementById('budgetStatRemaining');
  remEl.textContent = data.formatted_remaining;
  if (data.remaining < 0) {
    remEl.className = 'stat-amount red';
  } else {
    remEl.className = 'stat-amount green';
  }

  // 2. Circular Progress
  const circle = document.getElementById('budgetProgressCircle');
  const percentText = document.getElementById('budgetPercentVal');
  const pct = Math.min(100, Math.max(0, data.used_pct));
  percentText.textContent = `${Math.round(data.used_pct)}%`;

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = offset;

  if (data.used_pct > 100) {
    circle.style.stroke = 'var(--primary-red)';
  } else if (data.used_pct > 80) {
    circle.style.stroke = 'var(--accent-orange)';
  } else {
    circle.style.stroke = '#cbd5e1';
  }

  // 3. Where It Goes Breakdown
  const container = document.getElementById('whereItGoesContainer');
  const breakdown = data.categories_breakdown || [];

  if (breakdown.length === 0 || data.total_spent <= 0) {
    container.innerHTML = `
      <p style="font-size: 14px; color: var(--text-secondary); padding: 6px 0;">
        No spending recorded this month.
      </p>
    `;
    return;
  }

  let html = '<div class="where-it-goes-list">';
  breakdown.forEach(item => {
    html += `
      <div class="cat-progress-item">
        <div class="cat-progress-header">
          <div class="cat-progress-header-left">
            <div class="tx-icon-box ${item.bg_class}" style="width: 28px; height: 28px; border-radius: 6px;">
              <svg style="width: 14px; height: 14px;"><use href="#icon-${item.icon}"></use></svg>
            </div>
            <span>${item.category}</span>
          </div>
          <div class="cat-progress-header-right">
            <span>${item.formatted_total}</span>
            <span style="color: var(--text-secondary); font-size: 12px; margin-left: 6px;">(${item.percentage.toFixed(0)}%)</span>
          </div>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${item.percentage}%; background-color: ${item.color};"></div>
        </div>
      </div>
    `;
  });
  html += '</div>';

  container.innerHTML = html;
}
