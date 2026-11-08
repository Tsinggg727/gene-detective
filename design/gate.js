/* ==========================================================
   基因侦探 · 陈探长对话层（全站共用）
   ----------------------------------------------------------
   用法：
     GDGate.play({
       lines: ['…', '…'],
       key: 'gd_brief_seen',       // 只播一次（localStorage）；省略则每次都播
       kicker: 'CASE BRIEF · 开场交代',
       endLabel: '翻开第一份卷宗',
       choices: [                  // 可选：首句放完后出现分支按钮，点击即关层并回调
         { label: '我是新来的', onClick: fn },
         { label: '已有编号，去登录', onClick: fn }
       ],
       onFinish: function (skipped) { … }
     });
   特性：逐字打出（标点停顿）、点击/回车/空格推进、Esc 或「跳过」直接进、
        打字中点一次 = 这句立即说完；内容不做透明隐藏，动效失效也能看全。
   ========================================================== */
(function (window, document) {
  'use strict';

  var AVATAR = 'assets/ip-chen-avatar.jpg';
  var ARROW = '<svg class="ic" viewBox="0 0 24 24"><path d="M4 12h15"/><path d="M13.4 6l6 6-6 6"/></svg>';
  var cur = null;

  function html(s) { return s == null ? '' : String(s); }

  function build() {
    var el = document.createElement('div');
    el.className = 'gd-gate';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-label', '陈探长的交代');
    el.innerHTML =
      '<div class="gd-scrim" data-gd="scrim"></div>' +
      '<div class="gd-card">' +
        '<div class="gd-side">' +
          '<span class="gd-portrait"><img src="' + AVATAR + '" alt="陈探长"></span>' +
          '<span class="gd-name">陈探长</span>' +
          '<span class="gd-role">精准医学侦探社<br>负责人</span>' +
        '</div>' +
        '<div class="gd-main">' +
          '<div class="gd-top">' +
            '<span class="gd-kicker" data-gd="kicker"></span>' +
          '</div>' +
          '<p class="gd-line"><span class="gd-text" data-gd="text"></span>' +
            '<span class="gd-caret" data-gd="caret"></span></p>' +
          '<div class="gd-foot">' +
            '<span class="gd-dots" data-gd="dots" aria-hidden="true"></span>' +
            '<span class="gd-hint" data-gd="hint" aria-hidden="true">点击下一句' + ARROW + '</span>' +
            '<button class="btn btn-primary gd-next" type="button" data-gd="next" hidden>继续 ' + ARROW + '</button>' +
            '<div class="gd-choices" data-gd="choices" hidden></div>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(el);
    return el;
  }

  function play(opts) {
    opts = opts || {};
    var lines = (opts.lines || []).filter(Boolean);
    if (!lines.length) { if (opts.onFinish) opts.onFinish(true); return; }

    var key = opts.key || '';
    if (key) {
      var seen = false;
      try { seen = localStorage.getItem(key) === '1'; } catch (e) { /* 隐私模式 */ }
      if (seen) { document.documentElement.classList.remove('gd-locked');
        if (opts.onFinish) opts.onFinish(true); return; }
    }
    /* 拦截类提示（force）优先级最高：开场白若还占着层，先把它关掉，
       否则 locked / 未读手册等关键拦截会被静默丢弃，用户直接跳转 */
    if (cur) {
      if (!opts.force) return;
      cur.close(true);
      cur = null;
    }

    var el = build();
    var q = function (name) { return el.querySelector('[data-gd="' + name + '"]'); };
    var textEl = q('text'), caret = q('caret'), dotsEl = q('dots'),
        nextBtn = q('next'), scrimEl = q('scrim'), hintEl = q('hint'),
        choicesEl = q('choices');
    var kick = q('kicker');
    if (opts.kicker) kick.textContent = opts.kicker;
    else kick.style.display = 'none';

    /* 首句分支：opts.choices = [{ label, onClick }]，
       第一句播放完后把「继续/提示」换成这些选项按钮 */
    var choices = Array.isArray(opts.choices) && opts.choices.length ? opts.choices : null;
    if (choices) {
      choicesEl.innerHTML = choices.map(function (c, i) {
        var ghost = i > 0 ? ' ghost' : '';
        return '<button class="btn gd-choice' + ghost + '" type="button" data-gd="choice" data-i="' + i + '">' +
          html(c.label) + '</button>';
      }).join('');
      choicesEl.querySelectorAll('[data-gd="choice"]').forEach(function (b) {
        b.addEventListener('click', function (e) {
          e.stopPropagation();
          var c = choices[Number(b.getAttribute('data-i'))];
          close(false);
          if (c && c.onClick) c.onClick();
        });
      });
    }

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var li = 0, typing = false, timer = null, queue = [], qi = 0, alive = true;

    function paintDots() {
      var out = '';
      for (var i = 0; i < lines.length; i++) {
        out += '<i class="' + (i < li ? 'done' : (i === li ? 'on' : '')) + '"></i>';
      }
      dotsEl.innerHTML = out;
    }
    function updateNext() {
      var last = li >= lines.length - 1;
      /* 分支选项：有 choices 时，最后一句放完就展示选项按钮（替代「继续」） */
      var showChoices = choices && last;
      if (choicesEl) choicesEl.hidden = !showChoices;
      if (showChoices) {
        nextBtn.hidden = true;
        hintEl.hidden = true;
        return;
      }
      /* 中间句：右下角只留小字批注；最后一句才出现动作按钮 */
      nextBtn.hidden = !last;
      if (last) nextBtn.innerHTML = html(opts.endLabel || '继续') + ARROW;
      hintEl.hidden = last;
    }
    function finishLine() {
      clearTimeout(timer); typing = false;
      textEl.textContent = String(lines[li]);
      caret.classList.remove('on');
      updateNext();
      /* 只有最后一句有实体按钮可聚焦；中间句的提示是纯文字 */
      if (li >= lines.length - 1) {
        try { nextBtn.focus({ preventScroll: true }); } catch (e) { /* ignore */ }
      }
    }
    function step() {
      if (!typing || !alive) return;
      if (qi >= queue.length) { finishLine(); return; }
      var ch = queue[qi++];
      textEl.textContent += ch;
      var d = 34;
      if ('，、；：'.indexOf(ch) > -1) d = 180;
      else if ('。？！—…'.indexOf(ch) > -1) d = 250;
      else if ('「」『』（）'.indexOf(ch) > -1) d = 90;
      timer = setTimeout(step, d);
    }
    function startLine() {
      if (!alive) return;
      paintDots();
      queue = Array.from(String(lines[li]));
      qi = 0;
      textEl.textContent = '';
      updateNext();
      if (reduce) { finishLine(); return; }
      typing = true;
      caret.classList.add('on');
      timer = setTimeout(step, 150);
    }
    function advance() {
      if (!alive) return;
      if (typing) { finishLine(); return; }
      /* 分支选项：最后一句放完必须点选项按钮做选择，点击卡片/回车不往下翻 */
      if (choices && li >= lines.length - 1) return;
      if (li < lines.length - 1) { li++; startLine(); } else close(false);
    }

    function close(skipped) {
      if (!alive) return;
      alive = false;
      cur = null;
      clearTimeout(timer); typing = false;
      if (key) { try { localStorage.setItem(key, '1'); } catch (e) { /* ignore */ } }
      el.classList.add('closing');
      document.documentElement.classList.remove('gd-locked');
      document.removeEventListener('keydown', onKey);
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 460);
      if (opts.onFinish) opts.onFinish(!!skipped);
    }

    function onKey(e) {
      if (!alive) return;
      /* 不保留任何「直达结尾」的捷径：Esc 也不跳，只能一句句点下去 */
      if (e.key === 'Enter' || e.key === ' ') {
        if (e.target && e.target.closest && e.target.closest('button')) return;
        e.preventDefault(); advance();
      }
    }

    nextBtn.addEventListener('click', function (e) { e.stopPropagation(); advance(); });
    scrimEl.addEventListener('click', advance);
    el.querySelector('.gd-card').addEventListener('click', function (e) {
      if (e.target.closest('button') || e.target.closest('a')) return;
      advance();
    });
    document.addEventListener('keydown', onKey);

    document.documentElement.classList.add('gd-locked');
    /* 不用 requestAnimationFrame：部分环境（无头浏览器、内嵌 webview）
       不产生帧，rAF 不回调，台词会永远停在空白。定时器更稳。 */
    setTimeout(startLine, 90);
    cur = { el: el, close: close };
  }

  window.GDGate = {
    play: play,
    close: function () { if (cur) cur.close(true); },
    seen: function (key) {
      try { return localStorage.getItem(key) === '1'; } catch (e) { return false; }
    },
    forget: function (key) {
      try { localStorage.removeItem(key); } catch (e) { /* ignore */ }
    }
  };
})(window, document);
