/* ==========================================================
   基因侦探 · 全站共用脚本
   滚动进度线 / 滚动渐入 / 导航收缩
   ========================================================== */
(function () {
  /* ---------- 滚动进度线 ---------- */
  var progress = document.getElementById('progress');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var p = max > 0 ? h.scrollTop / max : 0;
    if (progress) progress.style.transform = 'scaleX(' + p + ')';
    var nav = document.querySelector('nav.top');
    if (nav) nav.classList.toggle('shrink', h.scrollTop > 24);
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll, { passive: true });
  onScroll();

  /* ---------- 滚动渐入（渐进增强） ----------
     默认全部可见；只把「一开始就在视口下方」的元素标记为等待，
     滚动进入时再显形。首屏 / 无 JS / 观察器失效都不会出现空白。 */
  var rvObs = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); rvObs.unobserve(e.target); }
    });
  }, { threshold: .1, rootMargin: '0px 0px -6% 0px' });

  function markWaiting() {
    document.querySelectorAll('.rv:not(.rv-wait)').forEach(function (el) {
      if (el.getBoundingClientRect().top > innerHeight * .92) {
        el.classList.add('rv-wait');
        rvObs.observe(el);
      }
    });
  }
  markWaiting();
  addEventListener('load', markWaiting);
  addEventListener('resize', markWaiting, { passive: true });
})();
