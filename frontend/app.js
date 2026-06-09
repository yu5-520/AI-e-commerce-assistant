const root = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const modeButtons = document.querySelectorAll('.mode-card');
const modeName = document.getElementById('modeName');
const form = document.getElementById('operationForm');
const resultBox = document.getElementById('resultBox');

const savedTheme = localStorage.getItem('theme') || 'light';
root.dataset.theme = savedTheme;
themeToggle.textContent = savedTheme === 'dark' ? '切换浅色' : '切换深色';

let currentMode = '自然流';

const modeOutputMap = {
  '自然流': {
    title: '自然流执行包',
    sections: [
      '拼多多标题测试包：搜索词覆盖、价格感、场景词、长尾词',
      '主图文案方向：价格利益点、功能卖点、使用场景',
      '价格测试建议：标准价、券后价、止损提醒',
      '观察指标：曝光、点击率、成交、退款、竞品价格'
    ],
    follow: '补充商品卖点、竞品价格、曝光/点击/成交，会让标题和价格建议更精准。'
  },
  '强付费': {
    title: '强付费放量结果卡',
    sections: [
      '放量条件检查：成本、售价、库存、转化、预算、ROI',
      '预算节奏：小预算测试、逐步放量、异常停投',
      '素材方向：价格利益点、卖点承接、活动素材',
      '风险提醒：ROI 警戒线、退款率、库存承接'
    ],
    follow: '补充点击率、转化率、ROI、退款和预算范围，会让放量判断更清晰。'
  },
  '爆品打造': {
    title: '爆品打造结果卡',
    sections: [
      '爆品结构拆解：需求、价格带、卖点、SKU、人群',
      '流通性测试：标题、主图、价格、半付费测试',
      '差异化承接：低价承接、升级承接、细分人群承接',
      '备货/清货建议：先小测，再判断是否放量'
    ],
    follow: '补充参考爆品、竞品价格、备货能力和当前数据，会让承接路线更精准。'
  }
};

function setTheme(nextTheme) {
  root.dataset.theme = nextTheme;
  localStorage.setItem('theme', nextTheme);
  themeToggle.textContent = nextTheme === 'dark' ? '切换浅色' : '切换深色';
}

function renderResult(product, detail) {
  const output = modeOutputMap[currentMode];
  const safeProduct = product.trim() || '未填写商品';
  const hasDetail = detail.trim().length > 0;

  resultBox.innerHTML = `
    <article class="result-card">
      <h3>${output.title}｜${safeProduct}</h3>
      <p>${hasDetail ? '已根据当前输入生成第一版执行方向。' : '当前为轻输入结果；补充更多信息会更精准。'}</p>
      <ul>
        ${output.sections.map(item => `<li>${item}</li>`).join('')}
      </ul>
    </article>
    <article class="result-card">
      <h3>VIP 持续跟进建议</h3>
      <p>把每天销售情况、已使用标题、SKU 组合、活动报名和数据变化存入私人商品档案，后续 AI 会基于你的店铺数据持续优化。</p>
    </article>
    <article class="result-card muted">
      <h3>补充这些信息会更精准</h3>
      <p>${output.follow}</p>
    </article>
  `;
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
    renderResult(document.getElementById('productInput').value, document.getElementById('detailInput').value);
  });
});

form.addEventListener('submit', event => {
  event.preventDefault();
  renderResult(document.getElementById('productInput').value, document.getElementById('detailInput').value);
});
