'use strict';
// 核心数据：常量、时代、兵种、科技表（对应 docs/设计文档.md 第 3–6 节）
// =====================================================================
// 常量与数据（对应 docs/设计文档.md 第 3–5 节）
// =====================================================================
const W = 1280, H = 720, WORLD = 1920, GROUND_Y = 590, STEP = 1 / 60;
const BASE_L = 160, BASE_R = WORLD - 160;    // 两边基地的门口 x
const MIN_ZOOM = W / WORLD;                    // 缩到最小时整个战场一屏装下
const MAX_UNITS = 15, QUEUE_MAX = 5, SPACING = 24;
const AIR_ALT = 150, AIR_BASE_DMG = 0.5; // 飞行高度（世界像素）；空军攻基地的伤害倍数
const UNIT_ORDER = [0, 1, 2, 4, 5, 3];  // 只改显示和快捷键顺序，兵种编号不变
// 堵门出兵：门口的兵被敌人顶住（站着不动）时，新兵照样出来，叠在门口；门口 SPAWN_ZONE 像素内最多叠 SPAWN_STACK 个
const SPAWN_STACK = 3, SPAWN_ZONE = 70;
// 主场加成：离自家门口 HOME_ZONE 像素以内的兵，受到的伤害 × HOME_DMG（各种来源都算：兵、塔、大招）
const HOME_ZONE = 300, HOME_DMG = 0.75;

// ---------- 时代（设计文档 6.1）：17 个时代。青铜纪之后分三条路线，每条路线最后再分三个最终时代（共 9 个结局时代）----------
// 0 部落 / 1 青铜 / 机械线 2 蒸汽 3 电气 / 生物线 5 驯兽 6 生化 / 火药线 7 火药 8 帆船
// 最终时代：机械线 4 机甲 9 核能 10 智械 / 生物线 11 共生 12 巨兽 13 蜂群 / 火药线 14 铁甲舰 15 航空 16 远征
const AGES = ['部落纪', '青铜纪', '蒸汽纪', '电气纪', '机甲纪', '驯兽纪', '生化纪', '火药纪', '帆船纪',
  '核能纪', '智械纪', '共生纪', '巨兽纪', '蜂群纪', '铁甲舰纪', '航空纪', '远征纪'];
const ERA_TIER = [0, 1, 2, 3, 4, 2, 3, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4];   // 第几个时代（决定数值强度）
const ERA_PARENTS = [[], [0], [1], [2], [3], [1], [5], [1], [7], [3], [3], [6], [6], [6], [8], [8], [8]];
const ERA_ROUTE = [null, null, 'mech', 'mech', 'mech', 'bio', 'bio', 'gun', 'gun', 'mech', 'mech', 'bio', 'bio', 'bio', 'gun', 'gun', 'gun'];
const FINAL_ERAS = [4, 9, 10, 11, 12, 13, 14, 15, 16];   // 科技树最右一列的顺序
// 美术：每个时代的兵种借用哪套画法（0–4）；空军另有飞行占位画法
const ERA_ART = [[0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3], [4, 4, 4, 4, 4],
  [0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [1, 2, 1, 1, 2], [2, 2, 1, 2, 2],
  [3, 3, 4, 3, 4], [4, 4, 4, 3, 3], [0, 1, 0, 0, 1], [0, 0, 0, 0, 0], [1, 0, 1, 1, 0], [3, 3, 2, 3, 3], [3, 2, 4, 2, 3], [2, 2, 1, 2, 2]];
const ERA_BASE_ART = [0, 1, 2, 3, 4, 5, 6, 7, 8, 3, 4, 6, 5, 6, 8, 7, 7];
for (const art of ERA_ART) art.push(art[1]);
const TIER_NAMES = ['部落', '青铜', '第三', '第四', '终局'];
// 最终时代自带的加成（进入时生效，整局保留），让 9 个结局玩起来不一样
const ERA_BONUS = {
  4: { desc: '重装生命 +25%', ap: m => { m.hp[3] *= 1.25; } },
  9: { desc: '大招每发伤害 +40%', ap: m => { m.spDmg *= 1.4; } },
  10: { desc: '所有兵训练时间 −20%', ap: m => { m.train *= 0.8; } },
  11: { desc: '所有兵每秒再回复 1% 生命', ap: m => { m.regen += 0.01; } },
  12: { desc: '骑兵和重装攻击 +20%', ap: m => { m.atk[2] *= 1.2; m.atk[3] *= 1.2; } },
  13: { desc: '所有兵价格 −15%', ap: m => { m.price *= 0.85; } },
  14: { desc: '基地受到的伤害 −20%', ap: m => { m.armor *= 0.8; } },
  15: { desc: '所有兵移动速度 +20%', ap: m => { for (let i = 0; i < UNIT_BASE.length; i++) m.speed[i] *= 1.2; } },
  16: { desc: '击杀金币 +40%，自动金币 +15%', ap: m => { m.bounty *= 1.4; m.income *= 1.15; } },
};
// 路线专属机制（design/quick-specs/early-tech-routes-ads.md 2.3）：第一次进入这条路线时生效，整局保留
// mech 标题是路线牌上的短名；desc 是完整规则
const SP_UPG_COST = [150, 300, 500], SP_UPG_DMG = 0.15, SP_UPG_SHELLS = 2;   // 机械线大招强化：价格 × 1.7^第几个时代；每级伤害 +15%、炮弹 +2 发
const SPORE_T = 4, SPORE_R = 60, SPORE_HEAL = 0.04;                        // 生物线孢子：持续秒数、半径、每秒回复最大生命的比例（多个不叠加）
const ROUTES = {
  mech: { name: '机械线', col: '#8a96a6', mech: '精准大招', desc: '大招每一发都锁定敌兵；可花金币强化大招 3 级，每级伤害 +15%、炮弹 +2 发', ap: m => { m.spLock = true; } },
  bio: { name: '生物线', col: '#6fbf4a', mech: '孢子治疗', desc: `我方兵阵亡时原地留下治疗孢子 ${SPORE_T} 秒，周围我方兵每秒回复 ${SPORE_HEAL * 100}% 生命`, ap: m => { m.spore = true; } },
  gun: { name: '火药线', col: '#d0533f', mech: '赏金', desc: '击杀金币 +50%，自动金币 −15%', ap: m => { m.bounty *= 1.5; m.income *= 0.85; } },
};
// 兵种编号：0 步兵 / 1 射手 / 2 骑兵 / 3 重装 / 4 炮兵 / 5 空军
const UNIT_NAMES = [
  ['骨棒战士', '投石手', '狼骑兵', '猛犸骑手', '巨石投手'],
  ['铜剑兵', '弓手', '马骑兵', '战车', '投石机'],
  ['刺刀兵', '火枪手', '摩托骑兵', '蒸汽坦克', '野战炮'],
  ['电棍卫', '步枪手', '电动突击车', '电磁战车', '迫击炮组'],
  ['光刃士', '等离子射手', '悬浮飞骑', '机甲', '轨道炮车'],
  ['兽皮战士', '吹箭手', '剑齿虎骑', '驯象', '投毒弩'],
  ['变异战士', '毒刺射手', '迅猛兽骑', '巨兽', '孢子炮'],
  ['长枪兵', '火绳枪手', '龙骑兵', '盾车', '臼炮'],
  ['水手刀客', '燧发枪手', '骠骑兵', '登陆炮艇', '舰炮'],
  ['防化兵', '伽马射手', '核动力车', '反应堆坦克', '战术核炮'],
  ['机器人兵', '无人机手', '机械狼', '守卫巨像', '集群导弹车'],
  ['藤甲战士', '荆刺射手', '苔原鹿骑', '树人', '种荚炮'],
  ['兽王卫', '骨矛手', '恐爪骑', '雷霆巨兽', '喷火兽'],
  ['工蜂卫', '针刺蜂', '飞蝗骑', '甲虫盾', '酸囊虫'],
  ['陆战队', '来复枪手', '装甲骑兵', '装甲列车', '巨舰炮'],
  ['伞兵', '狙击手', '滑翔骑兵', '轰炸飞艇', '高射炮'],
  ['佣兵', '神枪手', '远征骑兵', '堡垒车', '攻城巨炮'],
];
const AIR_NAMES = ['驯鹰人', '火鸢', '蒸汽飞艇', '旋翼机', '浮空炮艇', '巨鹰骑手', '翼蝠兽', '神火飞鸦', '热气球',
  '核动力轰炸机', '攻击无人机', '飘絮水母', '翼龙', '黄蜂王', '水上飞机', '战斗机', '侦察飞艇'];
UNIT_NAMES.forEach((names, era) => names.push(AIR_NAMES[era]));
const TYPE_SHORT = '步射骑重炮空';
const TOWER_NAMES = [
  ['石子弹弓', '骨矛投掷器', '滚石架'],
  ['连弩台', '弩炮台', '投石车'],
  ['蒸汽机枪', '加农炮', '臼炮'],
  ['电弧桩', '特斯拉塔', '磁轨炮'],
  ['激光哨塔', '离子炮', '引力井'],
  ['荆棘哨', '毒刺塔', '巨蜂巢'],
  ['菌毯哨', '酸液塔', '孢子井'],
  ['火枪台', '虎蹲炮', '红衣大炮'],
  ['瞭望炮台', '舷炮台', '岸防巨炮'],
  ['辐射哨', '粒子炮', '核子井'],
  ['自动哨戒', '无人机巢', '中枢炮台'],
  ['藤蔓哨', '刺藤塔', '母树'],
  ['兽骨哨', '骨刺塔', '巨口井'],
  ['蜂哨', '毒针塔', '蜂后巢'],
  ['机枪堡', '速射炮', '要塞巨炮'],
  ['高射机枪', '防空炮', '气球炮台'],
  ['商站哨', '炮楼', '黄金要塞'],
];
const SPECIAL_NAMES = ['陨石雨', '箭雨', '炮弹齐射', '雷暴', '轨道打击', '兽群奔袭', '孢子云', '火炮齐射', '舷炮齐射',
  '核爆', '无人机蜂群', '根须穿刺', '巨兽践踏', '虫群风暴', '舰队炮击', '空袭', '远征炮击'];
// 大招落地特效：boom 爆炸 / bolt 闪电 / beam 光束
// 大招落下来的弹体外观（js/render/arms.js drawShells）：meteor 火球 / arrow 箭 / shell 炮弹 / nuke 核弹 / spore 孢子团 / drone 无人机 / bolt 只有电光预警 / beam 只有瞄准激光
const SHELL_STYLE = ['meteor', 'arrow', 'shell', 'bolt', 'beam', 'meteor', 'spore', 'shell', 'shell', 'nuke', 'drone', 'spore', 'meteor', 'spore', 'shell', 'shell', 'shell'];
// 大招落点特效（pixelfx，fx.js 的 spawnHitFx）：按 SHELL_STYLE 选，[名字, 缩放]
// burn / puddle 是留在地上的燃烧圈 / 毒池，画在兵脚下（fx.js FX_UNDER）
const SHELL_LAND = {
  meteor: [['meteor', 1], ['burn', 1]],
  arrow:  [['dirt', 0.8]],
  shell:  [['big', 0.85], ['slam', 1], ['burn', 1]],
  nuke:   [['nuke', 1.1], ['slam', 1.3], ['burn', 1.3]],
  beam:   [['pillar', 1], ['plasma', 1.3]],
  drone:  [['emp', 1.3], ['boom', 0.7]],
  spore:  [['burst', 1], ['spore', 1.4], ['puddle', 2.2]],
  bolt:   [['strike', 1], ['thunder', 0.9]],
};
// 弹道外观（设计见 design/quick-specs/projectile-styles.md）：每个时代 [射手, 炮兵, 轻塔, 中塔, 重塔]
//   f 飞行体（FX_META 里 kind:'fly' 的名字）；s 飞行体缩放；h 命中特效（FX_META 里的受击 / 爆炸）；m 炮口火光（kind:'muzzle'）
//   beam 瞬发，不飞：arc 电弧 / chain 连锁闪电 / vine 藤鞭 / ray 光束；swarm 一群小虫（颜色），n 只数
//   不写 h：单体命中用 spark，溅射用 dirt
const PROJ_STYLE = [
  /* 0 部落 */ [{ f: 'stone', h: 'blunt' }, { f: 'boulder', h: 'dirt' }, { f: 'stone' }, { f: 'bone', h: 'crit' }, { f: 'boulder', s: 1.3, h: 'dirt' }],
  /* 1 青铜 */ [{ f: 'arrow' }, { f: 'boulder', h: 'dirt' }, { f: 'arrow', s: 0.8 }, { f: 'arrow', s: 1.4, h: 'crit' }, { f: 'boulder', s: 1.5, h: 'dirt' }],
  /* 2 蒸汽 */ [{ f: 'tracer', m: 'm_pistol' }, { f: 'ball', m: 'm_cannon', h: 'boom' }, { f: 'tracer', m: 'm_smg' }, { f: 'ball', m: 'm_cannon', h: 'bullet' }, { f: 'ball', s: 1.3, m: 'm_cannon', h: 'dirt' }],
  /* 3 电气 */ [{ f: 'tracer_b', m: 'm_pistol' }, { f: 'ball', s: 0.8, h: 'grenade' }, { beam: 'arc', h: 'zap' }, { beam: 'chain', h: 'zap' }, { f: 'laser_b', s: 1.4, h: 'plasma' }],
  /* 4 机甲 */ [{ f: 'plasma_b' }, { f: 'laser_b', s: 1.6, h: 'plasma' }, { f: 'laser' }, { f: 'plasma_b', s: 1.4, h: 'plasma' }, { f: 'void', h: 'implode' }],
  /* 5 驯兽 */ [{ f: 'dart', h: 'acid' }, { f: 'arrow_g', h: 'acid' }, { f: 'thorn' }, { f: 'arrow_g', h: 'acid' }, { swarm: '#f2c94c', n: 6, h: 'acid' }],
  /* 6 生化 */ [{ f: 'sting', h: 'acid' }, { f: 'plasma_s', h: 'spore' }, { f: 'plasma_a', s: 0.7 }, { f: 'plasma_a', h: 'acid' }, { f: 'plasma_s', s: 1.4, h: 'spore' }],
  /* 7 火药 */ [{ f: 'tracer', m: 'm_pistol' }, { f: 'ball', m: 'm_cannon', h: 'dirt' }, { f: 'tracer' }, { f: 'tracer', m: 'm_shotgun' }, { f: 'ball', s: 1.3, m: 'm_cannon', h: 'boom' }],
  /* 8 帆船 */ [{ f: 'tracer', m: 'm_pistol' }, { f: 'ball', m: 'm_cannon', h: 'boom' }, { f: 'tracer' }, { f: 'ball', s: 0.8, m: 'm_cannon', h: 'bullet' }, { f: 'ball', s: 1.5, m: 'm_cannon', h: 'big' }],
  /* 9 核能 */ [{ f: 'laser_g' }, { f: 'rocket', s: 0.8, h: 'nuke' }, { f: 'laser_g', s: 0.8 }, { f: 'plasma_g', s: 1.3, h: 'plasma' }, { f: 'plasma_g', s: 1.7, h: 'nuke' }],
  /* 10 智械 */ [{ f: 'disc' }, { f: 'rocket', s: 0.7, h: 'grenade' }, { f: 'tracer_c', m: 'm_smg' }, { f: 'rocket', s: 0.6, h: 'boom' }, { beam: 'ray', h: 'plasma' }],
  /* 11 共生 */ [{ f: 'arrow_t' }, { f: 'seed', h: 'spore' }, { beam: 'vine' }, { f: 'thorn', s: 1.3, h: 'acid' }, { f: 'boulder_w', s: 1.4, h: 'dirt' }],
  /* 12 巨兽 */ [{ f: 'bone', h: 'crit' }, { f: 'fireball', h: 'boom' }, { f: 'bone', s: 0.7 }, { f: 'bone', s: 1.3, h: 'crit' }, { f: 'fireball', s: 1.5, h: 'dirt' }],
  /* 13 蜂群 */ [{ f: 'sting' }, { f: 'plasma_a', h: 'acid' }, { swarm: '#f2c94c', n: 3 }, { f: 'sting', s: 1.3, h: 'acid' }, { swarm: '#f2c94c', n: 9, h: 'spore' }],
  /* 14 铁甲舰 */ [{ f: 'tracer', m: 'm_pistol' }, { f: 'ball', s: 1.4, m: 'm_cannon', h: 'big' }, { f: 'tracer', m: 'm_smg' }, { f: 'ball', s: 0.8, m: 'm_cannon', h: 'boom' }, { f: 'ball', s: 1.4, m: 'm_cannon', h: 'barrel' }],
  /* 15 航空 */ [{ f: 'tracer', s: 1.3, m: 'm_pistol' }, { f: 'ball', s: 0.8, h: 'grenade' }, { f: 'tracer', m: 'm_smg' }, { f: 'tracer_y', h: 'grenade' }, { f: 'bomb', h: 'boom' }],
  /* 16 远征 */ [{ f: 'tracer_y', m: 'm_pistol' }, { f: 'ball', s: 1.3, m: 'm_cannon', h: 'big' }, { f: 'tracer' }, { f: 'ball', m: 'm_cannon', h: 'bullet' }, { f: 'rocket_y', s: 0.8, h: 'barrel' }],
];
/** 一发弹道用哪种外观：tower 0 = 兵（attType 1 射手 / 4 炮兵），1–3 = 轻 / 中 / 重塔 */
const projStyle = (age, attType, tower) => PROJ_STYLE[age][tower ? 1 + tower : (attType === 4 ? 1 : 0)];
const BEAM_T = 0.12;   // 瞬发类从开火到命中的秒数
const UNIT_BASE = [
  { price: 15, hp: 60, atk: 10, range: 30, rate: 1.0, speed: 80, train: 1.5, w: 22, h: 44 },                          // 步兵
  { price: 25, hp: 40, atk: 8, range: 220, rate: 1.2, speed: 80, train: 2.0, w: 20, h: 42, ranged: true },            // 射手
  { price: 40, hp: 60, atk: 28, range: 30, rate: 0.9, speed: 140, train: 2.5, w: 36, h: 48 },                         // 骑兵
  { price: 100, hp: 300, atk: 28, range: 40, rate: 1.5, speed: 55, train: 4.0, w: 46, h: 44 },                        // 重装
  { price: 70, hp: 50, atk: 16.5, range: 340, minRange: 80, rate: 3.0, speed: 55, train: 3.5, w: 34, h: 34, ranged: true, splash: 50 }, // 炮兵
  { price: 85, hp: 70, atk: 16, range: 120, rate: 1.2, speed: 110, train: 3.5, w: 34, h: 30, ranged: true, air: true }, // 空军
];
const TOWER_BASE = [
  { price: 90, atk: 6, range: 300, rate: 0.5, splash: 0 },
  { price: 160, atk: 14, range: 340, rate: 1.0, splash: 0 },
  { price: 280, atk: 30, range: 380, rate: 2.0, splash: 60 },
];
const EVOLVE = [{ gold: 540 }, { gold: 1290 }, { gold: 2340 }, { gold: 3900 }];   // 玩家进入下一个时代的金币
// 科技点：击杀得经验，经验攒满一格立刻得 1 点（经验条清零重攒）。玩家和 AI 同一套，不再按时钟拖延发点。
// 每个时代的前 PT_FREE 点（够跃迁）按 PT_EXP 算；之后每多 1 点，这一格要的经验多 PT_STEP 倍（按比例变贵），跃迁后重置
const PT_EXP = [300, 800, 1200, 1500, 2850];
const PT_FREE = 4, PT_STEP = 1.0;
const ptNeed = sd => Math.round(PT_EXP[sd.age] * (1 + PT_STEP * Math.max(0, sd.got - (PT_FREE - 1))));
const ERA_PTS = 4;                                // 进入新时代要花的科技点
const BASE_HP = [2000, 3200, 4800, 7200, 10000];
// 每秒自动金币，随时代提高。2026-11-12：后期金币增速太快，第 4、5 个时代 13/20 → 12/16
const INCOME = [3, 5, 8, 12, 16];
const START_GOLD = 150;
const KILL_EXP = 2;                              // 击杀经验：敌兵价格 ×2
// 防御塔打死的兵，击杀金币和经验都只给这个比例。塔打不掉、不花维护费，全额奖励会让"只修塔不出兵"滚雪球
const TOWER_KILL_REWARD = 0.5;
// 大招炸死的兵同理：大招不花钱、冷却一好就能清一波，全额奖励会让"不出兵、靠大招清兵"也能滚雪球
const SPECIAL_KILL_REWARD = 0.5;
// AI 落后时的额外追赶：击杀经验倍率和自动金币倍率。
const CATCH_UP = { easy: { exp: 2, gold: 1.15 }, normal: { exp: 3, gold: 1.3 }, hard: { exp: 3, gold: 1.4 } };
const DIFF_NAME = { easy: '简单', normal: '普通', hard: '困难' };
// TapTap 广告总开关，SDK 接入见 js/ui/ads.js。
const ADS_ON = true;
const SLOT_COST = [0, 300, 800, 1600];
// 采矿场（设计文档 6.5）：3 级，每级自动金币 +15%
const MINE_COST = [150, 400, 900], MINE_BONUS = 0.15;
// 练兵场（design/quick-specs/training-ground.md）：3 级，每级让之后训练的兵生命和攻击各 +6%；升时代保留
const DRILL_COST = [200, 500, 1000], DRILL_BONUS = 0.06;
const AI_DRILL_T = 60;   // 普通 AI：开局多少秒后开始为练兵场 Lv1 存钱（js/core/ai.js）
// 防御塔强化（6.3）：每座塔 2 级，花费 = 塔价 ×0.6 / ×1.0，每级攻击 +30%、射程 +10%
const TOWER_UPG = [0.6, 1.0];         // 解锁第 n+1 个塔位的价格
const SPECIAL_CD = 60, SPECIAL_SHELLS = 20, SPECIAL_TIME = 3, SPECIAL_RADIUS = 60;
// AI 放大招：敌兵离自家门口多近算"压到家门口"（像素）；大招好了以后最多囤多少秒（普通 / 困难）
const AI_SP_GATE = 450, AI_SP_HOLD = 15;
// 出兵策略：六兵种基础权重、克制意识、重复兵种抑制；安全时可为贵兵存钱，开局和告急时缩短等待。
// siegeWait：被堵门时最多为选中的克制兵种攒几秒钱；blockEvery：门口没有前排时，每隔几秒才补一个步兵顶住，剩下的钱留给克制兵种。
// towerWait：被堵门且一座塔都没有时，最多停几秒出兵去攒一座轻塔（简单难度不这样做）。
const AI_RECRUIT = {
  easy: { weights: [1.4, 1.2, 1, 0.7, 0.75, 1], counter: 0.25, diversity: 0.4, antiAir: 1, wait: 30, openingWait: 4, queue: 2, siegeWait: 8, blockEvery: 5, towerWait: 0 },
  normal: { weights: [1.2, 1, 0.9, 0.8, 0.9, 1.25], counter: 0.8, diversity: 0.75, antiAir: 3, wait: 30, openingWait: 5, queue: 2, siegeWait: 14, blockEvery: 3, towerWait: 10 },
  hard: { weights: [1.1, 1, 1, 0.9, 1, 1.3], counter: 1.1, diversity: 0.9, antiAir: 4, wait: 30, openingWait: 5, queue: 2, siegeWait: 18, blockEvery: 3, towerWait: 10 },
};
const EVOLVE_TIME = 3;
const AI_TOWER_MAX = 4, AI_TOWER_KEEP = 2;   // AI 按时代保持的塔数上限；攒塔钱时场上至少留几个兵（js/core/ai.js）
// 科技节点（设计文档 6.4）：挂在各个时代下面，进入过那个时代才能点；每个时代 2 个
// 部落纪、青铜纪改为三选一（design/quick-specs/early-tech-routes-ads.md 2.2）：group 相同的只能点一个；
// dir：atk 进攻 / eco 经济 / def 防守（科技树卡片颜色）；bad：代价（红字显示）
const PERKS = [
  { id: 'hunt', era: 0, cost: 1, group: 'e0', dir: 'atk', name: '狩猎号角', desc: '步兵和骑兵攻击 +20%', ap: m => { m.atk[0] *= 1.2; m.atk[2] *= 1.2; } },
  { id: 'income', era: 0, cost: 1, group: 'e0', dir: 'eco', name: '火种矿脉', desc: '自动金币 +10%', ap: m => { m.income *= 1.1; } },   // 三选一里只有经济项带代价玩家会绕开，改为无代价、小加成（early-tech-routes-ads.md 第 9 节）
  { id: 'inf', era: 0, cost: 1, group: 'e0', dir: 'def', name: '盾墙', desc: '步兵生命 +40%', ap: m => { m.hp[0] *= 1.4; } },
  { id: 'train', era: 1, cost: 1, group: 'e1', dir: 'atk', name: '流水线', desc: '所有兵训练时间 −25%', ap: m => { m.train *= 0.75; } },
  { id: 'price', era: 1, cost: 1, group: 'e1', dir: 'eco', name: '精打细算', desc: '所有兵价格 −10%', ap: m => { m.price *= 0.9; } },
  { id: 'hold', era: 1, cost: 1, group: 'e1', dir: 'def', name: '坚守', desc: '自家门口的兵受伤再 −15%', ap: m => { m.home *= 0.85; } },
  { id: 'tower', era: 2, cost: 1, name: '要塞工程', desc: '防御塔攻击 +30%，射程 +15%', ap: m => { m.towerAtk *= 1.3; m.towerRange *= 1.15; } },
  { id: 'hvy', era: 2, cost: 2, name: '铁壁', desc: '重装生命 +35%，攻击 +15%', ap: m => { m.hp[3] *= 1.35; m.atk[3] *= 1.15; } },
  { id: 'art', era: 3, cost: 1, name: '弹道学', desc: '炮兵攻击 +25%，爆炸范围 +40%', ap: m => { m.atk[4] *= 1.25; m.splash *= 1.4; } },
  { id: 'wall', era: 3, cost: 2, name: '加固城墙', desc: '基地受到的伤害 −25%', ap: m => { m.armor *= 0.75; } },
  { id: 'cav', era: 5, cost: 1, name: '疾风', desc: '骑兵速度 +30%，攻击 +20%', ap: m => { m.speed[2] *= 1.3; m.atk[2] *= 1.2; } },
  { id: 'bounty', era: 5, cost: 2, name: '战利品', desc: '击杀获得的金币 +50%', ap: m => { m.bounty *= 1.5; } },
  { id: 'regen', era: 6, cost: 1, name: '自愈组织', desc: '所有兵每秒再回复 1.5% 生命', ap: m => { m.regen += 0.015; } },
  { id: 'exp', era: 6, cost: 2, name: '解读者', desc: '击杀经验 +30%，科技点来得更快', ap: m => { m.exp *= 1.3; } },
  { id: 'arc', era: 7, cost: 1, name: '鹰眼', desc: '射手射程 +25%，攻击 +20%', ap: m => { m.range[1] *= 1.25; m.atk[1] *= 1.2; } },
  { id: 'fire', era: 7, cost: 2, name: '火力覆盖', desc: '大招冷却 −20 秒，炮弹 +6 发', ap: m => { m.spCd += 20; m.spShells += 6; } },
  { id: 'trade', era: 8, cost: 1, name: '远洋贸易', desc: '自动金币 +15%', ap: m => { m.income *= 1.15; } },
  { id: 'march', era: 8, cost: 2, name: '登陆战', desc: '所有兵移动速度 +15%，攻击 +10%', ap: m => { for (let i = 0; i < UNIT_BASE.length; i++) { m.speed[i] *= 1.15; m.atk[i] *= 1.1; } } },
  // 最终时代：每个 2 个，2 点 / 3 点
  { id: 'orbit', era: 4, cost: 2, name: '轨道校准', desc: '大招每发伤害 +50%', ap: m => { m.spDmg *= 1.5; } },
  { id: 'mecha', era: 4, cost: 3, name: '机甲核心', desc: '重装攻击 +30%，炮兵生命 +30%', ap: m => { m.atk[3] *= 1.3; m.hp[4] *= 1.3; } },
  { id: 'chain', era: 9, cost: 2, name: '链式反应', desc: '炮兵攻击 +25%，爆炸范围 +50%', ap: m => { m.atk[4] *= 1.25; m.splash *= 1.5; } },
  { id: 'reactor', era: 9, cost: 3, name: '反应堆', desc: '自动金币 +20%', ap: m => { m.income *= 1.2; } },
  { id: 'drone', era: 10, cost: 2, name: '无人机护航', desc: '射手射程 +20%，攻击 +20%', ap: m => { m.range[1] *= 1.2; m.atk[1] *= 1.2; } },
  { id: 'omni', era: 10, cost: 3, name: '全知', desc: '所有兵攻击和生命 +12%', ap: m => { for (let i = 0; i < UNIT_BASE.length; i++) { m.atk[i] *= 1.12; m.hp[i] *= 1.12; } } },
  { id: 'bark', era: 11, cost: 2, name: '硬化树皮', desc: '步兵和重装生命 +30%', ap: m => { m.hp[0] *= 1.3; m.hp[3] *= 1.3; } },
  { id: 'root', era: 11, cost: 3, name: '根系网络', desc: '防御塔攻击 +35%，射程 +15%', ap: m => { m.towerAtk *= 1.35; m.towerRange *= 1.15; } },
  { id: 'alpha', era: 12, cost: 2, name: '兽王', desc: '骑兵速度 +25%，生命 +25%', ap: m => { m.speed[2] *= 1.25; m.hp[2] *= 1.25; } },
  { id: 'rage', era: 12, cost: 3, name: '狂暴', desc: '所有兵攻击 +15%', ap: m => { for (let i = 0; i < UNIT_BASE.length; i++) m.atk[i] *= 1.15; } },
  { id: 'acid', era: 13, cost: 2, name: '强酸', desc: '炮兵攻击 +30%', ap: m => { m.atk[4] *= 1.3; } },
  { id: 'brood', era: 13, cost: 3, name: '虫巢', desc: '所有兵训练时间 −30%', ap: m => { m.train *= 0.7; } },
  { id: 'steel', era: 14, cost: 2, name: '装甲钢', desc: '重装和骑兵生命 +30%', ap: m => { m.hp[3] *= 1.3; m.hp[2] *= 1.3; } },
  { id: 'bigGun', era: 14, cost: 3, name: '大口径', desc: '防御塔攻击 +40%', ap: m => { m.towerAtk *= 1.4; } },
  { id: 'scout', era: 15, cost: 2, name: '侦察机', desc: '射手和炮兵射程 +20%', ap: m => { m.range[1] *= 1.2; m.range[4] *= 1.2; } },
  { id: 'bomb', era: 15, cost: 3, name: '地毯轰炸', desc: '大招冷却 −20 秒，炮弹 +8 发', ap: m => { m.spCd += 20; m.spShells += 8; } },
  { id: 'merc', era: 16, cost: 2, name: '雇佣兵', desc: '所有兵价格 −15%', ap: m => { m.price *= 0.85; } },
  { id: 'conquest', era: 16, cost: 3, name: '征服', desc: '所有兵攻击和生命 +10%', ap: m => { for (let i = 0; i < UNIT_BASE.length; i++) { m.atk[i] *= 1.1; m.hp[i] *= 1.1; } } },
];
const perkById = id => PERKS.find(p => p.id === id);
function mkMod() {
  return { hp: UNIT_BASE.map(() => 1), atk: UNIT_BASE.map(() => 1), range: UNIT_BASE.map(() => 1), speed: UNIT_BASE.map(() => 1), splash: 1, train: 1, price: 1,
    income: 1, exp: 1, bounty: 1, towerAtk: 1, towerRange: 1, armor: 1, spCd: 0, spShells: 0, regen: 0, spDmg: 1,
    home: 1, spLock: false, spore: false };   // home：主场受伤倍数（坚守）；spLock：大招锁定（机械线）；spore：阵亡孢子（生物线）
}
// 决战：双方都到最终时代 FINAL_DELAY 秒后，方舟塔苏醒，打破僵局
// 不再让双方基地被动掉血（血少的一方会必输）；只让打基地的伤害每分钟 +50%，谁打得进去谁赢
const FINAL_DELAY = 25, FINAL_DMG_GROW = 0.5;
// 克制环：步兵 → 骑兵 → 炮兵 → 重装 → 射手 → 步兵（箭头指向被克制的一方）
const BEATS = [2, 0, 4, 1, 3, -1];    // 空军不属于原来的五兵克制环
const BEATEN_BY = [1, 3, 0, 4, 2, 1]; // 射手额外克制空军；空军之间互打，没有克制加成
const COUNTER_BONUS = 1.6;
const TYPE_DESC = [
  '步兵：便宜耐打，克制骑兵，怕射手',
  '射手：远程，能对空，克制步兵和空军，怕重装',
  '骑兵：移动快、攻击高，克制炮兵，怕步兵',
  '重装：血厚，克制射手，怕炮兵',
  '炮兵：远程溅射，有贴身盲区，克制重装，怕骑兵',
  '空军：独立飞行队列，能打地面兵和敌方空军；怕射手、防御塔和大招，攻基地伤害减半',
];
const TOWER_DESC = ['轻塔：射速快、伤害低', '中塔：均衡', '重塔：慢速、范围伤害'];
const ECHO_LINES = [
  '',
  '又快了一步……你确定前面不是悬崖吗？',
  '你们走得越快，就离上一次越近。',
  '电流在唱歌。两百年前，它也是这么唱的。',
  '你们造出了比自己更强的身体。下一步呢？',
  '你们驯服了野兽……也会驯服彼此吗？',
  '血肉也能被改写。上一次，他们改写了太多。',
  '火药让弱者也能杀死强者。这是礼物，还是诅咒？',
  '你们驶向远方。可远方，也有人在等着你们。',
  '你们点亮了太阳的碎片。上一次，天空就是这样熄灭的。',
  '机器学会了思考。它们会记得是谁造了它们吗？',
  '你们和森林长在了一起。这条路，上一次没人走过。',
  '最大的野兽，往往最先饿死。',
  '一万只虫子，只有一个念头。你们呢？',
  '船越造越大，海却没有变宽。',
  '你们飞上了天。从上面看，两边的营地一模一样。',
  '你们走遍了世界。可世界的尽头，还是这片裂谷。',
];
const SIDE_COL = [
  { body: '#e99a2e', dark: '#9c5814', light: '#ffd27a', name: '拾光派' },
  { body: '#8a5cd6', dark: '#4a2c8c', light: '#6fe3e3', name: '余烬派' },
];
const AGE_COL = ['#8b5a2b', '#d08a3a', '#6f7a86', '#4fb3ff', '#5ff7ff', '#6fbf4a', '#a6ff4d', '#c0392b', '#2e86c1',
  '#b6ff3b', '#9ad0ff', '#3fbf7f', '#e0703a', '#f2c12e', '#7f8c99', '#7fc8ff', '#e6b422'];
const SKY = [
  ['#7ec4f2', '#d9f0ff'], ['#f0a865', '#fde3be'], ['#8f939e', '#d2d0c8'], ['#27325c', '#6c79a8'], ['#090720', '#2b1f55'],
  ['#9fd39a', '#e6f5d0'], ['#3c5a3a', '#a8c98a'], ['#c9b08a', '#f3e6cc'], ['#6fb6d9', '#e0f3fb'],
  ['#1e2a14', '#5d7a2e'], ['#101826', '#3a4a66'], ['#7fc9a0', '#dff5e4'], ['#e3a36a', '#f6dcb4'], ['#d8c56a', '#f7efc6'],
  ['#7a8fa6', '#d5dde6'], ['#5aa8e8', '#e9f6ff'], ['#e8b86a', '#fff0cc'],
];
const GROUND_COL = ['#8a6a3f', '#9b7444', '#6b6259', '#4a4f5a', '#3a3550', '#5d7a3a', '#3f4a2c', '#7d6440', '#8c7a55',
  '#3d4530', '#363c48', '#3f6a3a', '#6e5a3a', '#7a6a32', '#5d5a52', '#8a8a5a', '#9a7a4a'];
const isNight = era => era === 3 || era === 4 || era === 9 || era === 10;

let PRICE_GROW = 1.7, STAT_GROW = 1.6;            // 每个时代：价格倍数 / 生命和攻击倍数
const pow2 = a => Math.pow(PRICE_GROW, a), pow22 = a => Math.pow(STAT_GROW, a);
const roundPrice = v => Math.max(5, Math.round(v / 5) * 5);
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const rand = (a, b) => a + Math.random() * (b - a);

// sd 可选：传入一方时叠加它的科技卡效果
// age 参数是时代编号（0–8），数值强度按它是第几个时代算
/**
 * 某一方在某时代训练出的兵的属性（含科技和练兵场加成）。
 * @param {number} type 兵种下标；@param {number} era 时代；@param {object} [sd] 所属一方，省略时为基础属性
 * @param {number} [drill] 练兵场等级，默认取 sd.drill（预览下一级时传入）
 */
function unitStats(type, era, sd, drill = sd ? sd.drill || 0 : 0) {
  const b = UNIT_BASE[type], m = sd ? sd.mod : null, age = ERA_TIER[era];
  const k = (key, v) => m ? v * m[key][type] : v;
  const dr = 1 + DRILL_BONUS * drill;
  const atk = k('atk', b.atk * pow22(age)) * dr;
  return {
    name: UNIT_NAMES[era][type], price: roundPrice(b.price * pow2(age) * (m ? m.price : 1)), hp: Math.round(k('hp', b.hp * pow22(age)) * dr),
    atk: type === 4 ? Math.round(atk * 10) / 10 : Math.round(atk), range: Math.round(k('range', b.range)),
    minRange: b.minRange || 0, rate: b.rate, speed: k('speed', b.speed),
    train: b.train * (m ? m.train : 1),
    w: b.w, h: (type === 3 && ERA_ART[era][3] === 4) ? 64 : b.h, ranged: !!b.ranged, air: !!b.air, splash: (b.splash || 0) * (m ? m.splash : 1),
  };
}
function towerStats(type, era, sd, lvl = 0) {
  const b = TOWER_BASE[type], m = sd ? sd.mod : null, age = ERA_TIER[era];
  return { name: TOWER_NAMES[era][type], price: roundPrice(b.price * pow2(age)),
    atk: Math.round(b.atk * pow22(age) * (m ? m.towerAtk : 1) * Math.pow(1.3, lvl)),
    range: Math.round(b.range * (m ? m.towerRange : 1) * Math.pow(1.1, lvl)), rate: b.rate, splash: b.splash };
}
const upgCost = t => t.lvl >= 2 ? null : roundPrice(towerStats(t.type, t.age).price * TOWER_UPG[t.lvl]);
const sellValue = t => Math.round((towerStats(t.type, t.age).price + t.spent) * 0.5);
// 大招每发伤害（按第几个时代）。部落纪原来 30，一次大招能直接炸死猛犸骑手，下调
const SPECIAL_DMG = [15, 28, 55, 95, 170];
const specialDmg = era => SPECIAL_DMG[ERA_TIER[era]];
const HEAVY_SP_CAP = 0.4;   // 重装一次大招最多掉 40% 最大生命（重装要扛得住）
// 克制：打被自己克制的兵种 ×1.6；塔（att = -1）没有克制
function counterMult(att, def) {
  return att >= 0 && (BEATS[att] === def || (att === 1 && def === 5)) ? COUNTER_BONUS : 1;
}
