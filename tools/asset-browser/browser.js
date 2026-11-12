(function () {
  'use strict';

  // 工具独立运行，不启动游戏、不修改共享数据，也不执行 skins.js。
  const $ = id => document.getElementById(id);
  const content = $('content');
  const dialog = $('unit-detail');
  const images = new Map();
  const previews = new Map();
  const unitCardBounds = new Map();
  const visible = new Set();
  const state = { tab: 'units', era: -1, query: '', zoom: 2, speed: 1, anchors: false, bounds: false, kind: 'all', severity: 'all', packGroup: 'all', histAction: 'walk', histSide: '0' };
  const tabs = ['units', 'bases', 'fx', 'textures', 'projectiles', 'health', 'packs', 'history'];
  const titles = ['兵种图鉴', '基地', '特效', '材质', '弹道总表', '素材体检', '外部素材包', '历代外观'];
  const HISTORY_FIT = 0.7;   // 历代外观的整体缩小系数：五代并排时一屏放得下，各代之间的相对大小不变
  const PACK_FPS = 10;   // 素材包动画统一播放帧率（素材包没有自带帧率）
  const sides = ['我方', '敌方', '纯白'];
  const actions = { walk: '走路', atk: '攻击', die: '死亡' };
  const kindNames = { hit: '受击 / 爆炸', muzzle: '炮口火光', fly: '飞行体' };
  const slots = ['射手', '炮兵', '轻塔', '中塔', '重塔'];
  const severityNames = { error: '错误', warning: '警告', info: '提示' };
  // 历代外观清单来自 generations.js；缺失时只是没有「历代外观」的内容，其余页签照常。
  const generations = typeof SPRITE_GENERATIONS === 'undefined' ? {} : SPRITE_GENERATIONS;
  const genStatus = { current: '游戏现用', dlc: 'DLC 外观包', archived: '已归档' };
  // 与 fx.js 的地面锚点规则一致；其余受击类在游戏中以格子中心为命中点。
  const groundFx = new Set(['dirt', 'big', 'acid', 'spore', 'grenade', 'boom', 'barrel', 'nuke', 'strike', 'thunder', 'meteor', 'pillar', 'emp', 'slam', 'burn', 'puddle', 'burst']);
  const defaultFx = ['blunt', 'spark', 'crit', 'flash', 'dirt', 'big'];
  let skins = [], skinError = '', issues = [], refs = new Map();
  let selection = null, animTime = 0, lastTime = 0;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => entry.isIntersecting ? visible.add(entry.target) : visible.delete(entry.target));
  }, { rootMargin: '160px' });

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function button(text, run, className = '') {
    const node = el('button', className, text);
    node.type = 'button'; node.addEventListener('click', run);
    return node;
  }
  function route(era) { return ROUTES[ERA_ROUTE[era]] || { name: '共同起源', col: '#b6a176' }; }
  function eraAllowed(era) { return state.era < 0 || state.era === era; }
  function matches(...values) { return !state.query || values.join(' ').toLowerCase().includes(state.query); }
  function eras() { return AGES.map((_, i) => i).filter(eraAllowed); }
  function kindOf(meta) { return meta.kind || 'hit'; }
  function texturePath(name) { return `assets/ui/textures/${name}.webp`; }
  function spritePath(era) { return `assets/sprites/era${era}.webp`; }
  function count(text) { $('result-count').textContent = text; }
  function empty(text = '没有符合筛选条件的素材。试试其他时代，或清空搜索。') { content.append(el('div', 'empty', text)); }
  function dropPreviews(root) {
    for (const canvas of previews.keys()) if (root.contains(canvas)) {
      observer.unobserve(canvas); visible.delete(canvas); previews.delete(canvas);
    }
  }

  // 路径统一相对项目根目录；onerror 会保留来源，体检可点击定位。
  function loadImage(path, target) {
    if (images.has(path)) return images.get(path).promise;
    const record = { image: new Image(), path, target, status: 'loading' };
    images.set(path, record);
    record.promise = new Promise(resolve => {
      record.image.onload = () => { record.status = 'ready'; resolve(record); };
      record.image.onerror = () => { record.status = 'error'; resolve(record); };
      // 素材包路径里有空格和括号，逐段编码
      record.image.src = `../../${path.split('/').map(encodeURIComponent).join('/')}${path.startsWith('assets/sprites/') ? `?v=${encodeURIComponent(SPRITE_VER)}` : ''}`;
    });
    return record.promise;
  }

  async function loadSkins() {
    try {
      const response = await fetch('../../js/ui/skins.js', { cache: 'no-cache' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const source = await response.text();
      // 只接受字符串字面量数组，不用 eval / Function 执行取回的脚本。
      const match = source.match(/\bconst\s+SKIN_OF_ERA\s*=\s*\[([\s\S]*?)\]\s*;/);
      if (!match) throw new Error('找不到 SKIN_OF_ERA 数组');
      const body = match[1].replace(/\/\*[\s\S]*?\*\/|\/\/[^\n\r]*/g, '');
      const strings = [...body.matchAll(/(['"])([a-zA-Z0-9_-]+)\1/g)];
      if (!strings.length || body.replace(/(['"])[a-zA-Z0-9_-]+\1/g, '').replace(/[\s,]/g, '')) throw new Error('材质表包含无法识别的内容');
      skins = strings.map(item => item[2]);
    } catch (error) { skinError = `材质表读取失败：${error.message}`; }
  }

  function buildEraFilter() {
    const root = $('eras'); root.replaceChildren();
    const all = button('全部时代', () => { state.era = -1; buildEraFilter(); render(); });
    all.setAttribute('aria-pressed', String(state.era === -1)); root.append(all);
    AGES.forEach((name, era) => {
      const item = button('', () => { state.era = era; buildEraFilter(); render(); });
      item.style.setProperty('--route', route(era).col);
      item.setAttribute('aria-pressed', String(state.era === era));
      item.title = route(era).name;
      item.append(el('span', 'era-num', String(era).padStart(2, '0')), el('span', 'dot'), el('span', '', name));
      if (FINAL_ERAS.includes(era)) item.append(el('span', 'era-end', '终局'));
      root.append(item);
    });
    $('era-count').textContent = AGES.length;
  }

  // 所有预览走一个动画时钟；仅绘制视口附近的画布，切页后解除观察。
  function canvasPreview(desc, label, className = 'preview checker') {
    const wrap = el('div', className);
    const holder = el('div', 'canvas-wrap');
    if (desc.card) holder.style.padding = '0';
    const canvas = el('canvas'); canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', label);
    holder.append(canvas); wrap.append(holder);
    previews.set(canvas, desc); observer.observe(canvas); draw(canvas, desc);
    return wrap;
  }
  function gensOf(era) { return generations[era] || []; }
  // 某一代的图集路径和格子信息；不指定代号就是游戏现用的那套。
  function genSource(era, genId) {
    const gen = genId && gensOf(era).find(item => item.id === genId);
    if (!gen || gen.live) return { path: spritePath(era), units: SPRITE_META[era] };
    return { path: gen.path, units: gen.units };
  }
  function unitDesc(era, type, row = 0, action = 'walk', frame = null, genId = null) {
    const source = genSource(era, genId), m = source.units?.[type];
    if (!m || !source.path) return { missing: true, w: 70, h: 55 };
    return { path: source.path, w: m.cw, h: m.ch, px: m.ax, py: m.ch - 1,
      frame: () => ({ x: (frame ?? (SPRITE_FRAMES[action] + Math.floor(animTime * (action === 'die' ? 1 / 0.12 : 8)) % 4)) * m.cw, y: m.y + row * m.ch }) };
  }
  // 卡片裁去四帧共有的透明余量；原图、详情和逐帧视图始终保留完整画格。
  function unitCardDesc(era, type) {
    const desc = unitDesc(era, type), meta = SPRITE_META[era]?.[type];
    const record = images.get(spritePath(era));
    if (!meta || record?.status !== 'ready') return desc;
    const key = `${era}/${type}`;
    if (!unitCardBounds.has(key)) {
      const scratch = document.createElement('canvas'); scratch.width = meta.cw; scratch.height = meta.ch;
      const ctx = scratch.getContext('2d', { willReadFrequently: true });
      let left = meta.cw, top = meta.ch, right = -1, bottom = -1;
      for (let frame = 0; frame < 4; frame++) {
        ctx.clearRect(0, 0, meta.cw, meta.ch);
        ctx.drawImage(record.image, (SPRITE_FRAMES.walk + frame) * meta.cw, meta.y, meta.cw, meta.ch, 0, 0, meta.cw, meta.ch);
        const data = ctx.getImageData(0, 0, meta.cw, meta.ch).data;
        for (let y = 0; y < meta.ch; y++) for (let x = 0; x < meta.cw; x++) if (data[(y * meta.cw + x) * 4 + 3] >= 200) {
          left = Math.min(left, x); top = Math.min(top, y); right = Math.max(right, x); bottom = Math.max(bottom, y);
        }
      }
      const x = Math.max(0, left - 2), y = Math.max(0, top - 2);
      unitCardBounds.set(key, right < 0 ? { x: 0, y: 0, w: meta.cw, h: meta.ch } : {
        x, y, w: Math.min(meta.cw - 1, right + 2) - x + 1, h: Math.min(meta.ch - 1, bottom + 2) - y + 1
      });
    }
    const crop = unitCardBounds.get(key), baseFrame = desc.frame;
    return { ...desc, card: true, displayRatio: Math.min(1, (meta.s || SPRITE_SCALE) / .88),
      w: crop.w, h: crop.h, px: meta.ax - crop.x, py: meta.ch - 1 - crop.y,
      frame: () => { const f = baseFrame(); return { x: f.x + crop.x, y: f.y + crop.y }; } };
  }
  function fxDesc(name) {
    const m = FX_META[name];
    if (!m) return { missing: true, w: 45, h: 35 };
    return { path: 'assets/fx/fx.webp', w: m.w, h: m.h, px: m.px, py: groundFx.has(name) || m.kind ? m.py : m.h / 2,
      frame: () => { const i = Math.floor(animTime * m.fps) % m.n; return { x: m.x + (i % m.cols) * m.w, y: m.y + Math.floor(i / m.cols) * m.h }; } };
  }
  function draw(canvas, desc) {
    const pad = desc.compact ? 4 : 12;
    let zoom = desc.compact ? Math.min(state.zoom, 56 / desc.w, 50 / desc.h) : state.zoom * (desc.ratio || 1);
    if (desc.card) {
      const available = canvas.closest('.preview')?.clientWidth || 224;
      zoom = Math.min(state.zoom * desc.displayRatio, Math.max(32, available - 30 - 2 * pad) / desc.w, 210 / desc.h);
    }
    const w = Math.max(1, Math.ceil(desc.w * zoom)) + pad * 2, h = Math.max(1, Math.ceil(desc.h * zoom)) + pad * 2;
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;
    const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, w, h); ctx.imageSmoothingEnabled = false;
    const image = images.get(desc.path);
    if (!desc.missing && image?.status === 'ready') {
      const frame = desc.frame();
      ctx.drawImage(image.image, frame.x, frame.y, desc.w, desc.h, pad, pad, desc.w * zoom, desc.h * zoom);
    } else {
      ctx.fillStyle = '#ff9f98'; ctx.font = '12px sans-serif'; ctx.fillText('缺少素材', pad, h / 2);
    }
    if (state.bounds) {
      ctx.strokeStyle = '#b2c9d9'; ctx.lineWidth = 1;
      ctx.strokeRect(pad - 0.5, pad - 0.5, desc.w * zoom + 1, desc.h * zoom + 1);
    }
    if (state.anchors && Number.isFinite(desc.px) && Number.isFinite(desc.py)) {
      const x = pad + desc.px * zoom, y = pad + desc.py * zoom;
      ctx.strokeStyle = '#ff7e83'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x - 7, y); ctx.lineTo(x + 7, y); ctx.moveTo(x, y - 7); ctx.lineTo(x, y + 7); ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.fillRect(x - 1, y - 1, 2, 2);
    }
  }
  function animate(time) {
    if (lastTime && !document.hidden) animTime += Math.min((time - lastTime) / 1000, 0.1) * state.speed;
    lastTime = time;
    visible.forEach(canvas => { const desc = previews.get(canvas); if (desc) draw(canvas, desc); });
    requestAnimationFrame(animate);
  }

  // 页签 01：兵种卡片与逐帧图鉴。
  function renderUnits() {
    const grid = el('div', 'grid'); let total = 0;
    eras().forEach(era => {
      for (let type = 0; type < UNIT_BASE.length; type++) {
        const name = UNIT_NAMES[era]?.[type] || `兵种 ${type}`;
        if (!matches(name, AGES[era], TYPE_DESC[type], era)) continue;
        const card = button('', () => openUnit(era, type), 'card unit-card'); card.id = `unit-${era}-${type}`;
        card.setAttribute('aria-label', `查看${AGES[era]}·${name}`);
        card.style.setProperty('--route', route(era).col);
        card.append(canvasPreview(unitCardDesc(era, type), `${name}${UNIT_BASE[type].air ? '飞行' : '走路'}动画`));
        const body = el('div', 'card-body'), title = el('div', 'card-title');
        title.append(el('span', 'dot'), el('h3', '', name), el('span', 'type', TYPE_SHORT[type]));
        body.append(title, el('p', '', `${String(era).padStart(2, '0')} / ${AGES[era]} · ${route(era).name}${gensOf(era).length > 1 ? ` · ${gensOf(era).length} 代外观` : ''}`));
        card.append(body); grid.append(card); total++;
      }
    });
    content.append(grid); count(`${total} / ${AGES.length * UNIT_BASE.length} 兵种`); if (!total) empty();
  }
  function openUnit(era, type, gen = null, row = 0, action = 'walk') {
    selection = { era, type, row, action, gen }; renderDetail(); dialog.showModal();
  }
  function renderDetail() {
    dropPreviews($('detail-content'));
    const { era, type, row, action, gen } = selection, name = UNIT_NAMES[era]?.[type] || '未命名兵种';
    const root = $('detail-content'); root.replaceChildren();
    const head = el('div', 'detail-head'), title = el('h2', '', `${AGES[era]} · ${name}`); title.id = 'detail-title';
    head.append(title, button('关闭 ×', () => dialog.close()));
    const main = el('div', 'detail-main'), controls = el('div', 'detail-controls');
    const unitActions = UNIT_BASE[type].air ? { walk: '飞行', atk: '攻击', die: '坠落' } : actions;
    Object.entries(unitActions).forEach(([key, label]) => {
      const b = button(label, () => { selection.action = key; renderDetail(); }, action === key ? 'active' : '');
      b.setAttribute('aria-pressed', String(action === key)); controls.append(b);
    });
    const sideLabel = el('label', '', '阵营 '), sideSelect = el('select'); sideSelect.setAttribute('aria-label', '阵营');
    sides.forEach((label, i) => { const option = el('option', '', label); option.value = i; sideSelect.append(option); });
    sideSelect.value = row; sideSelect.addEventListener('change', () => { selection.row = Number(sideSelect.value); renderDetail(); });
    sideLabel.append(sideSelect); controls.append(sideLabel);
    const unitGens = gensOf(era).filter(item => genSource(era, item.id).units?.[type]);
    if (unitGens.length > 1) {   // 有多代外观的兵种：详情里可以直接换代
      const genLabel = el('label', '', '版本 '), genSelect = el('select'); genSelect.setAttribute('aria-label', '外观版本');
      unitGens.forEach(item => { const option = el('option', '', `${item.name}（${genStatus[item.status]}）`); option.value = item.id; genSelect.append(option); });
      genSelect.value = gen || unitGens.find(item => item.live)?.id || unitGens[0].id;
      genSelect.addEventListener('change', () => { selection.gen = genSelect.value; renderDetail(); });
      genLabel.style.marginLeft = '0'; genLabel.append(genSelect); controls.append(genLabel);
    }
    const meta = genSource(era, gen).units?.[type];
    main.append(controls, canvasPreview(unitDesc(era, type, row, action, null, gen), `${name}${sides[row]}${unitActions[action]}动画`, 'preview checker detail-preview'),
      el('p', 'detail-description', `${TYPE_SHORT[type]} / ${TYPE_DESC[type]}。源格子 ${meta?.cw ?? '?'} × ${meta?.ch ?? '?'} px；锚点 (${meta?.ax ?? '?'}, ${(meta?.ch ?? 1) - 1})；游戏绘制倍数 ${meta?.s || SPRITE_SCALE}。预览按原始像素缩放。`));
    if (meta?.preview === 'concept-v4') {
      main.append(el('p', 'detail-description', '样稿接入预览版：保留已确认原图，走路与攻击使用整张角色的轻量起伏、前倾和伸缩，死亡使用倒地过渡；尚未制作独立的迈腿和武器挥动逐帧动画。'));
    }
    if (issues.some(issue => issue.severity === 'error' && issue.era === era && issue.target.tab === 'units')) {
      main.append(el('p', 'error detail-description', '此时代图集存在结构错误，预览可能混入相邻行或缺少部分帧。请在体检页核对图集与格子表。'));
    }
    if (type === 1 || type === 4) {
      main.append(el('h3', '', '弹道配置'), el('pre', 'config', JSON.stringify(PROJ_STYLE[era]?.[type === 1 ? 0 : 1] || {}, null, 2)));
    }
    main.append(el('h3', '', `12 帧检查 · ${sides[row]}`));
    const scroll = el('div', 'scroll checker'), strip = el('div', 'filmstrip');
    for (let frame = 0; frame < 12; frame++) {
      const figure = el('figure');
      figure.append(canvasPreview(unitDesc(era, type, row, action, frame, gen), `${name}第${frame}帧`, ''), el('figcaption', '', `${String(frame).padStart(2, '0')} / ${Object.values(unitActions)[Math.floor(frame / 4)]}`));
      strip.append(figure);
    }
    scroll.append(strip); main.append(scroll); root.append(head, main);
  }
  dialog.addEventListener('close', () => { dropPreviews($('detail-content')); selection = null; });

  function block(era, id, suffix = '') {
    const root = el('section', 'asset-block'); root.id = id; root.style.setProperty('--route', route(era).col);
    const head = el('div', 'block-heading');
    head.append(el('span', 'dot'), el('h3', '', `${String(era).padStart(2, '0')} / ${AGES[era]}`), el('small', '', suffix || route(era).name));
    root.append(head); return root;
  }
  // 页签 02：每时代横向展开九格，保持源像素，不压缩大图。
  function renderBases() {
    let total = 0;
    eras().forEach(era => {
      if (!matches(AGES[era], '基地', era)) return;
      const root = block(era, `base-${era}`, '列：损坏程度 / 每组三种阵营');
      const scroll = el('div', 'scroll'), grid = el('div', 'base-grid');
      for (let row = 0; row < 3; row++) for (let damage = 0; damage < 3; damage++) {
        const cell = el('div', 'base-cell'); cell.append(el('div', 'cell-label', `${sides[row]} · ${['完好', '受损', '残破'][damage]}`));
        cell.append(canvasPreview({ path: 'assets/bases/bases.webp', w: BASE_CELL.cw, h: BASE_CELL.ch, px: BASE_CELL.ax, py: BASE_CELL.ch - 1,
          missing: !BASE_META[era], frame: () => ({ x: damage * BASE_CELL.cw, y: (BASE_META[era]?.y || 0) + row * BASE_CELL.ch }) }, `${AGES[era]}${sides[row]}${damage}损坏阶段`));
        grid.append(cell);
      }
      scroll.append(grid); root.append(scroll); content.append(root); total++;
    });
    count(`${total} 时代 / ${total * 9} 格`); if (!total) empty();
  }

  function filters(options, key) {
    const bar = el('div', 'subbar');
    Object.entries(options).forEach(([value, label]) => {
      const b = button(label, () => { state[key] = value; render(); }, state[key] === value ? 'active' : '');
      b.setAttribute('aria-pressed', String(state[key] === value)); bar.append(b);
    }); return bar;
  }
  // 页签 03：特效元数据及游戏实际锚点。
  function renderFx() {
    content.append(filters({ all: '全部特效', ...kindNames }, 'kind'));
    const grid = el('div', 'grid'); let total = 0;
    Object.entries(FX_META).forEach(([name, meta]) => {
      const uses = refs.get(name) || [];
      if (state.era >= 0 && !uses.some(use => use.era === state.era || use.era === undefined)) return;
      if (state.kind !== 'all' && kindOf(meta) !== state.kind) return;
      if (!matches(name, kindNames[kindOf(meta)])) return;
      const card = el('article', 'card'); card.id = `fx-${name}`;
      const body = el('div', 'card-body'), desc = fxDesc(name);
      body.append(el('h3', 'mono', name), el('p', '', `${kindNames[kindOf(meta)]} · ${meta.n} 帧 · ${meta.fps} fps`),
        el('p', 'mono', `${meta.w} × ${meta.h} px / 锚点 ${desc.px}, ${desc.py}${desc.py !== meta.py ? `（meta.py=${meta.py}）` : ''}`),
        el('p', '', `${uses.length} 处数据引用${meta.spin ? ' · 游戏中可旋转' : ''}`));
      card.append(canvasPreview(desc, `${name}特效循环动画`), body); grid.append(card); total++;
    });
    content.append(grid); count(`${total} / ${Object.keys(FX_META).length} 特效`); if (!total) empty();
  }

  // 页签 04：材质平铺样本、普通按钮、窄按钮。
  function renderTextures() {
    let total = 0;
    eras().forEach(era => {
      const name = skins[era]; if (!matches(AGES[era], name, era)) return;
      const root = block(era, `texture-${era}`, name || '缺少材质映射'), grid = el('div', 'texture-row');
      if (!name) { root.append(el('p', 'error card-body', '没有该时代的材质映射，请查看体检。')); }
      else [name, `btn_${name}`, `btn_${name}_s`].forEach((file, index) => {
        const cell = el('div', 'texture-item'), path = texturePath(file), record = images.get(path);
        cell.append(el('div', 'cell-label', ['平铺纹理', '普通按钮', '窄按钮'][index]));
        const preview = el('div', 'preview checker');
        if (record?.status === 'ready') {
          if (index === 0) {
            const tile = el('div', 'repeat-sample'); tile.style.backgroundImage = `url("${record.image.src}")`;
            tile.style.backgroundSize = `${record.image.naturalWidth * state.zoom}px ${record.image.naturalHeight * state.zoom}px`;
            preview.append(tile);
          } else {
            const image = record.image.cloneNode(); image.alt = `${AGES[era]}${file}`;
            image.width = record.image.naturalWidth * state.zoom; image.height = record.image.naturalHeight * state.zoom; preview.append(image);
          }
        } else preview.append(el('span', 'error', '图片加载失败'));
        cell.append(preview, el('p', 'mono', path), el('p', '', record?.status === 'ready' ? `${record.image.naturalWidth} × ${record.image.naturalHeight} px` : '不可用'));
        grid.append(cell);
      });
      root.append(grid); content.append(root); total++;
    });
    count(`${total} 时代`); if (!total) empty();
  }

  function fxReference(name, role) {
    const root = el('div', 'fx-ref');
    root.append(canvasPreview({ ...fxDesc(name), compact: true }, `${name}缩略图`));
    const text = el('div'); text.append(el('div', 'ref-label', role), button(name, () => jump({ tab: 'fx', id: `fx-${name}` })));
    root.append(text); return root;
  }
  // 页签 05：保留完整五列，搜索时按整行匹配。
  function renderProjectiles() {
    const scroll = el('div', 'table-scroll'), table = el('table'), head = el('thead'), tr = el('tr'); let total = 0;
    ['时代', ...slots].forEach(name => tr.append(el('th', '', name))); head.append(tr); table.append(head);
    const body = el('tbody');
    eras().forEach(era => {
      if (!matches(AGES[era], ...(UNIT_NAMES[era] || []), ...(TOWER_NAMES[era] || []), JSON.stringify(PROJ_STYLE[era]), era)) return;
      const row = el('tr'), label = el('th', '', `${era} / ${AGES[era]}`); label.scope = 'row'; row.append(label);
      for (let slot = 0; slot < 5; slot++) {
        const cell = el('td'); cell.id = `proj-${era}-${slot}`;
        const style = PROJ_STYLE[era]?.[slot];
        if (!style) cell.append(el('p', 'error', '缺少弹道配置'));
        else {
          cell.append(el('p', 'cell-label', slot < 2 ? UNIT_NAMES[era]?.[slot === 0 ? 1 : 4] : TOWER_NAMES[era]?.[slot - 2]));
          [['f', '飞行体'], ['h', '命中'], ['m', '炮口']].forEach(([key, role]) => { if (style[key]) cell.append(fxReference(style[key], role)); });
          if (style.beam) cell.append(el('p', 'config', `瞬发：${style.beam}`));
          if (style.swarm) cell.append(el('p', 'config', `虫群：${style.n || '?'} 只 / ${style.swarm}`));
          if (style.s) cell.append(el('p', 'config', `飞行体缩放 ${style.s}×`));
          if (!style.h) cell.append(el('p', 'ref-label', '默认命中：单体 spark / 溅射 dirt'));
        }
        row.append(cell);
      }
      body.append(row); total++;
    });
    table.append(body); scroll.append(table); content.append(scroll); count(`${total} 时代 × 5 列`); if (!total) empty();
  }

  // 体检覆盖全部已加载图片；提示的引用范围明确限定为本工具读取的数据表。
  function audit() {
    issues = []; refs = new Map();
    const add = (severity, message, target, era, detail = '') => issues.push({ severity, message, target, era, detail });
    const use = (name, origin) => { if (!refs.has(name)) refs.set(name, []); refs.get(name).push(origin); };
    if (skinError) add('error', skinError, { tab: 'textures' });
    images.forEach(record => { if (record.status === 'error') add('error', '图片加载失败', record.target, record.target.era, record.path); });
    [['SPRITE_META', SPRITE_META, 'units'], ['BASE_META', BASE_META, 'bases'], ['SKIN_OF_ERA', skins, 'textures']].forEach(([name, data, tab]) => {
      if (Object.keys(data).length !== AGES.length) add('error', `${name} 时代数不一致`, { tab }, undefined, `${Object.keys(data).length} 项 / AGES ${AGES.length} 项`);
      AGES.forEach((_, era) => { if (data[era] === undefined) add('error', `${name} 缺少 ${AGES[era]}`, { tab, era }, era); });
    });
    const inside = (path, x, y, w, h) => {
      const record = images.get(path);
      return record?.status !== 'ready' || (Number.isFinite(x + y + w + h) && x >= 0 && y >= 0 && w > 0 && h > 0 && x + w <= record.image.naturalWidth && y + h <= record.image.naturalHeight);
    };
    const dimensions = path => {
      const image = images.get(path)?.image;
      return image?.naturalWidth ? `图集实际 ${image.naturalWidth}×${image.naturalHeight} px` : '图集不可用';
    };
    AGES.forEach((_, era) => {
      const units = SPRITE_META[era] || [];
      if (units.length !== UNIT_BASE.length) add('error', `${AGES[era]} 兵种数量应为 ${UNIT_BASE.length}`, { tab: 'units', era }, era);
      units.forEach((m, type) => {
        const target = { tab: 'units', era, id: `unit-${era}-${type}` };
        if (!inside(spritePath(era), 0, m.y, 12 * m.cw, 3 * m.ch)) add('error', `${AGES[era]} · ${UNIT_NAMES[era]?.[type]} 格子越界`, target, era, `需要宽 ${12 * m.cw} / 底边 y=${m.y + 3 * m.ch}；${dimensions(spritePath(era))}。图集与格子表可能不配套，请检查本时代全部兵种。`);
        units.slice(type + 1).forEach((other, offset) => {
          if (m.y < other.y + 3 * other.ch && other.y < m.y + 3 * m.ch) add('error', `${AGES[era]} 兵种格子在 y 方向重叠`, target, era, `${type} 与 ${type + 1 + offset}`);
        });
      });
      if (BASE_META[era] && !inside('assets/bases/bases.webp', 0, BASE_META[era].y, 3 * BASE_CELL.cw, 3 * BASE_CELL.ch)) add('error', `${AGES[era]} 基地格子越界`, { tab: 'bases', era, id: `base-${era}` }, era);
    });
    Object.entries(generations).forEach(([key, list]) => list.forEach(gen => {
      const era = Number(key), target = { tab: 'history', era, id: `history-${era}` };
      if (gen.live) return;   // 现用版已在上面检查
      if (gen.error) { add('error', `${AGES[era]} · ${gen.name}：${gen.error}`, target, era, gen.manifest || ''); return; }
      if (!gen.path || !Array.isArray(gen.units) || gen.units.length !== 5) { add('error', `${AGES[era]} · ${gen.name}：清单缺少图集路径或 5 个兵种的格子信息`, target, era, 'tools/asset-browser/generations.js'); return; }
      gen.units.forEach((m, type) => {
        if (!inside(gen.path, 0, m.y, 12 * m.cw, 3 * m.ch)) add('error', `${AGES[era]} · ${gen.name} · ${UNIT_NAMES[era]?.[type]} 格子越界`, target, era, `需要宽 ${12 * m.cw} / 底边 y=${m.y + 3 * m.ch}；${dimensions(gen.path)}。`);
      });
    }));
    PROJ_STYLE.forEach((styles, era) => styles.forEach((style, slot) => {
      const target = { tab: 'projectiles', era, id: `proj-${era}-${slot}` };
      [['f', 'fly'], ['m', 'muzzle'], ['h', 'hit']].forEach(([key, expected]) => {
        const name = style[key]; if (!name) return;
        use(name, { era, slot, key });
        if (!FX_META[name]) add('error', `${AGES[era] || era} · ${slots[slot]}：${key} 引用了不存在的 ${name}`, target, era, `PROJ_STYLE[${era}][${slot}].${key}`);
        else if (kindOf(FX_META[name]) !== expected) add('error', `${name} 种类用错：${key} 应为 ${kindNames[expected]}`, target, era, `实际为 ${kindNames[kindOf(FX_META[name])] || FX_META[name].kind}`);
      });
    }));
    defaultFx.forEach(name => use(name, { source: '默认命中 / 近战 / 基地 / 大招' }));
    Object.entries(SHELL_LAND).forEach(([style, entries]) => entries.forEach(([name]) => {
      const eraList = SHELL_STYLE.map((value, era) => value === style ? era : -1).filter(era => era >= 0);
      eraList.forEach(era => use(name, { era, source: `SHELL_LAND.${style}` }));
      if (!FX_META[name]) add('error', `大招落点引用了不存在的 ${name}`, { tab: 'fx' }, undefined, `SHELL_LAND.${style}`);
    }));
    Object.entries(FX_META).forEach(([name, m]) => {
      const target = { tab: 'fx', id: `fx-${name}` };
      if (![m.cols, m.n].every(n => Number.isInteger(n) && n > 0) || !Number.isFinite(m.fps) || m.fps <= 0) {
        add('error', `${name} 帧数、列数或速度无效`, target); return;
      }
      // 最后一排可能没填满：分开校验首排最大宽与末排最大高。
      if (!inside('assets/fx/fx.webp', m.x, m.y, Math.min(m.cols, m.n) * m.w, Math.ceil(m.n / m.cols) * m.h)) add('error', `${name} 特效格子越界`, target);
      if (!refs.has(name)) add('info', `${name} 未在已读取的数据表中被引用`, target, undefined, '已检查 PROJ_STYLE、SHELL_LAND 与游戏默认特效；代码中的其他直接引用不在扫描范围。');
    });
    issues.sort((a, b) => ['error', 'warning', 'info'].indexOf(a.severity) - ['error', 'warning', 'info'].indexOf(b.severity));
    const errors = issues.filter(issue => issue.severity === 'error').length;
    $('health-badge').textContent = errors ? `${errors} 错误` : '正常';
    $('health-badge').className = errors ? 'error' : '';
  }

  // 页签 06：完整体检先运行，时代和搜索只筛选显示，不影响顶部总计。
  function renderHealth() {
    const summary = el('div', 'health-summary');
    ['error', 'warning', 'info'].forEach(level => {
      const cell = el('div', `health-stat ${level}`);
      cell.append(el('b', '', issues.filter(issue => issue.severity === level).length), el('span', '', `全项目${severityNames[level]}`)); summary.append(cell);
    });
    content.append(summary);
    if (!issues.some(issue => issue.severity === 'error')) content.append(el('p', 'good', '素材结构检查通过 · 图片、弹道引用、图集边界与时代映射未发现错误。'));
    const bar = filters({ all: '全部问题', ...severityNames }, 'severity');
    bar.append(button('重新检查', () => { audit(); render(); }), el('p', '', '检查范围：全部时代；下方列表遵循筛选条件。'));
    content.append(bar);
    const list = issues.filter(issue => (state.severity === 'all' || issue.severity === state.severity) && (issue.era === undefined || eraAllowed(issue.era)) && matches(issue.message, issue.detail));
    list.forEach(issue => {
      const item = button('', () => jump(issue.target), 'issue');
      const text = el('span', 'issue-text', issue.message); if (issue.detail) text.append(el('small', 'mono', issue.detail));
      item.append(el('span', `severity ${issue.severity}`, severityNames[issue.severity]), text, el('span', 'jump', '查看素材 ↗')); content.append(item);
    });
    count(`${list.length} 条问题`); if (!list.length) empty('当前筛选下没有问题。');
  }

  // 页签 07：外部素材包（清单来自 packs.js）。横向长条图按帧循环播放，其余显示原图。
  function packDesc(pack, file) {
    const [rel, w, h, frames] = file, path = `${pack.root}/${rel}`, fw = frames > 1 ? h : w;
    loadImage(path, { tab: 'packs' });
    return { path, w: fw, h, frame: () => ({ x: frames > 1 ? (Math.floor(animTime * PACK_FPS) % frames) * fw : 0, y: 0 }) };
  }
  function packGroups(pack) { return [...new Set(pack.files.map(file => file[0].split('/')[0]))]; }
  function renderPacks() {
    const packs = typeof ASSET_PACKS === 'undefined' ? [] : ASSET_PACKS;
    if (!packs.length) { empty('还没有素材包清单。在项目根目录运行 python tools/asset-browser/scan_packs.py 后刷新。'); count('0 张'); return; }
    let total = 0;
    packs.forEach(pack => {
      const groups = packGroups(pack);
      content.append(filters({ all: '全部', ...Object.fromEntries(groups.map(g => [g, g])) }, 'packGroup'));
      const grid = el('div', 'grid');
      pack.files.forEach(file => {
        const [rel, w, h, frames] = file, parts = rel.split('/');
        if (state.packGroup !== 'all' && parts[0] !== state.packGroup) return;
        if (!matches(rel)) return;
        const name = parts[parts.length - 1].replace(/\.png$/i, '');
        const card = button('', () => openPack(pack, file), 'card unit-card');
        card.append(canvasPreview(packDesc(pack, file), `${name}预览`));
        const body = el('div', 'card-body'), title = el('div', 'card-title');
        title.append(el('h3', '', name), el('span', 'type', frames > 1 ? `${frames} 帧` : '静态'));
        body.append(title, el('p', '', `${parts.slice(0, -1).join(' / ')} · ${w}×${h}`));
        card.append(body); grid.append(card); total++;
      });
      content.append(grid);
    });
    count(`${total} 张`); if (!total) empty();
  }
  function openPack(pack, file) {
    selection = { pack: true };
    const [rel, w, h, frames] = file, root = $('detail-content'), path = `${pack.root}/${rel}`;
    dropPreviews(root); root.replaceChildren();
    const head = el('div', 'detail-head'), title = el('h2', '', rel.split('/').pop()); title.id = 'detail-title';
    head.append(title, button('关闭 ×', () => dialog.close()));
    const main = el('div', 'detail-main');
    main.append(canvasPreview(packDesc(pack, file), `${rel}动画`, 'preview checker detail-preview'),
      el('p', 'detail-description mono', `${path}\n整图 ${w}×${h} px · ${frames > 1 ? `${frames} 帧，每帧 ${h}×${h} px，按 ${PACK_FPS} fps 播放` : '静态图'}`),
      el('h3', '', '整张原图'));
    const sheet = el('div', 'scroll checker'), img = el('img');
    img.src = images.get(path)?.image.src || ''; img.alt = rel; img.style.margin = '12px';
    sheet.append(img); main.append(sheet); root.append(head, main); dialog.showModal();
  }

  // 页签 08：历代外观。每个兵种一行、每代一列，同一时刻播同一帧，方便直接比较。
  // 各代像素密度不同，这里统一乘上各自的绘制倍数，显示的大小就是游戏里的相对大小。
  function renderHistory() {
    const list = Object.keys(generations).map(Number).filter(era => gensOf(era).length > 1 && eraAllowed(era));
    if (!list.length) {
      empty(state.era >= 0 ? `${AGES[state.era]}只有游戏现用的一代外观，没有可比较的历史版本。` : '还没有历代外观清单（tools/asset-browser/generations.js）。');
      count('0 代'); return;
    }
    const bar = filters(actions, 'histAction');
    const sideLabel = el('label', '', '阵营 '), sideSelect = el('select'); sideSelect.setAttribute('aria-label', '阵营');
    sides.forEach((label, i) => { const option = el('option', '', label); option.value = i; sideSelect.append(option); });
    sideSelect.value = state.histSide; sideSelect.addEventListener('change', () => { state.histSide = sideSelect.value; render(); });
    sideLabel.append(sideSelect); bar.append(sideLabel);
    content.append(bar);
    let total = 0, shown = 0;
    list.forEach(era => {
      const gens = gensOf(era), row = Number(state.histSide);
      const root = block(era, `history-${era}`, `${gens.length} 代 · 按游戏内相对大小显示`);
      const scroll = el('div', 'table-scroll history'), table = el('table'), head = el('thead'), tr = el('tr');
      tr.append(el('th', '', '兵种'));
      gens.forEach((gen, index) => {
        const th = el('th'), title = el('div', 'gen-title');
        title.append(el('span', 'gen-num', `第 ${index + 1} 代`), el('strong', '', gen.name), el('span', `gen-status ${gen.status}`, genStatus[gen.status] || gen.status));
        const source = genSource(era, gen.id);
        th.append(title, el('p', 'gen-note', `${gen.date} · ${gen.note}`), el('p', 'gen-note mono', gen.error || (gen.live ? spritePath(era) : source.path || '')));
        tr.append(th);
      });
      head.append(tr); table.append(head);
      const body = el('tbody');
      for (let type = 0; type < 5; type++) {
        const name = UNIT_NAMES[era]?.[type] || `兵种 ${type}`;
        if (!matches(name, AGES[era], TYPE_DESC[type], ...gens.map(gen => gen.name))) continue;
        const line = el('tr'), label = el('th'); label.scope = 'row';
        label.append(el('div', '', name), el('div', 'ref-label', TYPE_SHORT[type]));
        line.append(label);
        gens.forEach(gen => {
          const cell = el('td'), m = genSource(era, gen.id).units?.[type];
          const open = button('', () => openUnit(era, type, gen.id, row, state.histAction), 'gen-cell');
          open.setAttribute('aria-label', `查看${gen.name}的${name}`);
          open.append(canvasPreview({ ...unitDesc(era, type, row, state.histAction, null, gen.id), ratio: (m?.s || SPRITE_SCALE) * HISTORY_FIT }, `${gen.name}${name}${actions[state.histAction]}动画`),
            el('span', 'ref-label mono', m ? `${m.cw}×${m.ch} 格 · ×${Number((m.s || SPRITE_SCALE).toFixed(2))}` : '缺少素材'));
          cell.append(open); line.append(cell);
        });
        body.append(line); shown++;
      }
      table.append(body); scroll.append(table); root.append(scroll); content.append(root); total += gens.length;
    });
    count(`${total} 代 / ${shown} 兵种`); if (!shown) empty();
  }

  function jump(target) {
    if (dialog.open) dialog.close();
    state.tab = target.tab; state.era = target.era ?? -1; state.query = ''; state.kind = 'all'; $('search').value = '';
    buildEraFilter(); render();
    requestAnimationFrame(() => {
      const node = target.id && $(target.id);
      if (node) { node.scrollIntoView({ block: 'center', inline: 'center' }); node.classList.add('flash'); setTimeout(() => node.classList.remove('flash'), 1800); }
      else $('content').focus({ preventScroll: true });
    });
  }
  const renderers = { units: renderUnits, bases: renderBases, fx: renderFx, textures: renderTextures, projectiles: renderProjectiles, health: renderHealth, packs: renderPacks, history: renderHistory };
  const notes = {
    units: '卡片按显示体积适配；点击兵种，在详情中按原始像素查看三段动画、阵营配色与 12 帧原图。',
    bases: '每时代九格，依次为我方、敌方、纯白；横向滚动查看全部损坏阶段。',
    fx: '按元数据帧率循环播放；十字标出游戏绘制锚点，不包含游戏的叠加发光与淡出。时代筛选显示该时代数据引用的特效。',
    textures: '纹理平铺预览与两种按钮原图。素材图片保持像素采样。',
    projectiles: '射手、炮兵与三类防御塔的弹道配置；点击特效名查看原图。',
    health: '只读检查全部图集、引用与映射。未引用项是提示，可点击跳转定位。',
    history: '同一个兵种的每一代外观并排播放，大小按游戏里的实际比例。点任意一格看该代的三段动画和 12 帧原图；兵种详情里也能用「版本」切换。清单在 tools/asset-browser/generations.js。',
    packs: '项目目录里的第三方素材包，只浏览不导入游戏。横向长条图按帧播放；点卡片看整张原图。左侧时代筛选在这里不起作用。'
  };
  function render() {
    dropPreviews(content); content.replaceChildren();
    $('page-title').textContent = titles[tabs.indexOf(state.tab)]; $('page-note').textContent = notes[state.tab];
    document.querySelectorAll('[data-tab]').forEach(node => {
      if (node.dataset.tab === state.tab) node.setAttribute('aria-current', 'page'); else node.removeAttribute('aria-current');
    });
    renderers[state.tab]();
  }
  async function start() {
    document.querySelector('.toolbar').addEventListener('submit', event => event.preventDefault());
    await loadSkins();
    const loads = AGES.map((_, era) => loadImage(spritePath(era), { tab: 'units', era }));
    loads.push(loadImage('assets/bases/bases.webp', { tab: 'bases' }), loadImage('assets/fx/fx.webp', { tab: 'fx' }));
    [...new Set(skins)].forEach(name => [name, `btn_${name}`, `btn_${name}_s`].forEach(file => {
      const era = skins.indexOf(name); loads.push(loadImage(texturePath(file), { tab: 'textures', era, id: `texture-${era}` }));
    }));
    // 历代外观：外观包读它自己的 manifest（和游戏加载的是同一份），归档版直接用清单里的路径。
    for (const [key, list] of Object.entries(generations)) for (const gen of list) {
      const era = Number(key);
      if (gen.manifest) {
        try {
          const response = await fetch(`../../${gen.manifest}`, { cache: 'no-cache' });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const entry = (await response.json()).eras?.[era];
          if (!entry?.file || !Array.isArray(entry.units)) throw new Error('清单里没有这个时代');
          gen.path = `${gen.manifest.slice(0, gen.manifest.lastIndexOf('/'))}/${entry.file}`; gen.units = entry.units;
        } catch (error) { gen.error = `外观包清单读取失败：${error.message}`; }
      }
      if (!gen.live && gen.path) loads.push(loadImage(gen.path, { tab: 'history', era, id: `history-${era}` }));
    }
    await Promise.all(loads); audit(); buildEraFilter();
    $('inventory').textContent = `${AGES.length} 时代 / ${AGES.length * UNIT_BASE.length} 兵种 / ${Object.keys(FX_META).length} 特效`;
    $('status').textContent = skinError || '';
    $('tabs').addEventListener('click', event => {
      const tab = event.target.closest('[data-tab]'); if (!tab) return;
      state.tab = tab.dataset.tab; render();
    });
    $('search').addEventListener('input', event => { state.query = event.target.value.trim().toLowerCase(); render(); });
    ['zoom', 'speed', 'anchors', 'bounds'].forEach(key => $(key).addEventListener('change', event => {
      state[key] = event.target.type === 'checkbox' ? event.target.checked : Number(event.target.value);
      if (key === 'zoom' && state.tab === 'textures') render();
      previews.forEach((desc, canvas) => draw(canvas, desc));
    }));
    render(); requestAnimationFrame(animate);
  }
  start().catch(error => { $('status').textContent = `工具启动失败：${error.message}。请在项目根目录启动静态服务器后重试。`; });
}());
