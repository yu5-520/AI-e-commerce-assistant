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

  function patchGenerationCopy() {
    if (typeof window.renderSystemMessage !== 'function' || window.__implicitPipelineCopyPatched) return;
    const originalRenderSystemMessage = window.renderSystemMessage;
    window.renderSystemMessage = (title, message = '') => {
      if (title === '正在生成方案') {
        return originalRenderSystemMessage('正在生成可测试方案', message || '正在生成可复制的标题、主图方向、SKU 和价格建议。');
      }
      return originalRenderSystemMessage(title, message);
    };
    window.__implicitPipelineCopyPatched = true;
  }

  function mountImplicitPipeline() {
    patchGenerationCopy();
    const form = document.getElementById('operationForm');
    if (!form || form.dataset.implicitPipelineMounted === 'true') return;
    if (typeof window.generateOperation !== 'function') return;
    form.dataset.implicitPipelineMounted = 'true';

    form.addEventListener('submit', event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      patchGenerationCopy();
      renderStatus('正在整理商品信息', '正在结合商品信息和参考素材，准备生成可测试方案。');
      window.setTimeout(() => {
        window.generateOperation();
      }, 650);
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountImplicitPipeline);
  } else {
    mountImplicitPipeline();
  }
})();
