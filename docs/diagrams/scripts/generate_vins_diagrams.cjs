// Generate the chapter 39 SVG diagrams and validate every text bounding box.
// Requires Node.js and Playwright. Use --browser PATH for a system Chromium browser.
// Optional --preview-dir PATH writes individual PNGs and a combined contact sheet.
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

const figures = [
  ["vins-joint-optimization.svg", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 450" role="img" aria-labelledby="title desc">
  <title id="title">滑动窗口中的状态、特征与约束</title>
  <desc id="desc">三个图像时刻的状态通过相邻区间的 IMU 预积分连接，同一特征的图像观测连接特征深度和各时刻位姿。历史先验约束保留状态。联合优化同时调整状态和特征深度，使这些关系尽量一致。图中省略其他特征与先验连接。</desc>
  <rect width="960" height="450" rx="12" fill="#fff"></rect>
  <g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#1e293b">
    <text x="32" y="38" font-size="24" font-weight="600">同一组状态，同时接受视觉和惯性约束</text>
    <g fill="none" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="7 5">
      <path d="M540 142L300 272M565 146L520 272M590 142L740 272"></path>
    </g>
    <rect x="427" y="76" width="276" height="70" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"></rect>
    <text x="565" y="105" text-anchor="middle" font-size="20">同一个空间特征点</text>
    <text x="565" y="131" text-anchor="middle" font-size="18">待调整：逆深度</text>
    <rect x="128" y="174" width="300" height="36" rx="6" fill="#fff"></rect>
    <text x="278" y="199" text-anchor="middle" font-size="18" fill="#2563eb">视觉：多次观测约束位姿和深度</text>
    <path d="M178 312H230" stroke="#64748b" stroke-width="3"></path>
    <rect x="32" y="279" width="146" height="66" rx="9" fill="#f1f5f9" stroke="#64748b" stroke-width="2"></rect>
    <text x="105" y="307" text-anchor="middle" font-size="20">历史先验</text>
    <text x="105" y="331" text-anchor="middle" font-size="18">来自旧观测</text>
    <g stroke="#c76b12" stroke-width="4">
      <path d="M370 312H450M590 312H670"></path>
    </g>
    <g fill="#fff7ed">
      <rect x="230" y="272" width="140" height="80" rx="10" stroke="#334155" stroke-width="2"></rect>
      <rect x="450" y="272" width="140" height="80" rx="10" stroke="#334155" stroke-width="2"></rect>
      <rect x="670" y="272" width="140" height="80" rx="10" stroke="#334155" stroke-width="2"></rect>
    </g>
    <g text-anchor="middle" font-size="20">
      <text x="300" y="307">状态 i</text>
      <text x="520" y="307">状态 j</text>
      <text x="740" y="307">状态 k</text>
    </g>
    <g text-anchor="middle" font-size="16" fill="#475569">
      <text x="300" y="335">位姿、速度、偏置</text>
      <text x="520" y="335">位姿、速度、偏置</text>
      <text x="740" y="335">位姿、速度、偏置</text>
    </g>
    <g text-anchor="middle" font-size="18" fill="#9a4b08">
      <text x="410" y="249">IMU 预积分</text>
      <text x="630" y="249">IMU 预积分</text>
    </g>
    <text x="520" y="389" text-anchor="middle" font-size="18" fill="#9a4b08">惯性：两端状态的运动变化与区间测量一致</text>
    <text x="32" y="428" font-size="18" fill="#475569">示意只画出一个特征；实际窗口包含多次视觉观测，先验也可连接多个保留变量。</text>
  </g>
</svg>`],
  ["vins-measurement-timing.svg", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 350" role="img" aria-labelledby="title desc">
  <title id="title">相邻图像时刻与 IMU 采样区间</title>
  <desc id="desc">以图像 20 Hz、IMU 200 Hz 为例，相邻图像时刻相隔 0.05 秒。其间的 IMU 采样用于预积分，得到相对旋转、速度增量和位置增量。示意包含区间端点，实际由时间戳确定积分范围。</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse">
      <path d="M0 0L8 4L0 8Z" fill="#64748b"></path>
    </marker>
  </defs>
  <rect width="960" height="350" rx="12" fill="#fff"></rect>
  <g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#1e293b">
    <text x="32" y="38" font-size="24" font-weight="600">同一段运动，两种采样频率</text>
    <rect x="260" y="68" width="480" height="157" fill="#eff6ff"></rect>
    <path d="M260 62V232M740 62V232" stroke="#94a3b8" stroke-dasharray="6 5"></path>
    <text x="32" y="112" font-size="20">图像 · 20 Hz</text>
    <path d="M210 106H888" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"></path>
    <g fill="#2563eb" stroke="#fff" stroke-width="3">
      <rect x="250" y="96" width="20" height="20" rx="3"></rect>
      <rect x="730" y="96" width="20" height="20" rx="3"></rect>
    </g>
    <text x="260" y="144" text-anchor="middle" font-size="18">图像 i · tᵢ</text>
    <text x="740" y="144" text-anchor="middle" font-size="18">图像 j · tⱼ</text>
    <text x="32" y="202" font-size="20">IMU · 200 Hz</text>
    <path d="M210 196H888" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"></path>
    <g fill="#c76b12" stroke="#fff" stroke-width="2">
      <circle cx="212" cy="196" r="6"></circle>
      <circle cx="260" cy="196" r="7"></circle>
      <circle cx="308" cy="196" r="7"></circle>
      <circle cx="356" cy="196" r="7"></circle>
      <circle cx="404" cy="196" r="7"></circle>
      <circle cx="452" cy="196" r="7"></circle>
      <circle cx="500" cy="196" r="7"></circle>
      <circle cx="548" cy="196" r="7"></circle>
      <circle cx="596" cy="196" r="7"></circle>
      <circle cx="644" cy="196" r="7"></circle>
      <circle cx="692" cy="196" r="7"></circle>
      <circle cx="740" cy="196" r="7"></circle>
      <circle cx="788" cy="196" r="6"></circle>
      <circle cx="836" cy="196" r="6"></circle>
    </g>
    <path d="M264 244H736" stroke="#64748b" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)"></path>
    <text x="500" y="273" text-anchor="middle" font-size="20">0.05 s 的测量 → 相邻图像之间的运动信息</text>
    <text x="32" y="324" font-size="18" fill="#475569">图中包含区间端点；实际积分范围与边界处理由采样时间戳确定。</text>
  </g>
</svg>`],
  ["vins-sliding-window.svg", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 440" role="img" aria-labelledby="title desc">
  <title id="title">移出旧状态并保留历史先验</title>
  <desc id="desc">更新前，历史先验与状态 A、B、C 一起参与求解。边缘化 A 后，其相关历史信息转为对保留状态的近似先验，再加入新状态 D 和观测。更新后优化 B、C、D，计算规模保持有限。该图示意移出最早状态的情况。</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0 0L8 4L0 8Z" fill="#64748b"></path>
    </marker>
  </defs>
  <rect width="960" height="440" rx="12" fill="#fff"></rect>
  <g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#1e293b">
    <text x="32" y="38" font-size="24" font-weight="600">窗口向前移动，部分历史约束继续保留</text>
    <text x="32" y="78" font-size="18" fill="#475569">更新前：联合估计 A、B、C</text>
    <path d="M202 133H266M394 133H486M614 133H706" fill="none" stroke="#64748b" stroke-width="3"></path>
    <rect x="32" y="103" width="170" height="60" rx="9" fill="#f1f5f9" stroke="#64748b" stroke-width="2"></rect>
    <text x="117" y="140" text-anchor="middle" font-size="20">历史先验</text>
    <rect x="266" y="103" width="128" height="60" rx="9" fill="#fff1f2" stroke="#be123c" stroke-width="2" stroke-dasharray="6 4"></rect>
    <rect x="486" y="103" width="128" height="60" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="2"></rect>
    <rect x="706" y="103" width="128" height="60" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="2"></rect>
    <g text-anchor="middle" font-size="20">
      <text x="330" y="140">状态 A</text>
      <text x="550" y="140">状态 B</text>
      <text x="770" y="140">状态 C</text>
    </g>
    <text x="330" y="191" text-anchor="middle" font-size="18" fill="#be123c">待移出</text>
    <path d="M890 128V300" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"></path>
    <rect x="32" y="211" width="802" height="43" rx="7" fill="#f8fafc"></rect>
    <text x="433" y="239" text-anchor="middle" font-size="20">消去 A → 生成新的近似先验 → 加入 D 及其观测</text>
    <text x="32" y="286" font-size="18" fill="#475569">更新后：联合估计 B、C、D</text>
    <path d="M202 336H266M394 336H486M614 336H706" fill="none" stroke="#64748b" stroke-width="3"></path>
    <rect x="32" y="306" width="170" height="60" rx="9" fill="#f1f5f9" stroke="#64748b" stroke-width="2"></rect>
    <text x="117" y="343" text-anchor="middle" font-size="20">更新后的先验</text>
    <rect x="266" y="306" width="128" height="60" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="2"></rect>
    <rect x="486" y="306" width="128" height="60" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="2"></rect>
    <rect x="706" y="306" width="128" height="60" rx="9" fill="#ecfdf5" stroke="#047857" stroke-width="2"></rect>
    <g text-anchor="middle" font-size="20">
      <text x="330" y="343">状态 B</text>
      <text x="550" y="343">状态 C</text>
      <text x="770" y="343">状态 D</text>
    </g>
    <text x="32" y="415" font-size="18" fill="#475569">图示为移出最早状态的情况；实际先验可同时连接多个保留变量。</text>
  </g>
</svg>`]
];

function option(name) {
  const i = process.argv.indexOf(name);
  if (i < 0) return undefined;
  if (!process.argv[i + 1] || process.argv[i + 1].startsWith('--')) throw Error(`Missing value for ${name}`);
  return process.argv[i + 1];
}
async function main() {
  const browserPath = option('--browser');
  const previewDir = option('--preview-dir');
  const output = path.resolve(__dirname, '../../06-sensors-navigation/diagrams');
  const browser = await chromium.launch({ headless: true, ...(browserPath ? { executablePath: browserPath } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 600 }, deviceScaleFactor: 1.5 });
    const validated = [];
    for (const [filename, source] of figures) {
      const svg = `${source}\n`;
      await page.setContent(`<html><body style="margin:0;background:white">${svg}</body></html>`);
      await page.evaluate(() => document.fonts.ready);
      const errors = await page.evaluate(() => {
        const svg = document.querySelector('svg');
        const canvas = svg.viewBox.baseVal;
        const labels = [...svg.querySelectorAll('text')].map(t => {
          const b = t.getBBox();
          return { text: t.textContent, x: b.x, y: b.y, w: b.width, h: b.height };
        });
        const errors = [];
        for (const a of labels) {
          if (a.x < canvas.x || a.y < canvas.y || a.x + a.w > canvas.x + canvas.width || a.y + a.h > canvas.y + canvas.height) errors.push(`Outside canvas: ${a.text}`);
        }
        for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) {
          const a = labels[i], b = labels[j];
          if (Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x) > 0.5 && Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y) > 0.5) errors.push(`Text overlap: ${a.text} / ${b.text}`);
        }
        return errors;
      });
      if (errors.length) throw Error(`${filename}:\n${errors.join('\n')}`);
      validated.push([filename, svg]);
    }
    // Validate every figure before replacing any generated SVG.
    await fs.mkdir(output, { recursive: true });
    if (previewDir) await fs.mkdir(previewDir, { recursive: true });
    for (const [filename, svg] of validated) {
      await fs.writeFile(path.join(output, filename), svg, 'utf8');
      if (previewDir) {
        await page.setContent(`<html><body style="margin:0;background:white">${svg}</body></html>`);
        await page.evaluate(() => document.fonts.ready);
        await page.locator('svg').screenshot({ path: path.join(previewDir, filename.replace('.svg', '.png')) });
      }
      console.log(`Validated and generated ${filename}`);
    }
    if (previewDir) {
      await page.setContent(`<html><body style="margin:0;width:960px;background:#e2e8f0">${validated.map(([, svg]) => `<div style="margin-bottom:16px">${svg}</div>`).join('')}</body></html>`);
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: path.join(previewDir, 'vins-diagrams-overview.png'), fullPage: true });
    }
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
