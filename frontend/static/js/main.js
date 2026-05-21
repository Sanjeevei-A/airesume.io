/**
 * ResumeIQ — main.js
 * Handles: drag-and-drop upload, form submission, results rendering, AI call.
 */

'use strict';

/* ── DOM refs ──────────────────────────────────────────────────────────────── */
const uploadForm = document.getElementById('uploadForm');
const fileInput  = document.getElementById('fileInput');
const dropzone   = document.getElementById('dropzone');
const fileName   = document.getElementById('fileName');
const submitBtn  = document.getElementById('submitBtn');
const btnText    = submitBtn.querySelector('.btn-text');
const btnLoader  = document.getElementById('btnLoader');
const results    = document.getElementById('results');
const errorBox   = document.getElementById('errorBox');
const aiBtn      = document.getElementById('aiBtn');
const aiCard     = document.getElementById('aiCard');
const aiContent  = document.getElementById('aiContent');

/* Cache last analysis for AI call */
let _lastResumeText = '';
let _lastScore      = 0;
let _lastProvider   = 'gemini';

/* ── Drag-and-drop ─────────────────────────────────────────────────────────── */
['dragenter','dragover'].forEach(e =>
  dropzone.addEventListener(e, ev => { ev.preventDefault(); dropzone.classList.add('dragover'); })
);
['dragleave','drop'].forEach(e =>
  dropzone.addEventListener(e, () => dropzone.classList.remove('dragover'))
);
dropzone.addEventListener('drop', ev => {
  ev.preventDefault();
  const file = ev.dataTransfer.files[0];
  if (file) _setFile(file);
});
dropzone.addEventListener('click', e => {
  if (e.target.tagName !== 'LABEL' && e.target.tagName !== 'INPUT') fileInput.click();
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) _setFile(fileInput.files[0]);
});

function _setFile(file) {
  // Attach to the hidden input via DataTransfer
  const dt = new DataTransfer();
  dt.items.add(file);
  fileInput.files = dt.files;
  fileName.textContent = `✓ ${file.name}`;
}

/* ── Form submit ───────────────────────────────────────────────────────────── */
uploadForm.addEventListener('submit', async e => {
  e.preventDefault();
  _setLoading(true);
  _hideError();
  results.classList.add('hidden');

  const formData = new FormData(uploadForm);
  _lastProvider = document.querySelector('input[name="provider"]:checked')?.value || 'gemini';

  try {
    const res = await fetch('/resume/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);

    _renderResults(data);
    _lastScore = data.ats_score;
    // We don't get raw text back from the API — store JD for re-use in AI call
  } catch (err) {
    _showError(err.message);
  } finally {
    _setLoading(false);
  }
});

/* ── Render results ────────────────────────────────────────────────────────── */
function _renderResults(data) {
  results.classList.remove('hidden');
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  /* Score ring */
  const score   = data.ats_score ?? 0;
  const circumf = 327; // 2π × 52
  const offset  = circumf - (circumf * score / 100);
  document.getElementById('scoreNum').textContent = Math.round(score);
  document.getElementById('scoreArc').style.strokeDashoffset = offset;

  const grade = data.ats_grade || '—';
  const gradeEl = document.getElementById('scoreGrade');
  gradeEl.textContent = `Grade ${grade}`;
  gradeEl.className = `grade-badge grade-${grade}`;

  document.getElementById('scoreSummary').textContent =
    `${data.word_count ?? '?'} words · ${data.sentence_count ?? '?'} sentences`;

  /* Component bars */
  const comps = data.ats_components || {};
  const compLabels = {
    skills_match:       'Skills Match',
    keyword_density:    'Keyword Density',
    formatting:         'Formatting',
    experience_quality: 'Experience Quality',
  };
  const compContainer = document.getElementById('components');
  compContainer.innerHTML = Object.entries(comps).map(([key, val]) => `
    <div class="comp-item">
      <div class="comp-label">${compLabels[key] || key}</div>
      <div class="comp-row">
        <div class="comp-bar"><div class="comp-fill" style="width:${val}%"></div></div>
        <div class="comp-val">${Math.round(val)}</div>
      </div>
    </div>
  `).join('');

  /* Skills */
  _renderTags('skillsCloud',  data.skills || [],          'tag-green');
  _renderTags('missingCloud', data.missing_keywords || [], 'tag-red');

  /* Job recommendations */
  const jobList = document.getElementById('jobList');
  jobList.innerHTML = (data.job_recommendations || []).map(j => `
    <div class="job-item">
      <span class="job-role">${j.role}</span>
      <div class="job-bar-wrap">
        <div class="job-bar"><div class="job-fill" style="width:${j.match_pct}%"></div></div>
      </div>
      <span class="job-pct">${j.match_pct}%</span>
    </div>
  `).join('');

  /* Tips */
  const tipsList = document.getElementById('tipsList');
  const tips = data.suggestions || [];
  tipsList.innerHTML = tips.length
    ? tips.map(t => `<li>${t}</li>`).join('')
    : '<li>No major issues found — great resume!</li>';

  /* AI button */
  aiCard.classList.add('hidden');
  aiBtn.classList.remove('hidden');
}

function _renderTags(containerId, items, cls) {
  const el = document.getElementById(containerId);
  el.innerHTML = items.length
    ? items.map(i => `<span class="tag ${cls}">${i}</span>`).join('')
    : `<span class="tag" style="color:var(--muted)">—</span>`;
}

/* ── AI suggestions ────────────────────────────────────────────────────────── */
aiBtn.addEventListener('click', async () => {
  aiCard.classList.remove('hidden');
  aiBtn.classList.add('hidden');
  aiContent.innerHTML = '<p class="ai-loading">🤖 Fetching AI suggestions…</p>';

  const resumeText = document.getElementById('jdInput').value; // use JD as proxy hint
  const jd         = document.getElementById('jdInput').value;

  try {
    const res = await fetch('/api/ai-suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_text:     resumeText || 'Resume text not available in this session.',
        job_description: jd,
        ats_score:       _lastScore,
        provider:        _lastProvider,
      }),
    });
    const data = await res.json();

    if (data.error) {
      aiContent.innerHTML = `<p class="ai-loading" style="color:var(--danger)">${data.overall_feedback || data.error}</p>`;
      return;
    }
    _renderAI(data);
  } catch (err) {
    aiContent.innerHTML = `<p class="ai-loading" style="color:var(--danger)">Error: ${err.message}</p>`;
  }
});

function _renderAI(data) {
  const strengths = (data.top_strengths || []).map(s => `<li>${s}</li>`).join('');
  const improvements = (data.critical_improvements || []).map(i =>
    `<li><strong>${i.issue}</strong> — ${i.fix}${i.example ? ` <em>(e.g. "${i.example}")</em>` : ''}</li>`
  ).join('');
  const tips = (data.ats_tips || []).map(t => `<li>${t}</li>`).join('');

  aiContent.innerHTML = `
    <p class="ai-feedback">${data.overall_feedback || ''}</p>
    ${strengths ? `<p class="ai-section-title">Strengths</p><ul class="ai-list">${strengths}</ul>` : ''}
    ${improvements ? `<p class="ai-section-title">Critical Improvements</p><ul class="ai-list">${improvements}</ul>` : ''}
    ${tips ? `<p class="ai-section-title">ATS Tips</p><ul class="ai-list">${tips}</ul>` : ''}
  `;
}

/* ── Helpers ───────────────────────────────────────────────────────────────── */
function _setLoading(on) {
  submitBtn.disabled = on;
  btnText.classList.toggle('hidden', on);
  btnLoader.classList.toggle('hidden', !on);
}
function _showError(msg) { errorBox.textContent = `Error: ${msg}`; errorBox.classList.remove('hidden'); }
function _hideError()    { errorBox.classList.add('hidden'); errorBox.textContent = ''; }
