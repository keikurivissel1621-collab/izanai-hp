/* ============================================================
   MUKIAI サイト共通：Google Analytics 4（GA4）ローダー
   ------------------------------------------------------------
   ★測定IDはこの1ファイルだけを書き換えればOK★
   下の GA_MEASUREMENT_ID を、GA4で取得した「G-B5J7XPC7L3」に
   差し替えると、サイト全ページの計測が一斉に有効になります。
   未設定（プレースホルダのまま）の間は何も送信しません。
   ============================================================ */
(function () {
  var GA_MEASUREMENT_ID = "G-B5J7XPC7L3"; // ← ここを実IDに差し替える

  // プレースホルダのままなら計測しない（誤送信・エラー防止）
  if (!GA_MEASUREMENT_ID || GA_MEASUREMENT_ID === "G-XXXXXXXXXX") return;

  // gtag.js 本体を読み込み
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_MEASUREMENT_ID;
  document.head.appendChild(s);

  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag("js", new Date());
  gtag("config", GA_MEASUREMENT_ID);

  /* ====== 成果計測：公式LINE（lin.ee）クリックを line_click イベントで送信 ======
     GA4の自動計測(outbound click)に加え、明示イベントも送って取りこぼしを防ぐ。
     GA4管理画面で「line_click」をキーイベントに指定するとCV計測になる。 */
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href*="lin.ee"]') : null;
    if (!a) return;
    gtag("event", "line_click", {
      link_url: a.href,
      link_text: (a.innerText || a.textContent || "").trim().slice(0, 60),
      page_path: location.pathname
    });
  }, true);
})();
