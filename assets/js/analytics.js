/* ============================================================
   MUKIAI サイト共通：拡張計測スクリプト
   ------------------------------------------------------------
   前提：GA4本体の読み込み・config・LINEクリック計測(line_click)は
   既存の assets/ga.js（測定ID: G-B5J7XPC7L3）が担当する。
   本ファイルはそれに乗る「追加イベント送信」専用：
     - scroll_depth : スクロール深度 25/50/75/90% 到達（各1回）
     - cta_view     : LINE CTA（a[href*="lin.ee"]）が初めて50%以上
                      可視になったとき（1要素1回）
   ＋ Microsoft Clarity（CLARITY_ID を記入すると自動で有効化）

   注意：
   - クリック計測は ga.js の line_click に一本化済み。ここでは送らない。
   - 万一 ga.js が読み込まれていない場合のみ、フォールバックとして
     gtag.js（G-B5J7XPC7L3）を読み込んで config する。
   - 読み込み順は「ga.js → analytics.js」（両方 defer、記述順に実行）。
   - gtag が未定義でも例外を出さない防御的実装。
   ============================================================ */
(function () {
  "use strict";

  /* GA4測定ID（ga.jsと同一。フォールバック時のみ使用） */
  var GA_MEASUREMENT_ID = "G-B5J7XPC7L3";

  /* ---------------- フォールバックGA4ローダー ----------------
     通常は ga.js が gtag を定義済みなので、ここは何もしない。 */
  function ensureGA() {
    if (typeof window.gtag === "function") return;
    // 二重読み込みガード
    if (window.__mukiaiGaFallback) return;
    window.__mukiaiGaFallback = true;

    if (!document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
      var s = document.createElement("script");
      s.async = true;
      s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_MEASUREMENT_ID;
      document.head.appendChild(s);
    }
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", GA_MEASUREMENT_ID);
  }

  /* gtag未定義・例外時も落ちない防御的呼び出し */
  function safeGtag() {
    try {
      if (typeof window.gtag === "function") {
        window.gtag.apply(window, arguments);
      } else if (window.dataLayer && window.dataLayer.push) {
        window.dataLayer.push(arguments);
      }
    } catch (e) {
      /* no-op: 計測エラーでサイト機能を壊さない */
    }
  }

  /* ---------------- スロットル ---------------- */
  function throttle(fn, wait) {
    var last = 0, timer = null;
    return function () {
      var now = Date.now();
      var args = arguments, ctx = this;
      if (now - last >= wait) {
        last = now;
        fn.apply(ctx, args);
      } else if (!timer) {
        timer = setTimeout(function () {
          last = Date.now();
          timer = null;
          fn.apply(ctx, args);
        }, wait - (now - last));
      }
    };
  }

  /* ---------------- スクロール深度計測 ---------------- */
  function initScrollDepth() {
    var THRESHOLDS = [25, 50, 75, 90];
    var fired = {};

    function calcPercent() {
      var doc = document.documentElement;
      var body = document.body;
      var scrollTop = window.pageYOffset || doc.scrollTop || 0;
      var winH = window.innerHeight || doc.clientHeight || 0;
      var docH = Math.max(
        body ? body.scrollHeight : 0,
        body ? body.offsetHeight : 0,
        doc.scrollHeight,
        doc.offsetHeight,
        doc.clientHeight
      );
      var scrollable = docH - winH;
      if (scrollable <= 0) return 100;
      return Math.min(100, Math.round((scrollTop / scrollable) * 100));
    }

    function check() {
      try {
        var pct = calcPercent();
        for (var i = 0; i < THRESHOLDS.length; i++) {
          var t = THRESHOLDS[i];
          if (!fired[t] && pct >= t) {
            fired[t] = true;
            safeGtag("event", "scroll_depth", {
              percent_scrolled: t,
              page_path: location.pathname
            });
          }
        }
      } catch (e) {
        /* no-op */
      }
    }

    var throttled = throttle(check, 300);
    window.addEventListener("scroll", throttled, { passive: true });
    // 初期表示で既に閾値を超えているケース（短いページ等）に対応
    check();
  }

  /* ---------------- CTA到達計測（IntersectionObserver） ---------------- */
  function initCtaView() {
    var links = document.querySelectorAll('a[href*="lin.ee"]');
    if (!links.length) return;

    if (typeof IntersectionObserver === "undefined") return; // 未対応環境は静かにスキップ

    var seen = new WeakSet();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
          var el = entry.target;
          if (seen.has(el)) return;
          seen.add(el);
          safeGtag("event", "cta_view", {
            link_url: el.href,
            page_path: location.pathname
          });
          observer.unobserve(el);
        }
      });
    }, { threshold: [0.5] });

    links.forEach(function (el) {
      try { observer.observe(el); } catch (e) { /* no-op */ }
    });
  }

  /* ---------------- Microsoft Clarity ---------------- */
  // 代表がClarityプロジェクト作成後、ここにプロジェクトIDを記入すると有効化される
  var CLARITY_ID = "xnaqkh3ivw";

  function loadClarity() {
    if (!CLARITY_ID) return;
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r);
      t.async = 1;
      t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0];
      y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", CLARITY_ID);
  }

  /* ---------------- 初期化 ---------------- */
  function init() {
    ensureGA();
    loadClarity();
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        initScrollDepth();
        initCtaView();
      });
    } else {
      initScrollDepth();
      initCtaView();
    }
  }

  init();
})();
