/* ==========================================================
   基因侦探 · 侦探须知手册（科普页）
   ----------------------------------------------------------
   一本书，不是一列卡片：
     · 合着 → 点「点击查看手册」/ 封面 → 封面绕书脊转 180° 翻开
     · 翻开后：左页正文（探长开场 → 正文），右页要点 + 图示 + 已读
     · 目录只列题目，点条目翻到那一页；内容只存在于具体页上
     · 翻页动效：一张「纸」绕书脊转 180°，正反两面分别是前后两页
        前进：正面 = 当前右页，背面 = 下一页左页
        后退：正面 = 上一跨页右页，背面 = 当前左页
     · 「已读」→ localStorage gd_manual_<id>（键名不能改，改了等于清零）
        标记已读后「去接第 N 案」的路引才亮
   约束：无外部库；localStorage 全部 try/catch；
        翻页结束一律由 setTimeout 收尾（无头环境不产帧，transitionend 不可靠）。
   ========================================================== */
(function (window, document) {
  'use strict';

  /* ---------- localStorage 兜底 ---------- */
  function lsGet(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function lsSet(key, val) { try { localStorage.setItem(key, val); } catch (e) { /* 隐私模式 */ } }

  /* 键名与计数顺序一个都不能改 */
  var MANUAL_IDS = ['c0', 'c1', 'c2', 'c3', 'c5', 'c8', 'c6', 'c7', 'c4'];
  /* 手册页序（第 1 页 → 第 7 页），与上面的计数顺序不同，别混 */
  var ORDER = ['c0', 'c1', 'c2', 'c3', 'c5', 'c8', 'c6', 'c7', 'c4'];

  /* 归档键按账号隔离：同名键会被不同账号互相「串读」。
     用当前用户名做命名空间，未登录兜底 'guest'，避免换号后误显示已读。 */
  function userNs() {
    var u = '';
    try { u = (window.GD && GD.getUser()) || ''; } catch (e) { u = ''; }
    return u || 'guest';
  }
  function archKey(id) {
    return 'gd_manual_' + userNs() + '_' + id;
  }
  function isArchived(id) { return lsGet(archKey(id)) === '1'; }
  function countArchived() {
    var n = 0;
    MANUAL_IDS.forEach(function (id) { if (isArchived(id)) n++; });
    return n;
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function attr(s) {
    return esc(s).replace(/"/g, '&quot;');
  }
  /* 「｜」只当停顿标记，不落到屏幕上 */
  function plain(s) { return String(s).replace(/｜/g, ''); }

  /* 术语标注（terms.js）：专有名词着色 + 定义短语高亮。
     模块缺失时退化成纯文本，页面照样能读。 */
  var TM = window.GDTerms || null;
  function tmHTML(s) { return TM ? TM.html(s) : esc(s); }
  function tmBuild(el, raw) {
    if (TM) return TM.build(el, raw);
    el.textContent = '';
    return [{ el: el, s: String(raw) }];
  }
  function tmFill(frags) {
    if (TM) { TM.fill(frags); return; }
    (frags || []).forEach(function (f) { f.el.textContent = plain(f.s); });
  }

  var REDUCE = false;
  try { REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { REDUCE = false; }

  /* ==========================================================
     九页内容
     ========================================================== */
  var PAGES = {
    c0: {
      no: 1, name: '什么是基因', hook: 'DNA、基因、染色体、蛋白',
      chip: '必读', kind: 'must', time: '约 2 分钟',
      open: '本页先明确四个基础概念。｜后面的所有内容都以它们为基础。',
      body: ['人体由细胞组成，细胞核内储存遗传物质 __DNA__。｜DNA 由 A、T、C、G 四种碱基组成，总长约 30 亿对。｜DNA 上具有功能的一段序列称为***基因***（人类约 2 万个），｜基因指导合成蛋白，由蛋白执行各项生理功能。'],
      points: [
        { t: '染色体', d: '46 条（23 对），DNA 的包装形式' },
        { t: '基因', d: '有功能的DNA 片段，人类约 2 万个' },
        { t: '蛋白', d: '基因的产物，执行各项生理功能' }
      ],
      tail: '下一页：测序与质量。', caseNo: 0
    },
    c1: {
      no: 2, name: '测序与质量', hook: '读段与 Q 值',
      chip: '必读', kind: 'must', time: '约 3 分钟',
      open: '本页解释测序数据的结构。｜案件一将练习本页的修剪操作。',
      body: ['测序仪一次读不完整个基因组，｜而是把 __DNA__ 打断为**大量短片段**分别测定，｜每个片段称为一条__读段__（read）。｜读段中每个__碱基__都附带__质量分值__（Q 值），｜表示该碱基的可靠程度。'],
      points: [
        { t: '读段（read）', d: '测序仪逐段测定产生的短片段' },
        { t: 'Q 值', d: '每个碱基的可靠度评分：Q ≥ 28 可靠，Q < 20 不可靠' },
        { t: '修剪', d: '剪除集中在读段末端的__低质量碱基__，避免误判变异' }
      ],
      tail: '案件一练习读段修剪。', caseNo: 1
    },
    c2: {
      no: 3, name: '序列比对', hook: '错配 SNV 与缺失 Indel',
      chip: '必读', kind: 'must', time: '约 3 分钟',
      open: '本页说明比对的原理。｜案件二将练习缺失序列的定位。',
      body: ['比对是把患者序列与人类__参考基因组__逐位对齐的过程。｜同一位置碱基不同，称为__错配__（SNV）；｜缺失或插入碱基，称为***Indel***。｜Indel 会使下游碱基整体错位，｜需在缺口处补__gap__ 后重新对齐。'],
      points: [
        { t: '参考序列', d: '人类基因组标准版，用作对照' },
        { t: '错配（SNV）', d: '同一位置碱基不同' },
        { t: '缺失/插入（Indel）', d: '下游碱基整体错位，需补 gap 重新对齐' }
      ],
      tail: '案件二练习缺失的比对定位。', caseNo: 2
    },
    c3: {
      no: 4, name: '变异与致病性', hook: '三类证据判定致病性',
      chip: '必读', kind: 'must', time: '约 4 分钟',
      open: '本页给出致病性的判定规则。｜案件三将完整练习一次判定。',
      body: ['健康人之间也存在数百万处序列差异，多数无害。｜判断一个变异是否致病，依据**三类证据**：｜__人群频率__（有多罕见）、__蛋白功能预测__（多有害）、__文献报道__（是否被反复记录）。'],
      points: [
        { t: '人群频率', d: '< 0.1% 支持致病；> 1% 支持良性' },
        { t: '功能预测分', d: '≥ 0.8 支持致病；≤ 0.3 支持良性' },
        { t: '意义不明（VUS）', d: '三类证据方向冲突时的诚实结论' }
      ],
      tail: '案件三练习对三个变异的判定。', caseNo: 3
    },
    c5: {
      no: 5, name: '密码子翻译', hook: '三个碱基对应一个氨基酸',
      chip: '必读', kind: 'must', time: '约 2 分钟',
      open: '本页说明从 DNA 到氨基酸的翻译规则。｜案件四将练习一段序列的翻译。',
      body: ['翻译以 3 个碱基为一组进行，每组称为一个***密码子***，｜对应 1 个__氨基酸__。｜翻译从__起始密码子 ATG__ 开始，｜到__终止密码子__（TAA / TAG / TGA）结束。'],
      points: [
        { t: '密码子', d: '3 个碱基一组，对应 1 个氨基酸' },
        { t: 'ATG 与终止子', d: 'ATG＝起始；TAA / TAG / TGA＝终止' },
        { t: '移码突变', d: '阅读框架错位，通常严重影响蛋白功能' }
      ],
      tail: '案件四练习 5 组密码子的翻译。', caseNo: 4
    },
    c8: {
      no: 6, name: '系谱判读', hook: '三个问题确定遗传方式',
      chip: '必读', kind: 'must', time: '约 2 分钟',
      open: '本页说明系谱图的判读方法。｜案件五将练习一份三代系谱。',
      body: ['__系谱图__记录家族各代成员的患病情况。｜判断遗传方式依次确认三点：｜是否逐代连续传递、男女是否均患病、是否存在**父传子**。'],
      points: [
        { t: '显性 / 隐性', d: '逐代传递为显性；隔代出现为隐性' },
        { t: '常染色体 / X 连锁', d: '男女均患病为常染色体；仅男性患病警惕 X 连锁' },
        { t: '线粒体遗传', d: '仅经母亲传递；出现父传子即可排除' }
      ],
      tail: '案件五练习三代系谱判读。', caseNo: 5
    },
    c6: {
      no: 7, name: '医学 AI 的应用', hook: '影像判读 / 蛋白结构 / 药物筛选',
      chip: '可跳过', kind: 'ext', time: '约 2 分钟',
      open: '本页补充医学 AI 的其他应用。｜案件三的评分器只是其中一种。',
      body: ['医学 AI 的应用不止变异解读：｜眼底照片与肺结节的影像判读、｜**蛋白三维结构预测**（AlphaFold）、｜药物分子初筛，均已投入实际使用。'],
      points: [
        { t: '影像判读', d: '眼底照片、肺结节筛查已投入实际使用' },
        { t: 'AlphaFold', d: '由氨基酸序列预测蛋白三维结构' },
        { t: '人机分工', d: 'AI 负责初筛，医生负责最终诊断' }
      ],
      tail: '', caseNo: 0
    },
    c7: {
      no: 8, name: '基因检测的应用', hook: '产前筛查 / 靶向用药 / 罕见病',
      chip: '建议读', kind: '', time: '约 2 分钟',
      open: '本页列举基因检测的现实应用。｜案件六即是其中一种。',
      body: ['__无创产前筛查__（NIPT）通过孕妇外周血检测胎儿染色体异常；｜肿瘤患者**先做基因检测、再选择靶向药**；｜测序也用于罕见病的病因定位。'],
      points: [
        { t: 'NIPT', d: '孕妇外周血筛查胎儿染色体异常' },
        { t: '靶向药', d: '先检测基因确认突变，再针对性用药' },
        { t: '风险报告', d: '消费级检测结论需理性解读' }
      ],
      tail: '', caseNo: 6
    },
    c4: {
      no: 9, name: '从变异到诊断', hook: '五步完整流程',
      chip: '建议读', kind: '', time: '约 2 分钟',
      open: '本页把前面各页串成完整流程。',
      body: ['**基因分析共五步**：｜测序产生读段，｜质控剪除低质量碱基，｜比对定位差异，｜识别变异，｜最后结合证据完成致病性解读。'],
      points: [
        { t: '五步流程', d: '__测序 → 质控 → 比对 → 变异识别 → 解读__' },
        { t: '案件对应', d: '案件一、二、三分别实操其中三步' },
        { t: '医生签发', d: 'AI 负责提速，诊断结论由医生综合判断' }
      ],
      tail: '', caseNo: 0
    }
  };

  /* ==========================================================
     页面 HTML
     p 为「平铺页号」：0 扉页 / 1 目录 / 2,3 = 第 1 页的左右 / … / 14,15
     ========================================================== */
  function runHTML(left, right) {
    return '<div class="pg-run"><b>' + left + '</b><span>' + right + '</span></div>';
  }

  function flyHTML() {
    return '<div class="pg pg-fly">' +
      '<div class="fly-title">侦探须知</div>' +
      '<div class="fly-sub">基因侦探 · 办案手册</div>' +
      '<div class="fly-rule"></div>' +
      '<p class="fly-gift">' +
        '<span data-ty="' + attr('使用建议') + '"></span><br>' +
        '<span data-ty="' + attr('先浏览本手册，再进入案件簿。') + '"></span><br>' +
        '<span data-ty="' + attr('各案件的判定规则都出自本手册。') + '"></span>' +
      '</p>' +
      '<div class="fly-sign"><img src="assets/ip-chen-avatar.jpg" alt="">陈探长<span>· 精准医学侦探社</span></div>' +
      '</div>';
  }

  function tocHTML() {
    var items = ORDER.map(function (id, i) {
      var p = PAGES[id];
      return '<button class="toc-item" type="button" data-goto="' + (i + 1) + '" data-toc="' + id + '">' +
        '<i>0' + (i + 1) + '</i><b>' + esc(p.name) + '</b>' +
        '<span class="ck">✓</span></button>';
    }).join('');

    return '<div class="pg">' +
      runHTML('目录', '<button class="pg-x" type="button" data-close-book aria-label="合上手册">×</button>') +
      '<h3 class="toc-h">目 录</h3>' +
      '<p class="toc-note">只列题目。想看内容，翻过去。</p>' +
      '<div class="toc-list">' + items + '</div>' +
      '</div>';
  }

  function leftHTML(id) {
    var p = PAGES[id];
    /* 正文段落带 data-ty（含「｜」停顿符），由打字机逐字打出 */
    var body = p.body.map(function (t) {
      return '<p class="pg-text" data-ty="' + attr(t) + '"></p>';
    }).join('');
    return '<div class="pg">' +
      runHTML('第 ' + p.no + ' 页', p.time) +
      '<h3 class="pg-title">' + esc(p.name) + '</h3>' +
      '<p class="pg-hook">' + tmHTML(p.hook) + '</p>' +
      '<blockquote class="pg-say"><p data-ty="' + attr(p.open) + '"></p></blockquote>' +
      body +
      '<ol class="pg-points">' + ptsHTML(id) + '</ol>' +
      '<div class="pg-foot"><button class="pg-back" type="button" data-back-toc>返回目录</button>' +
      '<span>' + (p.no * 2) + '</span></div>' +
      '</div>';
  }

  function ptsHTML(id) {
    var p = PAGES[id], NUM = ['一', '二', '三'];
    /* points 的每一项都是 { t: 名词, d: 解释 }，不能直接把对象丢给 esc()，
       否则会渲染成「[object Object]」。编号、名词、解释都带 data-ty——
       typeIn 按 DOM 顺序取任务，要点整条（含「一/二/三」）排在正文后逐字打出。 */
    return p.points.map(function (it, i) {
      return '<li><b data-ty="' + attr(NUM[i] || '·') + '"></b>' +
        ((it && it.t) ? '<em data-ty="' + attr(it.t) + '"></em>' : '') +
        '<span class="pt-d" data-ty="' + attr((it && it.d) || '') + '"></span></li>';
    }).join('');
  }

  function actsHTML(id) {
    var p = PAGES[id];
    var out = '<div class="pg-acts">';
    if (p.caseNo) {
      out += '<a class="act act-try" href="cases.html#case' + p.caseNo + '" data-try="' + id + '">去接第 ' +
        p.caseNo + ' 案<svg class="ic"><use href="#i-arrow"/></svg></a>';
    } else if (id === 'c4') {
      out += '<a class="act act-try" href="cases.html" data-try="' + id + '">去卷宗架' +
        '<svg class="ic"><use href="#i-arrow"/></svg></a>';
    }
    out += '<span class="act act-arch" data-arch="' + id + '">读到这里</span>';
    return out + '</div>';
  }

  function rightHTML(id) {
    var p = PAGES[id];
    return '<div class="pg">' +
      runHTML('图示', '<button class="pg-x" type="button" data-close-book aria-label="合上手册">×</button>') +
      '<div class="pg-fig" data-fig="' + id + '"></div>' +
      (p.tail ? '<p class="pg-tail">' + tmHTML(p.tail) + '</p>' : '') +
      actsHTML(id) +
      '<div class="pg-foot"><span>' + esc(p.name) + '</span><span>' + (p.no * 2 + 1) + '</span></div>' +
      '</div>';
  }

  function pageHTML(p) {
    if (p === 0) return flyHTML();
    if (p === 1) return tocHTML();
    if (p < 0) return '';
    var id = ORDER[(p - 2) >> 1];
    if (!id) return '';
    return p % 2 === 0 ? leftHTML(id) : rightHTML(id);
  }

  /* ==========================================================
     书本状态
     ========================================================== */
  var stage, book, leftEl, rightEl, leafEl, lfFront, lfBack, coverBack,
      badgeEl, deskEl, tbToc, tbClose;

  var TOTAL = ORDER.length + 1;     /* 10 个跨页：扉页/目录 + 九页 */
  var MAXPAGE = TOTAL * 2 - 1;      /* 15 */

  var S = { open: false, page: 0, busy: false };
  var leafTimer = null, coverTimer = null, closeTimer = null;

  /* 案件进度缓存：手册里的「去接第 N 案」要据此判断案件是否已解锁 */
  var progCache = null;
  function loadProg() {
    if (!window.GD || !GD.loadProgress) return;
    try {
      GD.loadProgress().then(function (p) { progCache = p || GD.emptyProgress(); })
        .catch(function () { progCache = null; });
    } catch (e) { progCache = null; }
  }
  /* 第一个未结案的案件号（1~6；全结案返回 7） */
  function firstOpenCase() {
    var p = progCache || (window.GD && GD.emptyProgress ? GD.emptyProgress() : null) || {};
    for (var i = 1; i <= 6; i++) { if (!p['level' + i]) return i; }
    return 7;
  }
  /* 案件 n 是否已解锁（前面全部结案） */
  function caseUnlocked(n) {
    var p = progCache || (window.GD && GD.emptyProgress ? GD.emptyProgress() : null) || {};
    if (p['level' + n]) return true;                 /* 已结案，可重阅 */
    for (var i = 1; i < n; i++) { if (!p['level' + i]) return false; }
    return true;
  }

  function MOBILE() {
    try { return window.matchMedia('(max-width: 900px)').matches; } catch (e) { return false; }
  }

  /* ---------- 小工具 ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    setTimeout(function () { toastEl.classList.add('show'); }, 20);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 3000);
  }

  /* ---------- 渲染 ---------- */
  function fill(root) {
    if (!root) return;
    Array.prototype.forEach.call(root.querySelectorAll('.pg-fig[data-fig]'), function (box) {
      var tpl = document.getElementById('fig-' + box.getAttribute('data-fig'));
      if (tpl && tpl.content) {
        box.innerHTML = '';
        box.appendChild(tpl.content.cloneNode(true));
      }
      /* 图注移出图框：放在 k-fig 下面，别关在色块里 */
      Array.prototype.forEach.call(box.querySelectorAll('.k-fig .fig-cap'), function (cap) {
        cap.parentNode.parentNode.appendChild(cap);
      });
    });
    paintArch(root);
  }

  function setSlot(el, html) {
    if (!el) return;
    el.innerHTML = html || '';
    fill(el);
  }

  function render(typeNow) {
    if (!book) return;
    if (MOBILE()) {
      setSlot(leftEl, '');
      setSlot(rightEl, pageHTML(S.page));
      if (S.open && typeNow !== false) typeIn(rightEl);  /* 跨断点重排后，正文要重新打一遍 */
    } else {
      var s = (S.page >> 1) * 2;
      setSlot(leftEl, pageHTML(s));
      setSlot(rightEl, pageHTML(s + 1));
      if (S.open && typeNow !== false) typeIn(leftEl);
    }
  }

  function paintArch(root) {
    var scope = root || document;
    Array.prototype.forEach.call(scope.querySelectorAll('[data-arch]'), function (b) {
      var on = isArchived(b.getAttribute('data-arch'));
      b.textContent = on ? '✓ 已读' : '读到这里';
      b.classList.toggle('done', on);
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-toc]'), function (a) {
      a.classList.toggle('done', isArchived(a.getAttribute('data-toc')));
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-try]'), function (a) {
      a.classList.toggle('is-off', !isArchived(a.getAttribute('data-try')));
    });
  }

  function paintBadge() {
    if (badgeEl) badgeEl.textContent = '读过 ' + countArchived() + ' / 9';
  }

  /* ---------- 打字机：开场白 + 正文按 DOM 顺序逐字打出（放慢；「｜」为停顿） ---------- */
  var TYPE_MS = 38;        /* 每字间隔 */
  var PAUSE_MS = 430;      /* 「｜」处的停顿 */
  var PARA_MS = 170;       /* 段落之间的间隔 */
  var typeToken = 0;

  function typeIn(root) {
    if (!root) return;
    var els = root.querySelectorAll('[data-ty]');
    /* 先判空再领 token：对没有打字元素的根（如目录页）空跑一次，
       不能把正在进行的打字任务作废——扉页「停在一个字」就是这么来的 */
    if (!els.length) return;
    var my = ++typeToken;                          /* 翻页/重渲后旧任务自动失效 */

    /* 这一页对应的归档 id（正文/要点打完就自动标已读）。
       从 S.page 推导：正文页 id = ORDER[(S.page-2)>>1]。
       扉页(0)/目录页(1) 会得到 undefined，自然不标记。
       （data-arch 按钮在右页，typeIn 打的左页里没有它，不能靠 root 查询） */
    var archId = ORDER[(S.page - 2) >> 1] || null;

    /* 任务队列：一个字一项，项里带着它该落到哪个「片段」上。
       片段由 GDTerms.build 按标注切开（专有名词 / 定义短语 / 关键句），
       所以高亮是跟着打字一起长出来的，不用打完再回填。
       注意别退化成「只 push 元素 + 记当前段第几个字」——那样同一段会被反复重打。 */
    var jobs = [];
    var sets = [];                                 /* 每段一份 frags，供兜底补全 */
    Array.prototype.forEach.call(els, function (el) {
      var raw = el.getAttribute('data-ty') || '';
      var frags = tmBuild(el, raw);
      sets.push({ el: el, frags: frags });
      if (REDUCE) { fillFrags(el, frags, raw); return; }
      if (!frags.length) { el.textContent = plain(raw); return; }
      frags.forEach(function (f, fi) {
        var chars = Array.from(f.s);               /* 代理对不会被拆坏 */
        for (var i = 0; i < chars.length; i++) {
          jobs.push({ el: el, frag: f, ch: chars[i], para: fi === 0 && i === 0 });
        }
      });
    });
    if (REDUCE || !jobs.length) return;

    /* 看门狗：动画链意外中断时，把未打完的段落一次性补全（正常打完则幂等退出）。
       注意：它一旦接管，主链必须停下，否则会在补全的全文后面继续追加，尾巴重复。
       超时时间要按「真实字符数 + 停顿数」算，留足余量（后台标签页定时器会被节流）。 */
    var finished = false;
    var totalMs = 800;
    Array.prototype.forEach.call(els, function (el) {
      var raw = el.getAttribute('data-ty') || '';
      var pauses = (raw.match(/｜/g) || []).length;
      totalMs += (raw.length - pauses) * TYPE_MS + pauses * PAUSE_MS + PARA_MS;
    });
    totalMs = totalMs * 1.8 + 1500;
    var watchdog = setTimeout(function () {
      if (my !== typeToken || finished) return;
      finished = true;                             /* 接管：主链就此停下 */
      sets.forEach(function (s) { fillFrags(s.el, s.frags, s.el.getAttribute('data-ty') || ''); });
      if (archId) archive(archId);                 /* 兜底补全也视为读完 */
    }, totalMs);

    var qi = 0;
    (function step() {
      try {
        if (my !== typeToken || finished) return;    /* 已有新任务 / 已被看门狗接管 */
        if (qi >= jobs.length) { finished = true; clearTimeout(watchdog); if (archId) archive(archId); return; }
        var job = jobs[qi++];
        if (!document.body.contains(job.el)) return; /* 页面已翻走：停止 */
        if (job.ch === '｜') { setTimeout(step, PAUSE_MS); return; }   /* 停顿，不落字 */
        job.frag.el.textContent += job.ch;
        setTimeout(step, (job.para && qi > 1) ? PARA_MS : TYPE_MS);
      } catch (e) {
        setTimeout(step, 40);                        /* 单步异常不中断整条任务 */
      }
    })();
  }

  /* 一次性填满某段（跳过 / 兜底） */
  function fillFrags(el, frags, raw) {
    if (frags && frags.length) { tmFill(frags); return; }
    el.textContent = plain(raw || '');
  }

  /* ---------- 翻页 ---------- */
  function startLeaf(dir, frontHTML, backHTML, dur, done) {
    S.busy = true;
    setSlot(lfFront, frontHTML);
    setSlot(lfBack, backHTML);
    leafEl.hidden = false;
    leafEl.style.transition = 'none';
    leafEl.style.transform = dir > 0 ? 'rotateY(0deg)' : 'rotateY(-180deg)';
    void leafEl.offsetWidth;                       /* 强制一次布局，让起点落地 */
    leafEl.style.transition = 'transform ' + dur + 'ms cubic-bezier(.42, 0, .28, 1)';
    leafEl.style.transform = dir > 0 ? 'rotateY(-180deg)' : 'rotateY(0deg)';

    /* 收尾只认定时器（无头环境 transitionend 不可靠） */
    clearTimeout(leafTimer);
    leafTimer = setTimeout(function () {
      leafEl.hidden = true;
      leafEl.style.transition = 'none';
      leafEl.style.transform = 'rotateY(0deg)';
      S.busy = false;
      if (done) done();
    }, dur + 40);
  }

  function flipTo(np, dur) {
    if (!S.open || S.busy) return;
    if (np < 0 || np > MAXPAGE || np === S.page) return;

    /* 新手引导锁定：读完第 2 页（c1「测序与质量」）之前，只能停在
       第 2 页（page ≤ 5），不能往后翻——引导接案由「读完第 2 页」触发 */
    if (!isArchived('c1') && np > 5) {
      if (window.GDGate) {
        GDGate.play({
          force: true,
          lines: [
            '别急着往后翻，先把第 2 页读完。',
            '测序读段和 Q 值的门道都在这页里，读透了，办案才会更顺利。'
          ],
          kicker: '翻页提醒 · 陈探长',
          endLabel: '好，我继续读'
        });
      } else if (window.GD && GD.bubble) {
        GD.bubble('先把第 2 页读完，办案才会更顺利。');
      } else {
        toast('先把第 2 页读完，办案才会更顺利。');
      }
      return;
    }

    dur = REDUCE ? 0 : (dur || 760);

    if (MOBILE()) {
      var curH = pageHTML(S.page), nxtH = pageHTML(np);
      var d0 = np > S.page ? 1 : -1;
      setSlot(rightEl, nxtH);
      startLeaf(d0, d0 > 0 ? curH : nxtH, d0 > 0 ? nxtH : curH, dur, function () {
        S.page = np;
        typeIn(rightEl);
      });
      return;
    }

    /* 桌面：落点对齐到左页（偶数页） */
    if (np % 2) np -= 1;
    if (np === S.page) return;
    var d = np > S.page ? 1 : -1;
    var curL = pageHTML(S.page), curR = pageHTML(S.page + 1);
    var nxtL = pageHTML(np), nxtR = pageHTML(np + 1);
    /* 被翻动的那一侧先露出后面的页，纸片压在上面 */
    if (d > 0) setSlot(rightEl, nxtR); else setSlot(leftEl, nxtL);
    startLeaf(d, d > 0 ? curR : nxtR, d > 0 ? nxtL : curL, dur, function () {
      setSlot(leftEl, nxtL);
      setSlot(rightEl, nxtR);
      S.page = np;
      typeIn(leftEl);
    });
  }

  function turn(dir) {
    if (!S.open || S.busy) return;
    flipTo(S.page + dir * (MOBILE() ? 1 : 2), 720);
  }

  /* ---------- 开合 ---------- */
  var openTypeTimer = 0;

  function openBook() {
    if (!book || S.open) return;
    S.open = true;
    S.page = 0;
    render(false);       /* 先铺页面；打字等封面掀开再起，否则扉页前两行被开书动画吃掉 */
    book.classList.add('is-pages', 'is-open');
    stage.classList.add('is-open');
    if (deskEl) deskEl.classList.add('is-open');

    clearTimeout(openTypeTimer);
    openTypeTimer = setTimeout(function () {
      openTypeTimer = 0;
      if (!S.open || S.page !== 0) return;   /* 期间翻走/合上就不补打 */
      typeIn(MOBILE() ? rightEl : leftEl);
    }, REDUCE ? 30 : 1000);

    clearTimeout(coverTimer);
    coverTimer = setTimeout(function () {
      book.classList.add('is-lit', 'is-covered');
    }, REDUCE ? 30 : 960);
  }

  function closeBook() {
    if (!book || !S.open) return;
    S.open = false;
    /* 收摊：把可能残留的拖拽 / 翻页收干净，免得合上后书变成死物 */
    drag = null;
    clearTimeout(dragGuard);
    clearTimeout(leafTimer);
    clearTimeout(openTypeTimer);
    openTypeTimer = 0;
    book.classList.remove('is-drag');
    leafEl.hidden = true;
    leafEl.style.transition = 'none';
    leafEl.style.transform = 'rotateY(0deg)';
    S.busy = false;
    /* 先把封面放回来（此刻还在 -180°，背面正好是扉页，替换不掉相）；
       纸页同步淡出，别等封面落定才「啪」地消失 */
    book.classList.add('is-closing');
    book.classList.remove('is-covered');
    void book.offsetWidth;
    book.classList.remove('is-open');
    stage.classList.remove('is-open');
    if (deskEl) deskEl.classList.remove('is-open');

    clearTimeout(closeTimer);
    closeTimer = setTimeout(function () {
      if (S.open) return;
      book.classList.remove('is-lit', 'is-pages', 'is-closing');
      S.page = 0;
    }, REDUCE ? 30 : 920);
  }

  /* ---------- 标记已读 ---------- */
  function archive(id) {
    if (!id || isArchived(id)) return;
    lsSet(archKey(id), '1');
    paintArch(document);
    paintBadge();
    /* 读完不再弹提示：按钮本身变成「✓ 已读」已经是足够的反馈 */
    /* 第一次读完第二页（c1）：陈探长出来引导去接第一案 */
    if (id === 'c1') guideFirstCase();
  }

  /* 第一次读完第二页后，引导去接第一案（每个账号只播一次，键按用户名隔离） */
  var FIRST_CASE_GUIDE_KEY = 'gd_guide_first_case_';
  /* 引导对话真正走完（用户点了选择）后置 1：这是「接案引导已触发完」的判定标记，
     案件簿导航栏入口据此决定是否放行 */
  var GUIDE_DONE_KEY = 'gd_guide_done_';
  function guideFirstCase() {
    if (!window.GDGate) return;
    var u = userNs();
    var done = false;
    try { done = lsGet(FIRST_CASE_GUIDE_KEY + u) === '1'; } catch (e) { done = false; }
    if (done) return;
    lsSet(FIRST_CASE_GUIDE_KEY + u, '1');
    GDGate.play({
      force: true,
      lines: [
        '读段、Q 值、修剪——这一页的门道，你算是摸到门了。',
        '测序仪看走眼的时候，低质量碱基就藏在读段的尾巴上，不剪掉，后面会把抄错的字母当成基因突变。',
        '正巧，测序中心刚送来第一宗案：一条读段的结尾字迹潦草，等着有人把它剪干净。',
        '带上你刚学到的修剪本事，去把第一宗案接下来吧。'
      ],
      kicker: '引导接案 · 陈探长',
      choices: [
        { label: '好，去接第一案', onClick: function () { location.href = 'cases.html#case1'; } },
        { label: '我再看会儿手册', onClick: function () { /* 留在本页继续读 */ } }
      ],
      /* 无论选哪个，对话一结束就算引导走完 */
      onFinish: function () { lsSet(GUIDE_DONE_KEY + userNs(), '1'); }
    });
  }

  /* ==========================================================
     手势：左右两侧点按 + 拖拽翻页
     点按：左页左半边 = 上一页，右页右半边 = 下一页
     拖拽：往左拖前进，往右拖后退，松手过 18% 就落页
     ========================================================== */
  var drag = null;
  var dragGuard = 0;

  function stageRect() { return (MOBILE() ? book : stage).getBoundingClientRect(); }

  function zoneAt(x) {
    var r = stageRect();
    var f = (x - r.left) / r.width;
    if (MOBILE()) {
      if (f < 0.32) return -1;
      if (f > 0.68) return 1;
      return 0;
    }
    if (f < 0.25) return -1;
    if (f > 0.75) return 1;
    return 0;
  }

  function leafAngle(dir, p) { return dir > 0 ? -180 * p : -180 + 180 * p; }

  /* 起手：把纸片摆到起点，被翻的一侧先露出后面的页 */
  function dragBegin(dir) {
    var np = S.page + (MOBILE() ? dir : dir * 2);
    if (np < 0 || np > MAXPAGE) return null;
    var snapL = leftEl.innerHTML, snapR = rightEl.innerHTML;
    var front, back;
    if (MOBILE()) {
      var curH = pageHTML(S.page), nxtH = pageHTML(np);
      front = dir > 0 ? curH : nxtH;
      back = dir > 0 ? nxtH : curH;
      setSlot(rightEl, nxtH);
    } else {
      var curL = pageHTML(S.page), curR = pageHTML(S.page + 1);
      var nxtL = pageHTML(np), nxtR = pageHTML(np + 1);
      front = dir > 0 ? curR : nxtR;
      back = dir > 0 ? nxtL : curL;
      if (dir > 0) setSlot(rightEl, nxtR); else setSlot(leftEl, nxtL);
    }
    setSlot(lfFront, front);
    setSlot(lfBack, back);
    leafEl.hidden = false;
    leafEl.style.transition = 'none';
    leafEl.style.transform = 'rotateY(' + leafAngle(dir, 0) + 'deg)';
    S.busy = true;
    /* 兜底：万一 pointerup 彻底丢了，别让书卡死在半页上 */
    clearTimeout(dragGuard);
    dragGuard = setTimeout(function () {
      if (!drag || !drag.s) return;
      var d = drag; drag = null;
      book.classList.remove('is-drag');
      dragEnd(d.s, false);
    }, 9000);
    return { dir: dir, np: np, snapL: snapL, snapR: snapR };
  }

  /* 松手：过阈值就落页，否则退回原样 */
  function dragEnd(s, commit) {
    var dur = commit ? 260 : 220;
    leafEl.style.transition = 'transform ' + dur + 'ms cubic-bezier(.3,0,.3,1)';
    leafEl.style.transform = 'rotateY(' + leafAngle(s.dir, commit ? 1 : 0) + 'deg)';
    clearTimeout(leafTimer);
    leafTimer = setTimeout(function () {
      leafEl.hidden = true;
      leafEl.style.transition = 'none';
      leafEl.style.transform = 'rotateY(0deg)';
      S.busy = false;
      if (commit) {
        S.page = s.np;
        if (MOBILE()) setSlot(rightEl, pageHTML(S.page));
        else { setSlot(leftEl, pageHTML(S.page)); setSlot(rightEl, pageHTML(S.page + 1)); }
        typeIn(MOBILE() ? rightEl : leftEl);
      } else {
        leftEl.innerHTML = s.snapL;
        rightEl.innerHTML = s.snapR;
        fill(leftEl); fill(rightEl);
      }
    }, dur + 30);
  }

  function onMove(e) {
    if (!drag) return;
    /* 鼠标键早松了却没收到 pointerup（指针下的 DOM 被换掉时会这样）——就地收尾 */
    if (e.pointerType === 'mouse' && e.buttons === 0) { onUp(e); return; }
    var dx = e.clientX - drag.x0, dy = e.clientY - drag.y0;
    if (!drag.s) {
      if (Math.abs(dx) < 10) return;
      if (Math.abs(dy) > Math.abs(dx)) { drag.abort = true; return; }
      var s = dragBegin(dx < 0 ? 1 : -1);
      if (!s) { drag = null; return; }
      drag.s = s;
      book.classList.add('is-drag');
    }
    var w = stageRect().width * (MOBILE() ? 1 : 0.5);
    drag.p = Math.min(1, Math.abs(dx) / w);
    leafEl.style.transform = 'rotateY(' + leafAngle(drag.s.dir, drag.p) + 'deg)';
  }

  function onUp(e) {
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
    window.removeEventListener('pointercancel', onCancel);
    clearTimeout(dragGuard);
    if (!drag) return;
    var d = drag; drag = null;
    book.classList.remove('is-drag');
    if (!d.s) {
      if (d.abort) return;
      var z = zoneAt(e.clientX);
      if (z) turn(z);
      return;
    }
    dragEnd(d.s, d.p > 0.18);
  }

  /* 手势被打断（来电、切后台、系统抢走指针）：一律退回原样，不落页 */
  function onCancel() {
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
    window.removeEventListener('pointercancel', onCancel);
    clearTimeout(dragGuard);
    if (!drag) return;
    var d = drag; drag = null;
    book.classList.remove('is-drag');
    if (d.s) dragEnd(d.s, false);
  }

  function bindDrag() {
    book.addEventListener('pointerdown', function (e) {
      if (!S.open || S.busy) return;
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      var t = e.target;
      if (t.closest && t.closest('button, a, input, .act, .toc-item')) return;
      drag = { x0: e.clientX, y0: e.clientY, s: null, p: 0, abort: false };
      window.addEventListener('pointermove', onMove, { passive: true });
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onCancel);
    });
  }

  /* ==========================================================
     绑定
     ========================================================== */
  function boot() {
    stage = document.getElementById('bk-stage');
    book = document.getElementById('book');
    if (!stage || !book) return;              /* 不是科普页，直接退出 */

    leftEl = document.getElementById('bk-left');
    rightEl = document.getElementById('bk-right');
    leafEl = document.getElementById('bk-leaf');
    lfFront = document.getElementById('lf-front');
    lfBack = document.getElementById('lf-back');
    coverBack = document.getElementById('cv-back');
    deskEl = document.querySelector('.bk-desk');
    tbToc = document.getElementById('tb-toc');
    tbClose = document.getElementById('tb-close');
    badgeEl = document.getElementById('manual-badge');

    render();
    setSlot(coverBack, flyHTML());
    paintBadge();
    loadProg();

    /* 翻开：直接点封面 */
    var cvFront = document.getElementById('cv-front');
    if (cvFront) cvFront.addEventListener('click', openBook);

    if (tbToc) tbToc.addEventListener('click', function () { flipTo(0, 560); });
    if (tbClose) tbClose.addEventListener('click', closeBook);
    bindDrag();

    /* 书页内交互（目录跳页 / 接案路引 / 返回目录 / 合上） */
    book.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('[data-back-toc]')) {
        e.preventDefault(); flipTo(1, 640); return;
      }
      if (e.target.closest && e.target.closest('[data-close-book]')) {
        e.preventDefault(); closeBook(); return;
      }

      var g = e.target.closest ? e.target.closest('[data-goto]') : null;
      if (g) {
        e.preventDefault();
        flipTo(parseInt(g.getAttribute('data-goto'), 10) * 2, 640);
        return;
      }

      var t = e.target.closest ? e.target.closest('[data-try]') : null;
      if (t) {
        var id = t.getAttribute('data-try');
        var page = PAGES[id];
        var caseN = page && page.caseNo ? page.caseNo : 0;

        /* ① 这一页还没读完：陈探长拦下，留在本页读完，不跳转 */
        if (!isArchived(id)) {
          e.preventDefault();
          if (window.GDGate) {
            GDGate.play({
              force: true,
              lines: [
                '别急着去接案，先把这一页读完。',
                '判定规则都在这页里，读透了，办案才会更顺利。'
              ],
              kicker: '接案提醒 · 陈探长',
              endLabel: '好，我继续读'
            });
          } else if (window.GD && GD.bubble) {
            GD.bubble('先把这页读完，办案会更顺利！');
          } else {
            toast('先把这页读完，办案会更顺利！');
          }
          return;
        }

        /* ② 这一页读完了，但对应的案件还没解锁（前面还有案件没办结）：
              陈探长拦下，指向该先办的那一宗，不跳转 */
        if (caseN && !caseUnlocked(caseN)) {
          e.preventDefault();
          var fn = firstOpenCase();
          fn = Math.min(6, Math.max(1, fn));
          if (window.GDGate) {
            GDGate.play({
              force: true,
              lines: [
                '这宗还封着呢，案子得一宗一宗来。',
                '先把第 ' + fn + ' 案办结，这宗的封条才会松开。'
              ],
              kicker: '接案提醒 · 陈探长',
              choices: [
                { label: '好，去办第 ' + fn + ' 案', onClick: function () { location.href = 'cases.html#case' + fn; } },
                { label: '我再想想', onClick: function () { /* 留在本页 */ } }
              ]
            });
          } else if (window.GD && GD.bubble) {
            GD.bubble('先把第 ' + fn + ' 案办结，再回来接这宗。');
          } else {
            toast('先把第 ' + fn + ' 案办结，再回来接这宗。');
          }
          return;
        }
      }
    });

    /* 键盘 */
    document.addEventListener('keydown', function (e) {
      if (!S.open) return;
      if (e.key === 'Escape') { closeBook(); return; }
      if (e.key === 'ArrowRight') { e.preventDefault(); turn(1); return; }
      if (e.key === 'ArrowLeft') { e.preventDefault(); turn(-1); }
    });

    /* 视口跨过断点：重排成单页 / 双页 */
    var mq = null;
    try { mq = window.matchMedia('(max-width: 900px)'); } catch (err) { mq = null; }
    function onMQ() {
      if (S.open && !MOBILE() && (S.page % 2)) S.page -= 1;
      render();
    }
    if (mq) {
      if (mq.addEventListener) mq.addEventListener('change', onMQ);
      else if (mq.addListener) mq.addListener(onMQ);
    }

    /* 外链带锚点：science.html#c2 → 翻开并翻到那一页 */
    function fromHash() {
      var h = (location.hash || '').replace('#', '');
      var i = ORDER.indexOf(h);
      if (i < 0) return;
      if (!S.open) openBook();
      setTimeout(function () { flipTo((i + 1) * 2, 340); }, 1040);
    }
    fromHash();
    window.addEventListener('hashchange', fromHash);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  /* 对外只读接口 */
  window.GDManual = {
    isArchived: isArchived,
    countArchived: countArchived,
    open: function () { openBook(); },
    close: function () { closeBook(); },
    goto: function (i) { flipTo(i * 2, 500); },
    /* 补播接案引导：老账号已读完第 2 页但引导没走完时，导航守卫调它兜底 */
    playFirstCaseGuide: guideFirstCase,
    state: function () { return { page: S.page, open: S.open, busy: S.busy, leaf: !leafEl.hidden }; }
  };
})(window, document);
