/* ==========================================================
   基因侦探 · 前端接入层
   1. 统一 API 请求（同源 /api；file:// 直开时回落 127.0.0.1:8000）
   2. 登录态（localStorage 保存 JWT）+ 401 自动清理
   3. 导航栏「侦探证」用户区与案件簿进度（各页零改动接入）
   ========================================================== */
(function (window, document) {
  'use strict';

  /* ---------- 基础配置 ---------- */
  var BASE = (window.GD_API_BASE ||
    (location.protocol === 'file:' ? 'http://127.0.0.1:8000/api' : '/api')
  ).replace(/\/+$/, '');

  var TOKEN_KEY = 'gd_token';
  var USER_KEY = 'gd_user';
  /* gd_avatar 头像缓存已按账号分键（avatarKey()），常量保留仅作迁移参考 */
  var LEVELS = ['level1', 'level2', 'level3', 'level4', 'level5', 'level6'];

  /* ---------- 预设头像目录（与后端 /api/auth/avatars 保持一致；不支持上传）
     tier = 解锁所需破案数，与头衔阶梯一一对应：破 N 案解锁第 N+1 级头像 ---------- */
  var AVATARS = [
    { id: 'rank-1',  label: '见习侦探', img: 'assets/avatar-1.png', tier: 0 },
    { id: 'rank-2',  label: '助理侦探', img: 'assets/avatar-2.png', tier: 1 },
    { id: 'rank-3',  label: '正式侦探', img: 'assets/avatar-3.png', tier: 2 },
    { id: 'rank-4',  label: '高级侦探', img: 'assets/avatar-4.png', tier: 3 },
    { id: 'rank-5',  label: '首席侦探', img: 'assets/avatar-5.png', tier: 4 },
    { id: 'rank-6',  label: '名侦探',   img: 'assets/avatar-6.png', tier: 5 },
    { id: 'rank-7',  label: '传奇侦探', img: 'assets/avatar-7.png', tier: 6 }
  ];
  /* 头像缓存键按账号隔离：同浏览器换号不串头像 */
  function avatarKey() {
    var u = '';
    try { u = getUser() || ''; } catch (e) { u = ''; }
    if (u && typeof u === 'object') u = u.username || '';
    return 'gd_avatar_' + (u || 'guest');
  }
  function getAvatar() {
    try {
      var id = localStorage.getItem(avatarKey()) || 'rank-1';
      return id === 'letter' ? 'rank-1' : id;
    } catch (e) { return 'rank-1'; }
  }
  function setAvatarLocal(id) {
    try { localStorage.setItem(avatarKey(), id); } catch (e) { /* ignore */ }
  }
  function avatarImg(id) {
    for (var i = 0; i < AVATARS.length; i++) {
      if (AVATARS[i].id === id) return AVATARS[i].img;
    }
    return null;
  }

  /* 头衔阶梯：破一案升一级，六案全破 → 传奇侦探 */
  var TITLES = [
    { zh: '见习侦探', en: 'Rookie' },
    { zh: '助理侦探', en: 'Assistant' },
    { zh: '正式侦探', en: 'Detective' },
    { zh: '高级侦探', en: 'Senior' },
    { zh: '首席侦探', en: 'Chief' },
    { zh: '名侦探', en: 'Master' },
    { zh: '传奇侦探', en: 'Legend' }
  ];
  function titleFor(done) {
    return TITLES[Math.max(0, Math.min(TITLES.length - 1, Number(done) || 0))];
  }

  /* ---------- 登录态存储 ---------- */
  function getToken() {
    try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }
  function getUser() {
    try { return localStorage.getItem(USER_KEY) || ''; } catch (e) { return ''; }
  }

  /* 手册页是否已读。键名规则与 manual.js 保持一致（按账号隔离）：
     gd_manual_<用户名>_<id>。跨页调用（如挑战页接案前检查）统一走这里。 */
  function isManualRead(id) {
    if (!id) return false;
    var u = getUser() || 'guest';
    try { return localStorage.getItem('gd_manual_' + u + '_' + id) === '1'; }
    catch (e) { return false; }
  }

  /* 接案引导对话是否已触发完（读完第 2 页 → 陈探长引导对话走完）。
     manual.js 的 guideFirstCase 在对话结束（onFinish）时写入 gd_guide_done。 */
  function isGuideDone() {
    var u = '';
    try { u = getUser() || ''; } catch (e) { u = ''; }
    if (u && typeof u === 'object') u = u.username || '';
    try { return localStorage.getItem('gd_guide_done_' + (u || 'guest')) === '1'; }
    catch (e) { return false; }
  }
  function setAuth(token, username) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, username);
    } catch (e) { /* 隐私模式忽略 */ }
  }
  function clearAuth() {
    try {
      var ak = avatarKey();                  /* 先算键再清用户名 */
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      localStorage.removeItem(ak);
    } catch (e) { /* ignore */ }
  }

  /* ---------- 请求封装 ---------- */
  function normalizeError(res, data) {
    var msg = '请求失败（' + res.status + '）';
    if (data && data.detail) {
      if (typeof data.detail === 'string') msg = data.detail;
      else if (Array.isArray(data.detail)) {
        msg = data.detail.map(function (d) { return d.msg || ''; }).filter(Boolean).join('；') || msg;
      }
    }
    var err = new Error(msg);
    err.status = res.status;
    err.data = data;
    return err;
  }

  function request(path, opt) {
    opt = opt || {};
    var headers = { Accept: 'application/json' };
    if (opt.body !== undefined) headers['Content-Type'] = 'application/json';
    var token = getToken();
    if (opt.auth !== false && token) headers.Authorization = 'Bearer ' + token;

    return fetch(BASE + path, {
      method: opt.method || 'GET',
      headers: headers,
      body: opt.body === undefined ? undefined : JSON.stringify(opt.body),
      cache: 'no-store'
    }).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
        if (res.ok) return data;
        if (res.status === 401 && opt.auth !== false) clearAuth();
        throw normalizeError(res, data);
      });
    }, function (e) {
      var err = new Error('连接不上后端服务，请确认已启动（默认 127.0.0.1:8000）');
      err.offline = true;
      throw err;
    });
  }

  /* ---------- 认证 ---------- */
  function handleAuthResult(data) {
    setAuth(data.access_token, data.username);
    emit('gd:auth', { username: data.username });
    return data;
  }
  function login(username, password) {
    return request('/auth/login', { method: 'POST', auth: false, body: { username: username, password: password } })
      .then(handleAuthResult);
  }
  function register(username, password) {
    return request('/auth/register', { method: 'POST', auth: false, body: { username: username, password: password } })
      .then(handleAuthResult);
  }
  function logout() {
    clearAuth();
    emit('gd:auth', { username: '' });
  }

  /* ---------- 陈探长气泡提示（轻量对话，复用开场白 .gd-card 的视觉格式） ---------- */
  var bubbleEl = null, bubbleTimer = null;
  function bubble(text) {
    if (!bubbleEl) {
      bubbleEl = document.createElement('div');
      bubbleEl.className = 'gd-bubble';
      bubbleEl.setAttribute('role', 'status');
      bubbleEl.innerHTML =
        '<div class="gd-card">' +
          '<div class="gd-side">' +
            '<span class="gd-portrait"><img src="assets/ip-chen-avatar.jpg" alt="陈探长"></span>' +
            '<span class="gd-name">陈探长</span>' +
          '</div>' +
          '<div class="gd-main">' +
            '<p class="gd-line"><span class="gd-text"></span></p>' +
          '</div>' +
        '</div>';
      document.body.appendChild(bubbleEl);
    }
    bubbleEl.querySelector('.gd-text').textContent = text;
    /* 重新触发进入动画：先摘 show 再下一次帧加回，保证连续提示也能重放 */
    bubbleEl.classList.remove('show');
    void bubbleEl.offsetWidth;
    bubbleEl.classList.add('show');
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(function () { bubbleEl.classList.remove('show'); }, 3200);
  }

  /* 校验本地 token 是否仍有效；无效则清理并返回 null */
  function me() {
    if (!getToken()) return Promise.resolve(null);
    return request('/auth/me').then(function (d) {
      if (d && d.username) {
        try {
          localStorage.setItem(USER_KEY, d.username);
          localStorage.setItem(avatarKey(), d.avatar || 'letter');
        } catch (e) { /* ignore */ }
      }
      return d;
    }).catch(function (e) {
      if (e.status === 401) { clearAuth(); return null; }
      throw e;
    });
  }

  /* ---------- 更换头像（预设 id，服务端存档） ---------- */
  function setAvatar(id) {
    return request('/auth/avatar', { method: 'POST', body: { avatar: id } })
      .then(function (d) {
        setAvatarLocal(d.avatar || id);
        renderNavUser(getUser());
        emit('gd:avatar', { avatar: d.avatar });
        return d.avatar;
      });
  }

  /* ---------- 进度 ---------- */
  function emptyProgress() {
    var r = {};
    LEVELS.forEach(function (k) { r[k] = null; });
    return r;
  }
  function normalizeProgress(d) {
    var results = (d && d.results) || {};
    var out = emptyProgress();
    LEVELS.forEach(function (k) {
      out[k] = results[k] && typeof results[k] === 'object' ? results[k] : null;
    });
    return out;
  }
  function loadProgress() {
    if (!getToken()) return Promise.resolve(emptyProgress());
    return request('/progress').then(function (d) {
      var p = normalizeProgress(d);
      emit('gd:progress', p);
      return p;
    }).catch(function (e) {
      if (e.status === 401) { emit('gd:progress', emptyProgress()); return emptyProgress(); }
      throw e;
    });
  }
  function saveProgress(results) {
    return request('/progress', { method: 'POST', body: { results: results } })
      .then(function (d) {
        var p = normalizeProgress(d);
        emit('gd:progress', p);
        return p;
      });
  }
  function resetProgress() {
    return request('/progress', { method: 'DELETE' }).then(function () {
      var p = emptyProgress();
      emit('gd:progress', p);
      // 后端会把高于见习的头像降回默认：重新同步头像缓存并刷新导航
      return me();
    }).then(function () {
      renderNavUser(getUser());
      return emptyProgress();
    });
  }
  function countDone(results) {
    if (!results) return 0;
    return LEVELS.filter(function (k) { return !!results[k]; }).length;
  }

  /* ---------- 用服务器进度回填本地「看过」标记 ----------
     开场白/收书/引导/手册已读这些标记只存 localStorage（跟随浏览器），
     而结案进度在服务器。换浏览器、无痕窗口或清过缓存的老账号，
     本地标记全丢 → 新手对话重播、案件簿导航被拦、接案被手册拦截。
     进度加载后统一回填：结过案的账号视为已完成全部新手流程。 */
  var CASE_MANUAL_MAP = { 1: 'c1', 2: 'c2', 3: 'c3', 4: 'c5', 5: 'c8', 6: 'c7' };
  function userKeyNS(base) {
    var u = getUser();
    if (u && typeof u === 'object') u = u.username || '';
    return base + (u || 'guest');
  }
  function syncOnboardingFromProgress(p) {
    var done = countDone(p);
    if (done < 1) return;
    try {
      ['gd_guide_done_', 'gd_brief_seen_', 'gd_manual_intro_v2_'].forEach(function (k) {
        var key = userKeyNS(k);
        if (localStorage.getItem(key) !== '1') localStorage.setItem(key, '1');
      });
      /* 已结案件对应的手册页也补「已读」 */
      for (var n = 1; n <= Math.min(done, 6); n++) {
        var mid = CASE_MANUAL_MAP[n];
        if (mid) localStorage.setItem(userKeyNS('gd_manual_') + '_' + mid, '1');
      }
    } catch (e) { /* 隐私模式存不进就作罢，各页面另有进度兜底 */ }
  }

  /* ---------- 评分（最终结案报告解锁后才展示） ----------
     分数 = 100 − 用时扣分（每案有基准用时，超 30s 扣 2，最多扣 40，下限 60）
     星级 = 锦囊次数（0 个 ★★★ / 1 个 ★★ / ≥2 个 ★），重演保留历史最好 */
  var CASE_BASE_SEC = { 1: 180, 2: 240, 3: 300, 4: 240, 5: 240, 6: 180 };
  function caseScore(n, elapsedSec) {
    if (!(elapsedSec > 0)) return null;
    var base = CASE_BASE_SEC[n] || 240;
    var over = Math.max(0, elapsedSec - base);
    var deduct = Math.min(40, Math.ceil(over / 30) * 2);
    return Math.max(60, 100 - deduct);
  }
  function caseStars(hints) {
    /* 兜底：hints 缺失或非法（旧存档/异常）一律按 0 锦囊满星处理，绝不给 0 星 */
    if (typeof hints !== 'number' || hints < 0) return 3;
    return hints === 0 ? 3 : (hints === 1 ? 2 : 1);
  }
  function finalUnlocked(results) { return countDone(results) === 6; }
  /* 传奇侦探：六案全破 + 平均 ≥95 分 + 所有案件满星（0 锦囊 ★★★） */
  function isLegend(results) {
    if (!finalUnlocked(results)) return false;
    var sum = 0;
    for (var i = 1; i <= 6; i++) {
      var r = results['level' + i];
      if (!r) return false;
      /* 旧存档兼容：计时功能上线前结的案没有 elapsedSec，按满分 100 计入，
         否则那批玩家永远到不了传奇（重演虽可补录，但没必要强制） */
      var s = caseScore(i, r.elapsedSec);
      sum += (s == null ? 100 : s);
      if (caseStars(r.hints) !== 3) return false;
    }
    return sum / 6 >= 95;
  }

  /* ---------- 彩蛋（案件页 / 报告页共用） ---------- */
  function eggBadgeRain() {
    var box = document.createElement('div');
    box.className = 'egg-rain';
    var glyphs = ['★', '✦', '✧'];
    var colors = ['#d9a13c', '#7e97c8', '#4f5f9e'];
    for (var i = 0; i < 16; i++) {
      var s = document.createElement('span');
      s.textContent = glyphs[i % glyphs.length];
      s.style.left = (4 + Math.random() * 92) + '%';
      s.style.color = colors[i % colors.length];
      s.style.fontSize = (10 + Math.random() * 8) + 'px';
      s.style.animationDelay = (Math.random() * 0.9) + 's';
      s.style.animationDuration = (1.7 + Math.random() * 1.1) + 's';
      box.appendChild(s);
    }
    document.body.appendChild(box);
    setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 3800);
  }
  function eggGiftNote(isLegend) {
    var note = document.createElement('div');
    note.className = 'egg-note' + (isLegend ? ' is-legend' : '');
    note.innerHTML =
      '<span class="egg-note-tape"></span>' +
      '<div class="egg-note-head"></div>' +
      '<p class="egg-note-body"></p>' +
      '<span class="egg-note-stamp">✿</span>' +
      '<span class="egg-note-sign"></span>';
    document.body.appendChild(note);
    note.querySelector('.egg-note-head').textContent =
      isLegend ? '侦探社内部便签 · 绝密' : '侦探社内部便签';
    var body = note.querySelector('.egg-note-body');
    var sign = note.querySelector('.egg-note-sign');
    /* 「致 + 玩家代号」开头；\n 是分段标记（打字时落成 <br>），
       **词** 是加粗标记（打字时落成 <b>） */
    var cached = getUser();
    var to = (typeof cached === 'string' ? cached : (cached && cached.username)) || '侦探';
    var lines = isLegend
      ? '致 ' + to + '：\n六案全破，分毫不差。这张便签，侦探社一百年也写不出几张。｜传奇这个称呼，你担得起。'
      : '致 ' + to + '：\n首案告破，恭喜。我就知道这对你来说是小菜一碟，我果然没看错人。\n你可能已经发现了那只**锦囊**——卡住时它能帮你，但每开一次，评星就要落一颗。你可能会疑惑什么是**星星**：结案时按**锦囊**的使用次数评星，用得越少，评星越高。\n对评星不满意也不要紧，案件随时**可以重演**，反复刷到满意为止——**星星**只认最好的一次。\n若你能全程不靠它、六案颗颗星都攥在手里，有份你**想不到的谢礼**等你。';
    /* 解析 **加粗** 标记：拍平成 [{ch, b}]，逐字打，加粗字落进 <b> 里 */
    var chars = [];
    Array.from(lines).forEach(function (ch) {
      if (ch === '*') { chars.push({ ch: '*', b: false }); return; }  /* 保险：不成对的星号按原文打 */
      chars.push({ ch: ch, b: false });
    });
    (function () {
      var out = [], i = 0, bold = false;
      while (i < chars.length) {
        var c = chars[i];
        if (c.ch === '*' && i + 1 < chars.length && chars[i + 1].ch === '*') {
          bold = !bold; i += 2; continue;
        }
        out.push({ ch: c.ch, b: bold }); i++;
      }
      chars = out;
    })();
    var bi = 0;
    var boldEl = null;
    (function tick() {
      if (!document.body.contains(note)) return;
      if (bi >= chars.length) return;
      var it = chars[bi++];
      if (it.ch === '｜') { setTimeout(tick, 260); return; }
      if (it.ch === '\n') {
        body.appendChild(document.createElement('br'));
        boldEl = null;                        /* 换行后重新起段，加粗态不跨段 */
        setTimeout(tick, 340);
        return;
      }
      if (it.b && !boldEl) { boldEl = document.createElement('b'); body.appendChild(boldEl); }
      if (!it.b) boldEl = null;
      (it.b ? boldEl : body).appendChild(document.createTextNode(it.ch));
      if (bi > chars.length - 6) sign.textContent = '—— 陈探长';
      setTimeout(tick, 34);
    })();
    note.addEventListener('click', function () {
      if (note.parentNode) note.parentNode.removeChild(note);
    });
  }

  /* 彩色烟花：六波升空炸开，每颗粒子随机色相；播放完自动清理 */
  function eggFireworks() {
    for (var b = 0; b < 6; b++) {
      (function (bi) {
        setTimeout(function () {
          var fw = document.createElement('div');
          fw.className = 'egg-fw';
          fw.style.left = (12 + Math.random() * 76) + '%';
          fw.style.top = (8 + Math.random() * 52) + '%';
          for (var i = 0; i < 46; i++) {
            var p = document.createElement('i');
            var ang = (Math.PI * 2 * i) / 46 + Math.random() * 0.22;
            var dist = 64 + Math.random() * 110;
            p.style.setProperty('--dx', (Math.cos(ang) * dist).toFixed(1) + 'px');
            p.style.setProperty('--dy', (Math.sin(ang) * dist).toFixed(1) + 'px');
            p.style.color = 'hsl(' + Math.round(Math.random() * 360) + ' 82% 62%)';
            p.style.animationDelay = (Math.random() * 0.2) + 's';
            fw.appendChild(p);
          }
          document.body.appendChild(fw);
          setTimeout(function () { if (fw.parentNode) fw.parentNode.removeChild(fw); }, 2600);
        }, bi * 620);
      })(b);
    }
  }

  /* ---------- 事件 ---------- */
  var target = document.createEvent ? document : window;
  function emit(name, detail) {
    try {
      document.dispatchEvent(new CustomEvent(name, { detail: detail }));
    } catch (e) { /* 老浏览器忽略 */ }
  }

  /* ---------- 页面路径工具 ---------- */
  function currentFile() {
    var p = location.pathname.split('/').pop() || '';
    try { p = decodeURIComponent(p); } catch (e) { /* 非法编码就用原值 */ }
    return p && /\.html?$/i.test(p) ? p : 'home.html';
  }
  /* 登录成功后的回跳地址（只接受站内文件名，防开放重定向） */
  function safeNext(raw) {
    if (!raw) return '';
    var v = String(raw).trim();
    if (!v || /:\/\//.test(v) || v.indexOf('//') === 0 || v.indexOf('..') !== -1) return '';
    return v;
  }

  /* ---------- 导航用户区 ---------- */
  var ICON_USER = '<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="8.4" r="3.6"/><path d="M5 20c0-3.6 3.1-5.6 7-5.6s7 2 7 5.6"/></svg>';
  var ICON_CHEV = '<svg class="ic nu-chev" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5"/></svg>';
  var ICON_CASE = '<svg class="ic" viewBox="0 0 24 24"><path d="M3.4 8.2h17.2v10.4a1.6 1.6 0 0 1-1.6 1.6H5a1.6 1.6 0 0 1-1.6-1.6Z"/><path d="M8.4 8.2V5.6A1.6 1.6 0 0 1 10 4h4a1.6 1.6 0 0 1 1.6 1.6v2.6"/></svg>';
  var ICON_OUT = '<svg class="ic" viewBox="0 0 24 24"><path d="M14.6 4.6H6.4A1.8 1.8 0 0 0 4.6 6.4v11.2a1.8 1.8 0 0 0 1.8 1.8h8.2"/><path d="M17 8.6 20.4 12 17 15.4"/><path d="M9.6 12h10.4"/></svg>';
  var ICON_CAM = '<svg class="ic" viewBox="0 0 24 24"><path d="M4.4 7.4h3l1.4-2h6.4l1.4 2h3.4a1.6 1.6 0 0 1 1.6 1.6v9.4a1.6 1.6 0 0 1-1.6 1.6H4.4a1.6 1.6 0 0 1-1.6-1.6V9a1.6 1.6 0 0 1 1.6-1.6Z"/><circle cx="12" cy="13.4" r="3.4"/></svg>';

  var lastDone = 0;

  function renderNavProgress(done) {
    lastDone = done || 0;
    var head = document.querySelector('.nu-menu-head span');
    if (head) head.textContent = titleFor(lastDone).zh + ' · 已登记';
  }

  function renderNavUser(username) {
    var nav = document.querySelector('nav.top');
    if (!nav) return;
    /* 登录页不放用户区：本身就停在登录页，再来一个「登录」按钮没有意义 */
    if (/login\.html$/.test(currentFile())) {
      var old = nav.querySelector('.nav-user');
      if (old) old.parentNode.removeChild(old);
      return;
    }
    var box = nav.querySelector('.nav-user');
    if (!box) {
      box = document.createElement('div');
      box.className = 'nav-user';
      nav.appendChild(box);
    }
    if (!username) {
      box.innerHTML = '<a class="nu-btn" href="login.html?next=' +
        encodeURIComponent(currentFile()) + '">' + ICON_USER + '<span class="nu-txt">登录</span></a>';
      return;
    }
    var initial = username.slice(0, 1).toUpperCase();
    var avImg = avatarImg(getAvatar());
    var avHtml = avImg ? '<img src="' + avImg + '" alt="">' : escapeHtml(initial);
    box.innerHTML =
      '<button class="nu-me" type="button" aria-haspopup="true" aria-expanded="false">' +
        '<span class="nu-av">' + avHtml + '</span>' +
        '<span class="nu-name">' + escapeHtml(username) + '</span>' +
        ICON_CHEV +
      '</button>' +
      '<div class="nu-menu" role="menu">' +
        '<div class="nu-menu-head" role="menuitem" title="查看我的工牌">' +
          '<div class="nu-mh-txt"><b>' + escapeHtml(username) + '</b>' +
            '<span>' + titleFor(lastDone).zh + ' · 已登记</span></div>' +
          miniAvatarHtml() +
        '</div>' +
        '<button role="menuitem" type="button" data-gd="logout">' + ICON_OUT + '退出登录</button>' +
      '</div>';

    var btn = box.querySelector('.nu-me');
    var menu = box.querySelector('.nu-menu');
    function close() {
      box.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = box.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    /* 菜单头的用户卡片：直达我的工牌 */
    menu.querySelector('.nu-menu-head').addEventListener('click', function () {
      close();
      location.href = 'entry.html';
    });
    menu.querySelector('[data-gd="logout"]').addEventListener('click', function (e) {
      e.stopPropagation();
      logout();
      close();
      // 退出后统一返回首页，不留在原页面
      location.href = 'home.html';
    });
    document.addEventListener('click', function (e) {
      if (!box.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* 菜单头的小头像（名字右侧）：rank 头像用图片，letter 用首字母色块 */
  function miniAvatarHtml() {
    var img = avatarImg(getAvatar());
    if (img) return '<img class="nu-mav" src="' + img + '" alt="">';
    var ch = escapeHtml((getUser() || '侦').slice(0, 1).toUpperCase());
    return '<span class="nu-mav nu-mav-letter">' + ch + '</span>';
  }

  /* ---------- 更换头像弹层（随头衔解锁，破 N 案点亮第 N+1 级） ---------- */
  function openAvatarPicker() {
    var modal = document.getElementById('gd-avatar-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'av-modal';
      modal.id = 'gd-avatar-modal';
      modal.innerHTML =
        '<div class="av-scrim"></div>' +
        '<div class="av-card" role="dialog" aria-modal="true" aria-label="更换头像">' +
          '<span class="av-kicker">AVATAR · 侦探证照片</span>' +
          '<h3>挑一张你的侦探形象</h3>' +
          '<p class="av-sub">头像随头衔解锁：每破一案晋升一级，对应头像逐一点亮。选中后按「确认更换」生效。</p>' +
          '<div class="av-grid"></div>' +
          '<p class="av-err"></p>' +
          '<div class="av-actions">' +
            '<span class="av-pick"></span>' +
            '<button type="button" class="btn btn-primary av-apply" disabled>确认更换</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(modal);
      modal.querySelector('.av-scrim').addEventListener('click', closeAvatarPicker);
      modal.querySelector('.av-apply').addEventListener('click', function () {
        applyAvatarPick(modal);
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeAvatarPicker();
      });
    }

    var errEl = modal.querySelector('.av-err');
    errEl.textContent = '';
    var pickEl = modal.querySelector('.av-pick');
    if (pickEl) pickEl.textContent = '';
    /* 默认选中当前头像：打开即可按「确认」（无变化则直接收起），不会出现"点了没反应" */
    var current0 = getAvatar();
    modal.dataset.pending = current0;
    var applyBtn = modal.querySelector('.av-apply');
    applyBtn.disabled = false;
    applyBtn.textContent = '确认更换';
    modal.classList.add('open');

    /* 解锁状态跟进度走（离线/未启动时按 0 案兜底） */
    GD.loadProgress().catch(function () { return GD.emptyProgress(); }).then(function (p) {
      var done = GD.countDone(p || GD.emptyProgress());
      var errEl2 = modal.querySelector('.av-err');
      errEl2.textContent = '';
      var grid = modal.querySelector('.av-grid');
      grid.innerHTML = '';
      var current = getAvatar();
      var curAvatar = null;
      AVATARS.forEach(function (a) {
        var unlocked = done >= a.tier;
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'av-opt' + (a.id === current ? ' active' : '') + (unlocked ? '' : ' locked');
        var need = Math.max(a.tier - done, 1);
        var vis = a.img
          ? '<img src="' + a.img + '" alt="">'
          : '<span class="av-letter">' + escapeHtml((getUser() || '侦').slice(0, 1).toUpperCase()) + '</span>';
        var lock = unlocked ? '' :
          '<span class="av-lock" aria-hidden="true">' +
            '<svg class="ic" viewBox="0 0 24 24"><rect x="5" y="10.4" width="14" height="10.2" rx="2.8"/>' +
            '<path d="M8.4 10.4V7.7a3.6 3.6 0 0 1 7.2 0v2.7"/></svg>' +
          '</span>';
        b.innerHTML =
          '<span class="av-vis">' + vis + lock + '</span>' +
          '<span class="av-name">' + a.label + '</span>' +
          '<span class="av-need">' + (unlocked ? '' : '还差 ' + need + ' 案') + '</span>';
        b.addEventListener('click', function () {
          if (!unlocked) {
            errEl2.textContent = '再破 ' + need + ' 案就能换上这一张';
            b.classList.remove('shake');
            void b.offsetWidth;
            b.classList.add('shake');
            return;
          }
          /* 仅标记待确认，不落库——按「确认更换」才生效。
             点当前原头像也一样：可选、可确认（确认后无变化直接收起），
             不禁用按钮，否则点了像没反应 */
          modal.dataset.pending = a.id;
          modal.querySelectorAll('.av-opt').forEach(function (x) { x.classList.remove('active'); });
          b.classList.add('active');
          applyBtn.disabled = false;
          applyBtn.textContent = '确认更换';
          if (pickEl) pickEl.textContent = '已选 · ' + a.label;
          errEl2.textContent = '';
        });
        if (a.id === current) curAvatar = a;
        grid.appendChild(b);
      });
      /* 打开弹窗即显示当前头像为默认选中项 */
      if (curAvatar && pickEl) pickEl.textContent = '已选 · ' + curAvatar.label;
    });
  }

  /* 应用待确认的头像选择 */
  function applyAvatarPick(modal) {
    var pending = modal.dataset.pending;
    if (!pending) { closeAvatarPicker(); return; }
    if (pending === getAvatar()) { closeAvatarPicker(); return; }
    var errEl = modal.querySelector('.av-err');
    var applyBtn = modal.querySelector('.av-apply');
    applyBtn.disabled = true;
    setAvatar(pending).then(function () {
      errEl.textContent = '';
      setTimeout(closeAvatarPicker, 280);
    }).catch(function (e2) {
      errEl.textContent = e2.message + '——稍后再试。';
      applyBtn.disabled = false;
    });
  }
  function closeAvatarPicker() {
    var m = document.getElementById('gd-avatar-modal');
    if (m) m.classList.remove('open');
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- 启动：渲染导航 + 校验登录态 + 拉进度 ---------- */
  /* 无需登录即可访问的页面（白名单） */
  function isPublicPage(file) {
    return /^(home|login|entry)\.html?$/i.test(file || currentFile());
  }

  /* 页面守卫：未登录时，除白名单页外一律强制跳回首页 */
  function guard() {
    if (getToken()) return false;          /* 已登录：放行 */
    if (isPublicPage()) return false;      /* 公开页：照常打开 */
    location.replace('home.html');         /* 未登录 + 受保护页：强制跳首页 */
    return true;                           /* 已拦截 */
  }

  /* 接案引导守卫：接案引导对话（读完第 2 页后陈探长弹出）还没走完之前，
     导航栏「案件簿」入口一律拦下，防止跳过引导直接去接案。
     全站统一绑定一次，幂等。 */
  var navGuardBound = false;
  function bindCaseNavGuard() {
    if (navGuardBound) return;
    navGuardBound = true;
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('.nav-shell a') : null;
      if (!a) return;
      var href = a.getAttribute('href') || '';
      /* 只盯「案件簿」入口（cases.html） */
      if (href.indexOf('cases.html') < 0) return;
      /* 引导已走完，放行 */
      if (isGuideDone()) return;
      /* 本地无标记可能是换浏览器/清过缓存的老号：先问服务器进度再决定拦不拦 */
      e.preventDefault();
      loadProgress().catch(function () { return emptyProgress(); }).then(function (p) {
        /* 结过案 → 引导必然早完成了：补标记并放行 */
        if (countDone(p) >= 1) {
          try { localStorage.setItem(userKeyNS('gd_guide_done_'), '1'); } catch (err) {}
          location.href = href;
          return;
        }
        /* 已读完第 2 页但引导没走完的老账号：直接补播接案引导，别拿「还没到时候」劝退 */
        if (window.GDGate && window.GDManual && GDManual.isArchived &&
            GDManual.isArchived('c1') && GDManual.playFirstCaseGuide) {
          GDManual.playFirstCaseGuide();
          return;
        }
        if (window.GDGate) {
          GDGate.play({
            force: true,
            lines: [
              '案子还没到你来接的时候。',
              '先把《侦探须知》第 2 页读完，陈探长会亲自把第一宗案交到你手上。'
            ],
            kicker: '引导提醒 · 陈探长',
            endLabel: '好，我继续读手册'
          });
        } else if (bubble) {
          bubble('先把手册第 2 页读完，陈探长才会交给你第一宗案。');
        }
      });
    });
  }

  function boot() {
    /* 先做登录守卫，避免受保护页面内容在未登录时闪现 */
    if (guard()) return;

    /* 全局绑定「案件簿」导航守卫（引导未完成时拦截） */
    bindCaseNavGuard();

    var cached = getUser();
    renderNavUser(cached);
    renderNavProgress(0);

    me().then(function (user) {
      var name = user && user.username ? user.username : '';
      /* token 已失效（401）：后端判定未登录，同样要拦截受保护页 */
      if (!name && !isPublicPage()) { location.replace('home.html'); return; }
      renderNavUser(name);
      emit('gd:auth', { username: name });
      if (!name) { renderNavProgress(0); emit('gd:progress', emptyProgress()); return; }
      return loadProgress().then(function (p) {
        syncOnboardingFromProgress(p);
        renderNavProgress(countDone(p));
      }).catch(function () {
        renderNavProgress(0);
      });
    }).catch(function () {
      // 后端没起来：保留本地缓存的登录外观，页面内容走各自的兜底
      renderNavProgress(0);
      emit('gd:progress', emptyProgress());
    });
  }

  /* ---------- 时间格式化（案件计时 / 排行榜共用）：秒 → mm:ss ---------- */
  function fmtSec(s) {
    s = Math.max(0, Math.round(Number(s) || 0));
    var m = Math.floor(s / 60), r = s % 60;
    return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
  }

  /* ---------- 对外接口 ---------- */
  window.GD = {
    base: BASE,
    api: request,
    getToken: getToken,
    getUser: getUser,
    login: login,
    register: register,
    logout: logout,
    bubble: bubble,
    isManualRead: isManualRead,
    isGuideDone: isGuideDone,
    me: me,
    loadProgress: loadProgress,
    saveProgress: saveProgress,
    resetProgress: resetProgress,
    countDone: countDone,
    caseScore: caseScore,
    caseStars: caseStars,
    finalUnlocked: finalUnlocked,
    isLegend: isLegend,
    eggFireworks: eggFireworks,
    eggBadgeRain: eggBadgeRain,
    eggGiftNote: eggGiftNote,
    emptyProgress: emptyProgress,
    LEVELS: LEVELS,
    TITLES: TITLES,
    titleFor: titleFor,
    AVATARS: AVATARS,
    getAvatar: getAvatar,
    setAvatar: setAvatar,
    openAvatarPicker: openAvatarPicker,
    avatarImg: avatarImg,
    fmtSec: fmtSec,
    currentFile: currentFile,
    safeNext: safeNext,
    loginUrl: function (next) {
      return 'login.html?next=' + encodeURIComponent(safeNext(next) || currentFile());
    },
    requireLogin: function (next) {
      if (getToken()) return true;
      location.href = 'login.html?next=' + encodeURIComponent(safeNext(next) || currentFile());
      return false;
    },
    refreshNav: function () { boot(); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})(window, document);
