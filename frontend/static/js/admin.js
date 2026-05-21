/**
 * ResumeIQ — admin.js
 * Loads stats + paginated resume table for the admin dashboard.
 */

'use strict';

let currentPage = 1;

/* ── On load ───────────────────────────────────────────────────────────────── */
(async () => {
  await loadStats();
  await loadResumes(1);
})();

/* ── Stats ─────────────────────────────────────────────────────────────────── */
async function loadStats() {
  try {
    const res  = await fetch('/admin/stats');
    const data = await res.json();

    document.getElementById('statTotal').textContent = data.total_resumes ?? '—';
    document.getElementById('statAvg').textContent   = data.avg_score    ?? '—';
    document.getElementById('statMax').textContent   = data.max_score    ?? '—';
    document.getElementById('statMin').textContent   = data.min_score    ?? '—';

    renderGrades(data.grade_distribution || {});
  } catch (e) {
    console.error('Stats load error:', e);
  }
}

function renderGrades(dist) {
  const container = document.getElementById('gradeDist');
  const grades    = ['A','B','C','D','F'];
  const max       = Math.max(1, ...Object.values(dist));

  container.innerHTML = grades.map(g => {
    const count  = dist[g] || 0;
    const height = Math.max(4, (count / max) * 70);
    return `
      <div class="grade-col">
        <div class="grade-bar" style="height:${height}px"></div>
        <span class="grade-col-label">${g} (${count})</span>
      </div>`;
  }).join('');
}

/* ── Table ─────────────────────────────────────────────────────────────────── */
async function loadResumes(page = 1) {
  currentPage = page;
  try {
    const res  = await fetch(`/admin/resumes?page=${page}&per_page=15`);
    const data = await res.json();

    renderTable(data.items || []);
    renderPagination(data.pages || 1, page);
  } catch (e) {
    console.error('Resumes load error:', e);
  }
}

function renderTable(items) {
  const tbody = document.getElementById('resumeTableBody');
  if (!items.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:2rem">No analyses yet. Upload a resume to get started.</td></tr>';
    return;
  }

  tbody.innerHTML = items.map((r, i) => `
    <tr>
      <td style="color:var(--muted)">${r.id}</td>
      <td>${r.filename}</td>
      <td>
        <span style="font-family:var(--font-head);font-weight:700;color:${scoreColor(r.ats_score)}">
          ${r.ats_score ?? '—'}
        </span>
      </td>
      <td><span class="grade-badge grade-${r.ats_grade || 'F'}" style="font-size:.78rem;padding:.15rem .55rem">${r.ats_grade || '—'}</span></td>
      <td>${r.word_count ?? '—'}</td>
      <td>${formatDate(r.upload_time)}</td>
      <td>
        <button class="del-btn" onclick="deleteResume(${r.id})">Delete</button>
      </td>
    </tr>
  `).join('');
}

function renderPagination(totalPages, current) {
  const container = document.getElementById('pagination');
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  let html = '';
  for (let p = 1; p <= totalPages; p++) {
    html += `<button class="page-btn${p === current ? ' active' : ''}" onclick="loadResumes(${p})">${p}</button>`;
  }
  container.innerHTML = html;
}

/* ── Delete ─────────────────────────────────────────────────────────────────── */
async function deleteResume(id) {
  if (!confirm(`Delete analysis #${id}?`)) return;
  try {
    await fetch(`/admin/resumes/${id}`, { method: 'DELETE' });
    await loadResumes(currentPage);
    await loadStats();
  } catch (e) {
    alert('Delete failed: ' + e.message);
  }
}

/* ── Helpers ───────────────────────────────────────────────────────────────── */
function scoreColor(score) {
  if (score >= 85) return '#c8f53e';
  if (score >= 70) return '#5b8fff';
  if (score >= 55) return '#ffb932';
  if (score >= 40) return '#ff8232';
  return '#ff5f5f';
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}
