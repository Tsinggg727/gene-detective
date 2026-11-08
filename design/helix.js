/* ==========================================================
   全站背景：水彩蓝双螺旋
   首页拿它当封面主视觉，其余页面淡一档，只作纸面上的纹样
   画布由脚本自己建，页面里不用再写 <canvas>
   ========================================================== */
(function () {
  'use strict';

  /* 系统开了「减少动态效果」就整块不画，别跟用户的偏好较劲 */
  var calm = false;
  try { calm = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  if (calm) return;

  var cv = document.createElement('canvas');
  cv.id = 'helix';
  cv.setAttribute('aria-hidden', 'true');
  /* 有封面主视觉的页面（首页）把画布塞进 hero：压在水彩纸之上、文字之下。
     其余页面挂在 body，当整页背景 */
  var hero = document.getElementById('hero');
  if (hero) {
    cv.className = 'is-strong';
    hero.insertBefore(cv, hero.firstChild);
  } else {
    document.body.appendChild(cv);
  }

  var cx = cv.getContext('2d');
  var W = 0, H = 0, DPR = 1, t0 = 0, on = true;
  var dyes = ['#5872b0', '#6a90c2', '#7767b4', '#3a4878'];

  function size() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = cv.width = Math.round(cv.offsetWidth * DPR);
    H = cv.height = Math.round(cv.offsetHeight * DPR);
  }
  size();
  addEventListener('resize', size, { passive: true });

  function draw() {
    if (!on) return;
    cx.clearRect(0, 0, W, H);

    /* 窄屏把节点拉开，免得一排点挤成仪器面板 */
    var narrow = cv.offsetWidth < 720;
    var step = (narrow ? 96 : 72) * DPR;
    var amp = Math.min(H * .30, W * .155, 240 * DPR);
    var mid = H * .5;
    var N = Math.ceil(W / step) + 2;
    var drift = (t0 * 26 * DPR) % step;

    for (var i = 0; i < N; i++) {
      var x = i * step - drift;
      var ph = x / (168 * DPR) + t0 * 1.0;
      var y1 = mid + Math.sin(ph) * amp;
      var y2 = mid + Math.sin(ph + Math.PI) * amp;
      var depth = (Math.cos(ph) + 1) / 2;   /* 1 = 朝前，0 = 转到背后 */

      /* 碱基对：朝前的那段实、背面那段虚 */
      cx.strokeStyle = 'rgba(76,100,162,' + (.19 + depth * .3).toFixed(3) + ')';
      cx.lineWidth = (1.3 + depth * 1.7) * DPR;
      cx.beginPath();
      cx.moveTo(x, y1);
      cx.lineTo(x, y2);
      cx.stroke();

      var r = (3.0 + depth * 3.9) * DPR;
      var a = .38 + depth * .5;
      var tint = dyes[i % 4];

      /* 先垫一层放大两倍的光晕，再点核心，像水彩没干透的洇开 */
      cx.globalAlpha = a * .4;
      cx.fillStyle = tint;
      cx.beginPath(); cx.arc(x, y1, r * 2.1, 0, 7); cx.fill();
      cx.beginPath(); cx.arc(x, y2, r * 2.1, 0, 7); cx.fill();

      cx.globalAlpha = a;
      cx.beginPath(); cx.arc(x, y1, r, 0, 7); cx.fill();
      cx.beginPath(); cx.arc(x, y2, r, 0, 7); cx.fill();
    }
    cx.globalAlpha = 1;

    /* 两条链的脊线：连续的一笔，比一堆点更像螺旋 */
    var span = W + step;
    for (var s2 = 0; s2 < 2; s2++) {
      var off = s2 ? Math.PI : 0;
      cx.beginPath();
      for (var xx = -step; xx <= span; xx += 7 * DPR) {
        var pp = xx / (168 * DPR) + t0 * 1.0 + off;
        var yy = mid + Math.sin(pp) * amp;
        if (xx <= -step) cx.moveTo(xx, yy); else cx.lineTo(xx, yy);
      }
      cx.strokeStyle = 'rgba(86,110,172,.24)';
      cx.lineWidth = 1.8 * DPR;
      cx.stroke();
    }

    t0 += .0085;
    requestAnimationFrame(draw);
  }

  /* 切到后台就停，回来继续 —— 省电，也免得回来时跳一大格 */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      on = false;
    } else if (!on) {
      on = true;
      requestAnimationFrame(draw);
    }
  });

  requestAnimationFrame(draw);
})();
