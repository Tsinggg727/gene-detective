/* ==========================================================
   基因侦探 · 文本标注（短语荧光 + 名词加粗）
   ----------------------------------------------------------
   不做「词表自动全标」——那样一段里同一个词会被反复刷色，
   读到后面反而看不出重点。改成在文案里按句子手工标，一段只标一次。

   三种语法（写在文案里）：
     **短语**     荧光笔   —— 信息量大的词组 / 动作短语，如「大量短片段」
     __名词__     加粗     —— 专业名词，只强调字面，如「碱基」
     ***重点***   两者一起 —— 全篇最要紧的那一两处

   两套输出：
     html(text)          静态文本直接给 innerHTML
     build/fill          给打字机：把段落切成有序片段，逐字写进对应片段，
                         高亮随打字一起长出来，不用打完再回填。
   文本转义在这里一次做掉，调用方不要再 esc。
   ========================================================== */
(function (window) {
  'use strict';

  /* 顺序要紧：*** 必须排在 ** 前面，否则「***重点***」会被当成「**」+「*」 */
  var RE_MARK = /\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|__([^_]+)__/g;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function parse(text) {
    var src = String(text == null ? '' : text);
    var out = [], last = 0, m;
    RE_MARK.lastIndex = 0;
    while ((m = RE_MARK.exec(src))) {
      if (m.index > last) out.push({ k: '', s: src.slice(last, m.index) });
      if (m[1] != null) out.push({ k: 'duo', s: m[1] });
      else if (m[2] != null) out.push({ k: 'hl', s: m[2] });
      else out.push({ k: 'tm', s: m[3] });
      last = RE_MARK.lastIndex;
    }
    if (last < src.length) out.push({ k: '', s: src.slice(last) });
    return out;
  }

  /* ---------- 静态文本 ---------- */
  function html(text) {
    return parse(text).map(function (c) {
      var s = escapeHtml(c.s);
      if (c.k === 'hl') return '<mark class="tx-hl">' + s + '</mark>';
      if (c.k === 'duo') return '<mark class="tx-hl tx-duo">' + s + '</mark>';
      if (c.k === 'tm') return '<span class="tx-tm">' + s + '</span>';
      return s;
    }).join('');
  }

  /* ---------- 打字机 ----------
     返回 [{ el, s }]：el 已挂到 node 上、内容为空；s 是这一段完整文字
     （含「｜」停顿符，打字时跳过不写）。 */
  function build(node, text) {
    node.innerHTML = '';
    var frags = [];
    parse(text).forEach(function (c) {
      if (!c.s) return;
      var el;
      if (c.k === 'hl' || c.k === 'duo') {
        el = document.createElement('mark');
        el.className = c.k === 'duo' ? 'tx-hl tx-duo' : 'tx-hl';
      } else if (c.k === 'tm') {
        el = document.createElement('span');
        el.className = 'tx-tm';
      } else {
        el = document.createTextNode('');
      }
      node.appendChild(el);
      frags.push({ el: el, s: c.s });
    });
    return frags;
  }

  function fill(frags) {
    (frags || []).forEach(function (f) { f.el.textContent = f.s.replace(/｜/g, ''); });
  }

  window.GDTerms = {
    parse: parse,
    html: html,
    build: build,
    fill: fill
  };
})(window);
