# -*- coding: utf-8 -*-
"""手册 v2 补丁：九页直述文案 + 结构化要点（专有名词着色/定义高亮）+ 正文打字机。"""
import io, re

p = r"D:/医学人工智能导论大作业/design/manual.js"
s = io.open(p, encoding="utf-8").read()

NEW_PAGES = r'''  var PAGES = {
    c0: {
      no: 1, name: '什么是基因', hook: 'DNA、基因、染色体、蛋白',
      chip: '必读', kind: 'must', time: '约 2 分钟',
      open: '本页先明确四个基础概念。｜后面的所有内容都以它们为基础。',
      body: ['人体由细胞组成，细胞核内储存遗传物质 DNA。｜DNA 由 A、T、C、G 四种碱基组成，总长约 30 亿对。｜DNA 上具有功能的一段序列称为基因（人类约 2 万个），｜基因指导合成蛋白，由蛋白执行各项生理功能。'],
      points: [
        { t: '染色体', d: '46 条（23 对），DNA 的包装形式' },
        { t: '基因', d: '有功能的 DNA 片段，人类约 2 万个' },
        { t: '蛋白', d: '基因的产物，执行各项生理功能' }
      ],
      tail: '下一页：测序与质量。', caseNo: 0
    },
    c1: {
      no: 2, name: '测序与质量', hook: '读段与 Q 值',
      chip: '必读', kind: 'must', time: '约 3 分钟',
      open: '本页解释测序数据的结构。｜案件一将练习本页的修剪操作。',
      body: ['测序仪一次读不完整个基因组，｜而是把 DNA 打断为大量短片段分别测定，｜每个片段称为一条读段（read）。｜读段中每个碱基都附带质量分值（Q 值），｜表示该碱基的可靠程度。'],
      points: [
        { t: '读段（read）', d: '测序仪逐段测定产生的短片段' },
        { t: 'Q 值', d: '每个碱基的可靠度评分：Q ≥ 28 可靠，Q < 20 不可靠' },
        { t: '修剪', d: '剪除集中在读段末端的低质量碱基，避免误判变异' }
      ],
      tail: '案件一练习读段修剪。', caseNo: 1
    },
    c2: {
      no: 3, name: '序列比对', hook: '错配 SNV 与缺失 Indel',
      chip: '必读', kind: 'must', time: '约 3 分钟',
      open: '本页说明比对的原理。｜案件二将练习缺失序列的定位。',
      body: ['比对是把患者序列与人类参考基因组逐位对齐的过程。｜同一位置碱基不同，称为错配（SNV）；｜缺失或插入碱基，称为 Indel。｜Indel 会使下游碱基整体错位，｜需在缺口处补占位符 gap 后重新对齐。'],
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
      body: ['健康人之间也存在数百万处序列差异，多数无害。｜判断一个变异是否致病，依据三类证据：｜人群频率（有多罕见）、蛋白功能预测（多有害）、文献报道（是否被反复记录）。'],
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
      body: ['翻译以 3 个碱基为一组进行，每组称为一个密码子，｜对应 1 个氨基酸。｜翻译从起始密码子 ATG 开始，｜到终止密码子（TAA / TAG / TGA）结束。'],
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
      body: ['系谱图记录家族各代成员的患病情况。｜判断遗传方式依次确认三点：｜是否逐代连续传递、男女是否均患病、是否存在父传子。'],
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
      body: ['医学 AI 的应用不止变异解读：｜眼底照片与肺结节的影像判读、｜蛋白三维结构预测（AlphaFold）、｜药物分子初筛，均已投入实际使用。'],
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
      body: ['无创产前筛查（NIPT）通过孕妇外周血检测胎儿染色体异常；｜肿瘤患者先做基因检测、再选择靶向药；｜测序也用于罕见病的病因定位。'],
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
      body: ['基因分析共五步：｜测序产生读段，｜质控剪除低质量碱基，｜比对定位差异，｜识别变异，｜最后结合证据完成致病性解读。'],
      points: [
        { t: '五步流程', d: '测序 → 质控 → 比对 → 变异识别 → 解读' },
        { t: '案件对应', d: '案件一、二、三分别实操其中三步' },
        { t: '医生签发', d: 'AI 负责提速，诊断结论由医生综合判断' }
      ],
      tail: '', caseNo: 0
    }
  };'''

m = re.search(r'  var PAGES = \{.*?\n  \};', s, flags=re.S)
assert m, "PAGES 块未找到"
s = s[:m.start()] + NEW_PAGES + s[m.end():]

# ---------- ② ptsHTML：专有名词着色 + 定义短语高亮 ----------
old_pts = """  function ptsHTML(id) {
    var p = PAGES[id], NUM = ['一', '二', '三'];
    return p.points.map(function (t, i) {
      var inner = p.marks.indexOf(i) > -1 ? '<mark>' + esc(t) + '</mark>' : esc(t);
      return '<li><b>' + (NUM[i] || '·') + '</b>' + inner + '</li>';
    }).join('');
  }"""
new_pts = """  function ptsHTML(id) {
    var p = PAGES[id], NUM = ['一', '二', '三'];
    return p.points.map(function (o, i) {
      /* 专有名词着色（.pg-term）+ 定义/功能短语高亮（mark.pg-def） */
      return '<li><b>' + (NUM[i] || '·') + '</b>' +
        '<em class="pg-term">' + esc(o.t) + '</em>' +
        '<mark class="pg-def">' + esc(o.d) + '</mark></li>';
    }).join('');
  }"""
if old_pts in s:
    s = s.replace(old_pts, new_pts)
else:
    print("ptsHTML 已是新版本，跳过")

# ---------- ③ leftHTML：正文带 data-ty 交给打字机，页眉去掉 chip ----------
old_left = """  function leftHTML(id) {
    var p = PAGES[id];
    var body = p.body.map(function (t) {
      return '<p class="pg-text">' + esc(plain(t)) + '</p>';
    }).join('');
    return '<div class="pg">' +
      runHTML('第 ' + p.no + ' 页', p.time) +
      '<h3 class="pg-title">' + esc(p.name) + '</h3>' +
      '<p class="pg-hook">' + esc(p.hook) + '</p>' +
      '<blockquote class="pg-say"><p data-ty="' + attr(plain(p.open)) + '"></p></blockquote>' +
      body +
      '<ol class="pg-points">' + ptsHTML(id) + '</ol>' +
      '<div class="pg-foot"><span>侦探须知</span><span>' + (p.no * 2) + '</span></div>' +
      '</div>';
  }"""
new_left = """  function leftHTML(id) {
    var p = PAGES[id];
    /* 正文段落带 data-ty（含「｜」停顿符），由打字机逐字打出 */
    var body = p.body.map(function (t) {
      return '<p class="pg-text" data-ty="' + attr(t) + '"></p>';
    }).join('');
    return '<div class="pg">' +
      runHTML('第 ' + p.no + ' 页', p.time) +
      '<h3 class="pg-title">' + esc(p.name) + '</h3>' +
      '<p class="pg-hook">' + esc(p.hook) + '</p>' +
      '<blockquote class="pg-say"><p data-ty="' + attr(p.open) + '"></p></blockquote>' +
      body +
      '<ol class="pg-points">' + ptsHTML(id) + '</ol>' +
      '<div class="pg-foot"><span>侦探须知</span><span>' + (p.no * 2) + '</span></div>' +
      '</div>';
  }"""
if old_left in s:
    s = s.replace(old_left, new_left)
else:
    print("leftHTML 已是新版本，跳过")

# ---------- ④ typeIn 重写：顺序打出开场白+正文，放慢，「｜」停顿，翻页即停 ----------
m2 = re.search(r'  /\* ---------- 逐字打出探长那句话 ---------- \*/\n  function typeIn\(root\) \{.*?\n  \}\n', s, flags=re.S)
assert m2, "typeIn 锚点未找到"
NEW_TYPEIN = """  /* ---------- 打字机：开场白 + 正文按 DOM 顺序逐字打出（放慢；「｜」为停顿） ---------- */
  var TYPE_MS = 38;        /* 每字间隔 */
  var PAUSE_MS = 430;      /* 「｜」处的停顿 */
  var typeToken = 0;

  function typeIn(root) {
    if (!root) return;
    var my = ++typeToken;                          /* 翻页/重渲后旧任务自动失效 */
    var els = root.querySelectorAll('[data-ty]');
    if (!els.length) return;

    var jobs = [];
    Array.prototype.forEach.call(els, function (el) {
      var raw = el.getAttribute('data-ty') || '';
      if (REDUCE) { el.textContent = raw.replace(/｜/g, ''); return; }
      el.textContent = '';
      Array.prototype.forEach.call(raw, function () { jobs.push(el); });
    });
    if (REDUCE) return;

    var ei = 0, ci = 0;
    (function step() {
      if (my !== typeToken) return;                /* 已有新任务：本轮作废 */
      if (ei >= jobs.length) return;
      var el = jobs[ei], raw = el.getAttribute('data-ty') || '';
      if (!document.body.contains(el)) return;     /* 页面已翻走：停止 */
      if (ci >= raw.length) { ei++; ci = 0; setTimeout(step, 170); return; }
      var ch = raw.charAt(ci++);
      if (ch === '｜') { setTimeout(step, PAUSE_MS); return; }   /* 停顿，不落字 */
      el.textContent += ch;
      setTimeout(step, TYPE_MS);
    })();
  }
"""
s = s[:m2.start()] + NEW_TYPEIN + s[m2.end():]

# ---------- ⑤ 残留的七页/批注文案 ----------
s = s.replace("runHTML('目录', '共七页')", "runHTML('目录', '共九页')")
lines = s.split("\n")
for i, l in enumerate(lines):
    if "fly-gift" in l and "p class" in l:
        lines[i] = "      '<p class=\"fly-gift\">使用建议：<br>先浏览本手册，再进入案件簿。<br>各案件的判定规则都出自本手册。</p>' +"
s = "\n".join(lines)

io.open(p, "w", encoding="utf-8").write(s)
left = sum(s.count(w) for w in ["撕", "抄书", "地基", "审人", "定罪", "电报", "暗号", "看走眼", "出厂设置"])
print("manual.js v2 完成；七页残留:", s.count("七页"), "；比喻残留:", left)
