const root = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const modeButtons = document.querySelectorAll('.mode-card');
const modeName = document.getElementById('modeName');
const form = document.getElementById('operationForm');
const resultBox = document.getElementById('resultBox');
const sideItems = document.querySelectorAll('.side-item');

const savedTheme = localStorage.getItem('theme') || 'light';
root.dataset.theme = savedTheme;
themeToggle.textContent = savedTheme === 'dark' ? '切换浅色' : '切换深色';

let currentMode = '自然流';
let currentResultId = null;

function setTheme(nextTheme) {
  root.dataset.theme = nextTheme;
  localStorage.setItem('theme', nextTheme);
  themeToggle.textContent = nextTheme === 'dark' ? '切换浅色' : '切换深色';
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function markdownToHtml(markdown) {
  const escaped = escapeHtml(markdown || '');
  return escaped
    .replace(/^### (.*)$/gm, '<h4>$1</h4>')
    .replace(/^## (.*)$/gm, '<h3>$1</h3>')
    .replace(/^- (.*)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.*)$/gm, '<li>$1. $2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

function setLoading(isLoading) {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = isLoading;
  button.textContent = isLoading ? '生成中...' : '生成运营执行包';
}

function renderSystemMessage(title, message) {
  resultBox.innerHTML = `
    <article class="result-card muted">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(message)}</p>
    </article>
  `;
}

function renderResult(payload) {
  currentResultId = payload.result_id || null;
  const statusText = payload.llm_status?.used_fallback ? '确定性回退结果' : 'AI 大模型结果';
  const backflowText = payload.backflow_status || 'not_stored';
  const content = markdownToHtml(payload.markdown || '暂无结果');

  resultBox.innerHTML = `
    <article class="result-card">
      <h3>${escapeHtml(payload.mode || currentMode)}｜${escapeHtml(payload.product || '未填写商品')}</h3>
      <p class="result-meta">${escapeHtml(statusText)} · 回流状态：${escapeHtml(backflowText)} · Result ID：${escapeHtml(currentResultId || '-')}</p>
      <div class="markdown-result"><p>${content}</p></div>
    </article>
    <article class="result-card">
      <h3>结果回流</h3>
      <p>点击下面按钮，记录你对本次标题、SKU、主图方向或活动建议的使用反馈。后续 VIP 私人知识库会基于这些记录持续优化。</p>
      <div class="action-row">
        <button class="small-btn" data-feedback="liked" type="button">有用 / 收藏</button>
        <button class="small-btn" data-feedback="used_title" type="button">已使用标题</button>
        <button class="small-btn" data-feedback="used_sku" type="button">已使用 SKU</button>
        <button class="small-btn" data-feedback="used_activity" type="button">已尝试活动建议</button>
        <button class="small-btn ghost" data-feedback="needs_rewrite" type="button">需要重写</button>
      </div>
      <p id="feedbackStatus" class="feedback-status">等待反馈。</p>
    </article>
  `;

  document.querySelectorAll('[data-feedback]').forEach(button => {
    button.addEventListener('click', () => sendFeedback(button.dataset.feedback));
  });
}

async function generateOperation() {
  const product = document.getElementById('productInput').value;
  const detail = document.getElementById('detailInput').value;
  const cost = document.getElementById('costInput').value;
  const price = document.getElementById('priceInput').value;
  const stock = document.getElementById('stockInput').value;

  setLoading(true);
  renderSystemMessage('正在生成', '后端正在读取输入、调用模型或回退模板，并写入结果回流记录。');

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: currentMode, product, detail, cost, price, stock })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || 'generate_failed');
    }
    renderResult(data);
  } catch (error) {
    renderSystemMessage('生成失败', `后端接口暂不可用或返回异常：${error.message}。请确认已运行 backend/server.py。`);
  } finally {
    setLoading(false);
  }
}

async function sendFeedback(action) {
  const status = document.getElementById('feedbackStatus');
  if (!currentResultId) {
    status.textContent = '没有可回流的结果，请先生成运营执行包。';
    return;
  }
  status.textContent = '正在写入反馈...';
  try {
    const response = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ result_id: currentResultId, action, section: 'frontend_result_card' })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || 'feedback_failed');
    }
    status.textContent = `反馈已回流：${action}，反馈 ID：${data.feedback_id}`;
  } catch (error) {
    status.textContent = `反馈写入失败：${error.message}`;
  }
}

themeToggle.addEventListener('click', () => {
  setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
});

modeButtons.forEach(button => {
  button.addEventListener('click', () => {
    modeButtons.forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
    currentMode = button.dataset.mode;
    modeName.textContent = currentMode;
    renderSystemMessage(`${currentMode}模式已选择`, '输入商品信息后，点击“生成运营执行包”即可调用后端生成结果。');
  });
});

sideItems.forEach(item => {
  item.addEventListener('click', () => {
    sideItems.forEach(link => link.classList.remove('active'));
    item.classList.add('active');
  });
});

form.addEventListener('submit', event => {
  event.preventDefault();
  generateOperation();
});
