/**
 * Dashboard JavaScript: Native SVG Charts, Dynamic Stats, Quick Log, and Recent Transactions
 */

let currentPeriod = '30D';
let selectedCategory = 'Food';

document.addEventListener('DOMContentLoaded', () => {
  initQuickLog();
  initPeriodTabs();
  loadDashboard();

  window.addEventListener('expenseUpdated', () => {
    loadDashboard();
  });
});

function initPeriodTabs() {
  const tabs = document.querySelectorAll('#periodTabs .pill-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentPeriod = tab.getAttribute('data-period');
      loadDashboard();
    });
  });
}

function initQuickLog() {
  // Category selector grid
  const catButtons = document.querySelectorAll('#categoryGrid .cat-btn');
  catButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      catButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedCategory = btn.getAttribute('data-category');
    });
  });

  // Quick Amount Pills
  const amountInput = document.getElementById('quickAmount');
  const amountPills = document.querySelectorAll('.quick-amount-pills .pill-amount');
  amountPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const val = parseFloat(pill.getAttribute('data-amount'));
      const currentVal = parseFloat(amountInput.value) || 0;
      // If current value is 0 or empty, replace with pill value; otherwise add to it
      if (currentVal === 0) {
        amountInput.value = val;
      } else {
        amountInput.value = currentVal + val;
      }
    });
  });

  // Quick Log Form Submit
  const form = document.getElementById('quickLogForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(amountInput.value);
    const note = document.getElementById('quickNote').value.trim();

    if (!amount || amount <= 0) {
      showToast('Please enter a valid amount', 'error');
      return;
    }

    const payload = {
      amount: amount,
      category: selectedCategory,
      note: note || selectedCategory,
      transaction_date: new Date().toISOString().split('T')[0]
    };

    try {
      const res = await fetch('/api/add-transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Spent ${formatINR(amount)} on ${selectedCategory}!`);
        amountInput.value = '0';
        document.getElementById('quickNote').value = '';
        loadDashboard();
      } else {
        showToast(data.error || 'Failed to log spend', 'error');
      }
    } catch (err) {
      showToast('Error connecting to server', 'error');
    }
  });
}

async function loadDashboard() {
  try {
    const res = await fetch(`/api/dashboard?period=${currentPeriod}`);
    const data = await res.json();
    renderSummaryCards(data.summary);
    renderBreakdownChart(data.breakdown);
    renderCategoryShare(data.category_share, data.summary.total_spent);
    renderRecentTransactions(data.recent_grouped, data.total_transactions_count);
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
  }
}

function renderSummaryCards(summary) {
  // Total Spent
  document.getElementById('statTotalSpent').textContent = summary.formatted_total_spent;
  const totalTrendEl = document.getElementById('statTotalTrend');
  const totalIcon = document.getElementById('statTotalTrendIcon');
  const totalVal = document.getElementById('statTotalTrendVal');
  totalVal.textContent = `${Math.abs(summary.total_change_pct).toFixed(1)}%`;
  if (summary.total_change_pct > 0) {
    totalTrendEl.className = 'trend-badge red';
    totalIcon.innerHTML = '&nearr;';
  } else {
    totalTrendEl.className = 'trend-badge green';
    totalIcon.innerHTML = '&searr;';
  }

  // Daily Average
  document.getElementById('statDailyAvg').textContent = summary.formatted_daily_avg;
  const dailyTrendEl = document.getElementById('statDailyTrend');
  const dailyIcon = document.getElementById('statDailyTrendIcon');
  const dailyVal = document.getElementById('statDailyTrendVal');
  dailyVal.textContent = `${Math.abs(summary.daily_avg_change_pct).toFixed(1)}%`;
  if (summary.daily_avg_change_pct > 0) {
    dailyTrendEl.className = 'trend-badge red';
    dailyIcon.innerHTML = '&nearr;';
  } else {
    dailyTrendEl.className = 'trend-badge green';
    dailyIcon.innerHTML = '&searr;';
  }

  // Top Category
  document.getElementById('statTopCat').textContent = summary.top_category || 'None';
  const topVal = document.getElementById('statTopTrendVal');
  topVal.textContent = `${summary.top_category_pct.toFixed(1)}%`;

  // Remaining Budget
  const remBudgetEl = document.getElementById('statRemainingBudget');
  remBudgetEl.textContent = summary.formatted_remaining_budget;
  if (summary.remaining_budget < 0) {
    remBudgetEl.style.color = 'var(--primary-red)';
  } else {
    remBudgetEl.style.color = 'var(--accent-green)';
  }
  const budgetVal = document.getElementById('statBudgetTrendVal');
  budgetVal.textContent = `${(100 - summary.budget_used_pct).toFixed(1)}%`;

  // Sparklines
  renderSparkline('sparklineSpent', summary.sparklines.spent, '#ef4444');
  renderSparkline('sparklineDaily', summary.sparklines.avg, '#3b82f6');
  renderSparkline('sparklineTop', summary.sparklines.top, '#f97316');
  renderSparkline('sparklineBudget', summary.sparklines.budget, '#10b981');
}

function renderSparkline(containerId, points, strokeColor) {
  const container = document.getElementById(containerId);
  if (!container || !points || points.length === 0) return;

  const w = 80;
  const h = 24;
  const min = Math.min(...points);
  const max = Math.max(...points) || 1;
  const range = max - min || 1;

  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * w;
    const y = h - ((p - min) / range) * (h - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${coords.join(' L ')}`;
  container.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}">
      <path d="${pathD}" fill="none" stroke="${strokeColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `;
}

/**
 * Native SVG Stacked Bar Chart with Gridlines and Tooltips
 */
function renderBreakdownChart(breakdown) {
  const svg = document.getElementById('stackedChartSvg');
  const tooltip = document.getElementById('chartTooltip');
  if (!svg || !breakdown) return;

  const width = svg.clientWidth || 640;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 35, left: 50 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Compute nice max scale
  let maxVal = breakdown.max_total || 1000;
  if (maxVal <= 0) maxVal = 1000;
  // Round up to nice number
  const roundFactor = Math.pow(10, Math.floor(Math.log10(maxVal)));
  const yMax = Math.ceil(maxVal / roundFactor) * roundFactor || 1000;

  let svgContent = '';

  // 1. Horizontal Gridlines & Y-Axis labels (4 lines)
  const gridSteps = 4;
  for (let i = 0; i <= gridSteps; i++) {
    const yVal = (yMax / gridSteps) * i;
    const yPos = padding.top + chartH - (yVal / yMax) * chartH;

    // Gridline
    svgContent += `
      <line x1="${padding.left}" y1="${yPos}" x2="${width - padding.right}" y2="${yPos}" class="chart-axis-line"/>
    `;
    // Y-Axis Label
    svgContent += `
      <text x="${padding.left - 8}" y="${yPos + 4}" text-anchor="end" class="chart-axis-text">
        ${formatCompactINR(yVal)}
      </text>
    `;
  }

  // 2. Bars rendering
  const dataPoints = breakdown.data_points || [];
  const barCount = dataPoints.length;
  if (barCount > 0) {
    const slotW = chartW / barCount;
    const barW = Math.max(4, Math.min(24, slotW * 0.65));

    dataPoints.forEach((pt, idx) => {
      const centerX = padding.left + (idx + 0.5) * slotW;
      const x = centerX - barW / 2;
      let curY = padding.top + chartH;

      const categories = pt.categories || {};
      const catKeys = Object.keys(categories);

      catKeys.forEach(cat => {
        const val = categories[cat];
        if (val > 0) {
          const segH = (val / yMax) * chartH;
          curY -= segH;
          const color = breakdown.category_colors[cat] || '#8b5cf6';

          svgContent += `
            <rect x="${x}" y="${curY}" width="${barW}" height="${segH}" rx="2" ry="2"
                  fill="${color}" class="chart-bar-segment"
                  data-label="${pt.display_label || pt.label || pt.key}"
                  data-cat="${cat}" data-val="${val}" data-total="${pt.total}"/>
          `;
        }
      });

      // X-Axis Label
      const displayLabel = pt.display_label !== undefined ? pt.display_label : pt.label;
      if (displayLabel) {
        svgContent += `
          <text x="${centerX}" y="${height - 10}" text-anchor="middle" class="chart-axis-text">
            ${displayLabel}
          </text>
        `;
      }
    });
  }

  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.innerHTML = svgContent;

  // Add Tooltip interactions
  const segments = svg.querySelectorAll('.chart-bar-segment');
  segments.forEach(seg => {
    seg.addEventListener('mouseenter', (e) => {
      const cat = seg.getAttribute('data-cat');
      const val = parseFloat(seg.getAttribute('data-val'));
      const label = seg.getAttribute('data-label');
      const total = parseFloat(seg.getAttribute('data-total'));

      tooltip.innerHTML = `<strong>${label}</strong><br/>${cat}: ${formatINR(val)}<br/>Total: ${formatINR(total)}`;
      tooltip.style.opacity = '1';
    });

    seg.addEventListener('mousemove', (e) => {
      const containerRect = svg.getBoundingClientRect();
      const x = e.clientX - containerRect.left;
      const y = e.clientY - containerRect.top;
      tooltip.style.left = `${x}px`;
      tooltip.style.top = `${y}px`;
    });

    seg.addEventListener('mouseleave', () => {
      tooltip.style.opacity = '0';
    });
  });
}

/**
 * Native SVG Donut Chart with Center Text and Legend
 */
function renderCategoryShare(categoryShare, totalSpent) {
  const svg = document.getElementById('donutChartSvg');
  const legend = document.getElementById('donutLegendContainer');
  const centerTotal = document.getElementById('donutCenterTotal');

  if (!svg || !legend) return;

  centerTotal.textContent = formatCompactINR(totalSpent);

  if (!categoryShare || categoryShare.length === 0 || totalSpent <= 0) {
    svg.innerHTML = `
      <circle cx="80" cy="80" r="54" stroke="#f1f5f9" stroke-width="24" fill="none"/>
    `;
    legend.innerHTML = `
      <div style="font-size: 13px; color: var(--text-secondary); text-align: center; padding: 20px 0;">
        No expenses recorded yet.
      </div>
    `;
    return;
  }

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  let accumulatedPct = 0;
  let circlesHtml = `
    <circle cx="80" cy="80" r="${radius}" stroke="#f1f5f9" stroke-width="24" fill="none"/>
  `;
  let legendHtml = '';

  categoryShare.forEach(item => {
    const strokeDash = (item.percentage / 100) * circumference;
    const strokeOffset = - (accumulatedPct / 100) * circumference;

    circlesHtml += `
      <circle cx="80" cy="80" r="${radius}"
              stroke="${item.color}"
              stroke-width="24"
              stroke-dasharray="${strokeDash} ${circumference}"
              stroke-dashoffset="${strokeOffset}"
              fill="none"
              style="transition: stroke-dasharray 0.5s ease;"/>
    `;
    accumulatedPct += item.percentage;

    legendHtml += `
      <div class="donut-legend-item">
        <div class="donut-legend-left">
          <div class="donut-legend-dot" style="background-color: ${item.color};"></div>
          <span>${item.category}</span>
        </div>
        <div class="donut-legend-pct">${item.percentage.toFixed(0)}%</div>
      </div>
    `;
  });

  svg.innerHTML = circlesHtml;
  legend.innerHTML = legendHtml;
}

/**
 * Render Recent Transactions Grouped by Date
 */
function renderRecentTransactions(groupedData, totalCount) {
  const container = document.getElementById('recentListContainer');
  const countEl = document.getElementById('recentEntriesCount');
  if (!container) return;

  countEl.textContent = `${totalCount} total`;

  if (!groupedData || groupedData.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No transactions yet. Start logging above!</p>
      </div>
    `;
    return;
  }

  let html = '';
  groupedData.forEach(group => {
    html += `
      <div class="date-group">
        <div class="date-group-header">
          <span class="date-group-title">${group.date_label}</span>
          <span class="date-group-total">${group.formatted_day_total}</span>
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
