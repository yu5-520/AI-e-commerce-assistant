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

function cleanText(value) {
  return String(value || '')
    .replace(/result_id|backflow|llm_status|fallback|debug|api|POST|GET/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
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

function normalizeProductResult(payload) {
  const productResult = payload.product_result || {};
  return {
    title: cleanText(productResult.title || `${payload.mode || currentMode}执行包｜${payload.product || '未填写商品'}`),
    summary: cleanText(productResult.summary || '已生成可复制、可执行、可回流的运营结果。'),
    titles: Array.isArray(productResult.titles) ? productResult.titles : [],
    imageDirections: Array.isArray(productResult.image_directions) ? productResult.image_directions : [],
    skuPlans: Array.isArray(productResult.sku_plans) ? productResult.sku_plans : [],
    priceAdvice: Array.isArray(productResult.price_advice) ? productResult.price_advice : [],
    activitySuggestions: Array.isArray(productResult.activity_suggestions) ? productResult.activity_suggestions : [],
    nextActions: Array.isArray(productResult.next_actions) ? productResult.next_actions : [],
    precisionTips: Array.isArray(productResult.precision_tips) ? productResult.precision_tips : [],
    debug: payload.debug || {},
  };
}

function productItemButton(action, text, label = '标记使用') {
  return `<button class="small-btn" data-feedback="${escapeHtml(action)}" data-item-text="${escapeHtml(text)}" type="button">${escapeHtml(label)}</button>`;
}

function copyButton(text) {
  return `<button class="small-btn ghost" data-copy="${escapeHtml(text)}" type="button">复制</button>`;
}

function renderTitleCards(titles) {
  if (!titles.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>标题测试包</h3><span>可直接复制上架测试</span></div>
      <div class="copy-list">
        ${titles.map((item, index) => {
          const text = cleanText(item.text || item);
          const tag = cleanText(item.tag || '测试标题');
          const useCase = cleanText(item.use_case || '标题测试');
          return `
            <article class="copy-item">
              <div class="copy-index">${index + 1}</div>
              <div class="copy-content">
                <strong>${escapeHtml(text)}</strong>
                <p>${escapeHtml(tag)} · ${escapeHtml(useCase)}</p>
              </div>
              <div class="copy-actions">
                ${copyButton(text)}
                ${productItemButton('used_title', text, '已使用')}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderImageDirections(items) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>主图结构</h3><span>给美工或生成图工具直接使用</span></div>
      <div class="card-grid">
        ${items.map(item => {
          const name = cleanText(item.name || '主图方向');
          const mainText = cleanText(item.main_text || '主图大字');
          const subText = cleanText(item.sub_text || '副文案');
          const structure = cleanText(item.structure || '画面结构');
          const copyText = `${name}\n主图大字：${mainText}\n副文案：${subText}\n画面结构：${structure}`;
          return `
            <article class="product-card">
              <span class="card-kicker">${escapeHtml(name)}</span>
              <h4>${escapeHtml(mainText)}</h4>
              <p>${escapeHtml(subText)}</p>
              <div class="structure-box">${escapeHtml(structure)}</div>
              <div class="action-row">
                ${copyButton(copyText)}
                ${productItemButton('used_image_direction', copyText, '已使用')}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderSkuPlans(items) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>SKU 组合建议</h3><span>可用于商品规格设计</span></div>
      <div class="sku-table">
        <div class="sku-row sku-head"><span>SKU 类型</span><span>示例</span><span>作用</span><span>操作</span></div>
        ${items.map(item => {
          const type = cleanText(item.type || 'SKU');
          const example = cleanText(item.example || '规格示例');
          const purpose = cleanText(item.purpose || '作用');
          const copyText = `${type}：${example}｜${purpose}`;
          return `
            <div class="sku-row">
              <span>${escapeHtml(type)}</span>
              <span>${escapeHtml(example)}</span>
              <span>${escapeHtml(purpose)}</span>
              <span class="table-actions">${copyButton(copyText)}${productItemButton('used_sku', copyText, '已用')}</span>
            </div>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderSimpleList(title, subtitle, items, action) {
  if (!items.length) return '';
  return `
    <section class="product-section">
      <div class="section-title"><h3>${escapeHtml(title)}</h3><span>${escapeHtml(subtitle)}</span></div>
      <div class="simple-list">
        ${items.map(item => {
          const label = typeof item === 'string' ? '' : cleanText(item.label || '建议');
          const value = typeof item === 'string' ? cleanText(item) : cleanText(item.value || item.text || '');
          const copyText = label ? `${label}：${value}` : value;
          return `
            <article class="simple-item">
              <div>${label ? `<strong>${escapeHtml(label)}</strong>` : ''}<p>${escapeHtml(value)}</p></div>
              <div class="copy-actions">${copyButton(copyText)}${productItemButton(action, copyText, '已执行')}</div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function renderResult(payload) {
  currentResultId = payload.result_id || null;
  const product = normalizeProductResult(payload);
  resultBox.innerHTML = `
    <article class="result-card product-result">
      <div class="product-head">
        <div>
          <h3>${escapeHtml(product.title)}</h3>
          <p>${escapeHtml(product.summary)}</p>
        </div>
        <span class="saved-pill">已保存用于后续跟进</span>
      </div>
      ${renderTitleCards(product.titles)}
      ${renderImageDirections(product.imageDirections)}
      ${renderSkuPlans(product.skuPlans)}
      ${renderSimpleList('价格与活动建议', '直接给动作，不显示工程字段', [...product.priceAdvice, ...product.activitySuggestions], 'used_activity')}
      ${renderSimpleList('下一步操作', '按顺序执行并回填数据', product.nextActions, 'done_next_action')}
      ${renderSimpleList('补充这些信息会更精准', '不是必填项，只用于提高下一版质量', product.precisionTips, 'precision_tip')}
    </article>
    <article class="result-card">
      <h3>结果回流</h3>
      <p>复制、使用、执行反馈都会写入回流记录，后续可进入 VIP 私人商品跟进。</p>
      <p id="feedbackStatus" class="feedback-status">等待反馈。</p>
      <details class="debug-panel">
        <summary>开发调试信息</summary>
        <pre>${escapeHtml(JSON.stringify(product.debug, null, 2))}</pre>
      </details>
    </article>
  `;

  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', () => copyToClipboard(button.dataset.copy));
  });
  document.querySelectorAll('[data-feedback]').forEach(button => {
    button.addEventListener('click', () => sendFeedback(button.dataset.feedback, button.dataset.itemText || ''));
  });
}

async function copyToClipboard(text) {
  const status = document.getElementById('feedbackStatus');
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = '已复制，可直接粘贴使用。';
  } catch {
    status.textContent = '复制失败，请手动选中文案复制。';
  }
}

async function generateOperation() {
  const product = document.getElementById('productInput').value;
  const detail = document.getElementById('detailInput').value;
  const cost = document.getElementById('costInput').value;
  const price = document.getElementById('priceInput').value;
  const stock = document.getElementById('stockInput').value;

  setLoading(true);
  renderSystemMessage('正在生成', '后端正在清洗输出，返回可复制、可执行、可回流的产品化结果。');

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

async function sendFeedback(action, itemText = '') {
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
      body: JSON.stringify({ result_id: currentResultId, action, item_text: itemText, section: 'product_result_card' })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || 'feedback_failed');
    }
    status.textContent = `反馈已回流：${action}。`;
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
    renderSystemMessage(`${currentMode}模式已选择`, '输入商品信息后，点击“生成运营执行包”即可调用后端生成产品化结果。');
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
