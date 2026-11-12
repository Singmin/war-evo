'use strict';
// 开始页背景：AI 对 AI 的实时对局（只画战场，不画 HUD、不出声、不记战绩）
// 没有真正的对局时（G 为 null：开始页、从开始页进的设置 / 战绩）由 main.js 驱动。
// 演示局放在 DEMO 里，推进和绘制时临时换进 G，用的是和正式对局完全相同的规则、AI 和画面。

/** 演示局状态；null = 还没开始 */
let DEMO = null;
let demoAcc = 0;
/** 演示局比正常速度快一点，开始页更热闹 */
const DEMO_SPEED = 1.5;
/** 演示局最长秒数，到点或任一基地血量低于这个比例就重开（不会真的分出胜负，也就不会写战绩） */
const DEMO_MAX_T = 150, DEMO_MIN_HP = 0.3;
/** 镜头：缩放和跟随前线的平滑速度 */
const DEMO_ZOOM = 1, DEMO_CAM_EASE = 0.6;
/** 整个战场往上抬多少逻辑像素：让交战线落在标题和底部按钮板之间（css/menu.css 留出的 y 200–520） */
const DEMO_LIFT = 180;

/** 把 fn 放在演示局里跑（G 临时指向 DEMO） */
function withDemo(fn) {
  const real = G; G = DEMO;
  try { fn(); } finally { G = real; }
}

/** 开一局新的演示：随机从第 2–4 个时代起步（青铜到火药一带，一开场兵就好看），每次开始页看到的兵种和画面都不一样 */
function demoNew() {
  const real = G;
  newGame('normal');
  DEMO = G; G = real;
  DEMO.demo = true; DEMO.mineHint = true; DEMO.zoom = DEMO_ZOOM;
  const tier = 1 + Math.floor(Math.random() * 3);
  withDemo(() => {
    for (const sd of G.sides) {
      for (let i = 0; i < tier; i++) demoAdvance(sd);
      sd.gold = 200 + INCOME[sd.age] * 40;
    }
    G.camX = (WORLD - W / G.zoom) / 2;
  });
  demoAcc = 0;
}

/** 立即进入下一个时代（跳过跃迁等待），规则和 sim.js stepSide 里跃迁完成时一样 */
function demoAdvance(sd) {
  const e = aiNextEra(sd);
  if (e === undefined) return;
  sd.age++; sd.era = e; sd.path.push(e); sd.baseHp = BASE_HP[sd.age];
  const rt = ERA_ROUTE[e];
  if (rt && !sd.route) { sd.route = rt; ROUTES[rt].ap(sd.mod); }
  if (ERA_BONUS[e]) ERA_BONUS[e].ap(sd.mod);
}

/** 每帧推进演示局（rdt = 真实经过的秒数） */
function demoTick(rdt) {
  if (!DEMO || DEMO.t > DEMO_MAX_T || DEMO.sides.some(sd => sd.baseHp < BASE_HP[sd.age] * DEMO_MIN_HP)) demoNew();
  withDemo(() => {
    demoAcc += rdt * DEMO_SPEED;
    let n = 0;
    while (demoAcc >= STEP && n < 12) {
      step(STEP);                 // step 里每 0.5 秒替余烬派（右）想一次
      G.ai0T = (G.ai0T || 0) - STEP;
      if (G.ai0T <= 0) { G.ai0T = 0.5; aiThink(0); }   // 拾光派（左）也交给 AI
      demoAcc -= STEP; n++;
    }
    if (n >= 12) demoAcc = 0;
    // 演示局不要提示文字、震屏和放大招时的镜头拉远
    G.toast = G.echo = G.specialView = G.castFx = null; G.freeze = 0; G.shake = 0; G.texts.length = 0;
    // 镜头慢慢跟着两军交锋的地方走
    const xs = G.units.map(u => u.x);
    const mid = xs.length ? (Math.min(...xs) + Math.max(...xs)) / 2 : WORLD / 2;
    G.zoom = DEMO_ZOOM;
    const want = clamp(mid - W / G.zoom / 2, 0, WORLD - W / G.zoom);
    G.camX += (want - G.camX) * Math.min(1, rdt * DEMO_CAM_EASE);
  });
}

/** 画演示局的战场（不画 HUD） */
function demoRender() {
  if (!DEMO) { drawBackground(0); return; }
  withDemo(() => {
    ctx.save(); ctx.translate(0, -DEMO_LIFT); drawWorld(); ctx.restore();
  });
}
