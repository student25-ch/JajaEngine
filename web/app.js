(() => {
  const form = document.getElementById('search-form');
  const input = document.getElementById('q');
  const meta = document.getElementById('meta');
  const list = document.getElementById('results');
  const pager = document.getElementById('pager');
  const PAGE_SIZE = 10;
  const state = { q: '', page: 1 };

  function readUrl() {
    const p = new URLSearchParams(location.search);
    state.q = p.get('q') || '';
    state.page = Math.max(1, parseInt(p.get('page') || '1', 10) || 1);
    input.value = state.q;
  }

  function writeUrl() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.page > 1) p.set('page', state.page);
    const qs = p.toString();
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
  }

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html !== undefined) n.innerHTML = html;
    return n;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[c]);
  }

  function renderEmpty(query) {
    list.innerHTML = ''; pager.innerHTML = ''; meta.textContent = '';
    const box = el('div', 'empty');
    box.innerHTML = query
      ? `没有找到与 <strong>${escapeHtml(query)}</strong> 相关的内容。<br>试试更短的关键词。`
      : '输入关键词开始搜索。';
    list.appendChild(box);
  }

  function renderResults(data) {
    list.innerHTML = ''; pager.innerHTML = '';
    if (!data.total) { renderEmpty(data.query); return; }
    const from = (data.page - 1) * data.size + 1;
    const to = Math.min(data.page * data.size, data.total);
    meta.textContent = `找到约 ${data.total} 条结果（第 ${from}–${to} 条），耗时 ${data.took_ms} ms`;
    data.results.forEach((item, i) => {
      const li = el('li', 'result');
      li.appendChild(el('h3', '', `<a href="#">${escapeHtml(item.title)}</a>`));
      li.appendChild(el('p', 'snippet', item.snippet));
      li.appendChild(el('span', 'score', `#${from + i} · 相关度 ${item.score}`));
      list.appendChild(li);
    });
    renderPager(data);
  }

  function renderPager(data) {
    const pages = Math.ceil(data.total / data.size);
    if (pages <= 1) return;
    const makeBtn = (label, page, opts = {}) => {
      const b = el('button', opts.active ? 'active' : '', label);
      b.disabled = !!opts.disabled;
      if (!opts.disabled && !opts.active) b.addEventListener('click', () => go(state.q, page));
      return b;
    };
    pager.appendChild(makeBtn('上一页', data.page - 1, { disabled: data.page <= 1 }));
    const windowSize = 5;
    let start = Math.max(1, data.page - Math.floor(windowSize / 2));
    const end = Math.min(pages, start + windowSize - 1);
    start = Math.max(1, end - windowSize + 1);
    for (let p = start; p <= end; p++)
      pager.appendChild(makeBtn(String(p), p, { active: p === data.page }));
    pager.appendChild(makeBtn('下一页', data.page + 1, { disabled: data.page >= pages }));
  }

  async function go(query, page) {
    state.q = query.trim();
    state.page = Math.max(1, page || 1);
    writeUrl();
    if (!state.q) { renderEmpty(''); return; }
    meta.textContent = '搜索中…'; list.innerHTML = '';
    try {
      const url = `/api/search?q=${encodeURIComponent(state.q)}&page=${state.page}&size=${PAGE_SIZE}`;
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      renderResults(data);
    } catch (err) {
      list.innerHTML = ''; pager.innerHTML = ''; meta.textContent = '';
      const box = el('div', 'empty');
      box.innerHTML = `请求失败：<strong>${escapeHtml(String(err.message))}</strong>`;
      list.appendChild(box);
    }
  }

  form.addEventListener('submit', (e) => { e.preventDefault(); go(input.value, 1); });
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault(); input.focus();
    }
  });

  readUrl();
  if (state.q) go(state.q, state.page);
  else { renderEmpty(''); input.focus(); }
})();
