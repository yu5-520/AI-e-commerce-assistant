(() => {
  function renderStatus(title, message = '') {
    const resultBox = document.getElementById('resultBox');
    if (!resultBox) return;
    resultBox.innerHTML = `
      <article class="result-card muted">
        <h3>${title}</h3>
        ${message ? `<p>${message}</p>` : ''}
      </article>
    `;
  }

  function mountImplicitPipeline() {
    const form = document.getElementById('operationForm');
    if (!form || form.dataset.implicitPipelineMounted === 'true') return;
    form.dataset.implicitPipelineMounted = 'true';

    form.addEventListener('submit', event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      renderStatus('正在整理商品素材', '正在校准当前时间、商品信息和参考素材。');
      window.setTimeout(() => {
        renderStatus('正在生成可测试方案', '正在生成可复制的标题、主图方向、SKU 和价格建议。');
        if (typeof window.generateOperation === 'function') {
          window.generateOperation();
        } else {
          const submitButton = form.querySelector('button[type="submit"]');
          submitButton?.click();
        }
      }, 650);
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountImplicitPipeline);
  } else {
    mountImplicitPipeline();
  }
})();
