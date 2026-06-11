/* ============================================================
   IZANAI サイト共通：Google Analytics 4（GA4）ローダー
   ------------------------------------------------------------
   ★測定IDはこの1ファイルだけを書き換えればOK★
   下の GA_MEASUREMENT_ID を、GA4で取得した「G-XXXXXXXXXX」に
   差し替えると、サイト全ページの計測が一斉に有効になります。
   未設定（プレースホルダのまま）の間は何も送信しません。
   ============================================================ */
(function () {
  var GA_MEASUREMENT_ID = "G-XXXXXXXXXX"; // ← ここを実IDに差し替える

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
})();
