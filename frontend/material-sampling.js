(() => {
  function currentSeason() {
    const month = new Date().getMonth() + 1;
    if ([3, 4, 5].includes(month)) return '春季';
    if ([6, 7, 8].includes(month)) return '夏季';
    if ([9, 10, 11].includes(month)) return '秋季';
    return '冬季';
  }

  function clean(value) {
    return String(value || '').trim() || '商品';
  }

  function getMode() {
    return document.querySelector('.mode-card.selected')?.dataset?.mode || '自然流';
  }

  function buildTasks(product, mode) {
    const season = currentSeason();
    const tasks = [
      `${product} ${season} 热门标题`,
      `${product} ${season} 主图卖点`,
      `${product} 同价位 SKU 组合`,
    ];
    if (mode === '强付费') {
      tasks.push(`${product} 投放素材 点击率 卖点`);
    } else if (mode === '爆品打造') {
      tasks.push(`${product} 爆品 对标 价格带`);
    } else {
      tasks.push(`${product} 自然搜索 长尾词`);
    }
    return tasks;
  }

  function buildTemplate(product, mode) {
    const season = currentSeason();
    const tasks = buildTasks(product, mode);
    return [
      `【采样任务】`,
      ...tasks.map((task, index) => `${index + 1}. ${task}`),
      '',
      `【粘贴素材】`,
      `${product}${season}可用标题或主图卖点 1：`,
      `${product}${season}可用标题或主图卖点 2：`,
      `${product}${season}可用标题或主图卖点 3：`,
      '',
      `【注意】不要复制过去年份词，不要直接照抄竞品标题，只提取词感和结构。`,
    ].join('\n');
  }

  function ensureSamplingHelper() {
    const textarea = document.getElementById('marketMaterialInput');
    const productInput = document.getElementById('productInput');
    if (!textarea || !productInput || document.querySelector('[data-sampling-helper="true"]')) return;

    const helper = document.createElement('div');
    helper.className = 'sampling-helper';
    helper.dataset.samplingHelper = 'true';
    helper.innerHTML = `
      <div class="sampling-actions">
        <button class="small-btn ghost" type="button" data-sampling-template>生成采样任务</button>
        <button class="small-btn" type="button" data-sampling-append>追加采样模板</button>
      </div>
      <p class="sampling-tip">先让系统给你列采样方向，再把看到的当前标题或主图卖点粘进来。</p>
    `;
    textarea.insertAdjacentElement('afterend', helper);

    helper.querySelector('[data-sampling-template]').addEventListener('click', () => {
      const product = clean(productInput.value);
      const mode = getMode();
      textarea.value = buildTemplate(product, mode);
      textarea.focus();
    });

    helper.querySelector('[data-sampling-append]').addEventListener('click', () => {
      const product = clean(productInput.value);
      const mode = getMode();
      const template = buildTemplate(product, mode);
      textarea.value = textarea.value.trim() ? `${textarea.value.trim()}\n\n${template}` : template;
      textarea.focus();
    });
  }

  document.addEventListener('DOMContentLoaded', ensureSamplingHelper);
  setTimeout(ensureSamplingHelper, 100);
})();
