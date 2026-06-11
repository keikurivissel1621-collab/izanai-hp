# -*- coding: utf-8 -*-
"""
IZANAI ブログ生成エンジン
  content/articles/*.md  →  blog/<slug>/index.html ＋ blog/index.html ＋ sitemap.xml

特徴:
  - note的リーディングUI（assets/blog.css）／SEOに強い見出し階層(H1=タイトル, H2/H3/H4)
  - 各記事に自動でCTA挿入（中間CTA＋末尾LINE CTA＋「ホーム/会社を知る/LINE」3択）
  - meta / OGP / Twitter / canonical / 構造化データ(BlogPosting + BreadcrumbList) を自動付与
  - 目次(TOC) 自動生成・サイトマップ自動更新

使い方:  python scripts/build_blog.py
依存:    pip install markdown
"""
import os, re, sys, json, html, datetime, glob

# Windowsコンソール(cp932)でも絵文字を出せるようUTF-8に
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============ 設定 ============
SITE       = "https://shirubeai.com"
LINE_URL   = "https://lin.ee/8upkUmI"
ORG        = "株式会社いざない"
ORG_EN     = "IZANAI"
AUTHOR     = "栗田 啓介"
ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # izanai-hp/
ART_DIR    = os.path.join(ROOT, "content", "articles")
BLOG_DIR   = os.path.join(ROOT, "blog")
DEFAULT_OG = "/assets/og-image.jpg"
LOGO_TRANS = "/assets/izanai-logo-transparent.png"
LOGO_WHITE = "/assets/izanai-logo-white.png"
LOGO_PUB   = SITE + "/assets/izanai-logo.png"
LINE_SVG   = "/assets/logos/line.svg"
PORTRAIT   = "/assets/photos/profile-keisuke.jpg"

try:
    import markdown
except ImportError:
    sys.exit("markdown が必要です:  pip install markdown")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_images

# 画像自動取得の設定
REFRESH_IMAGES = "--refresh-images" in sys.argv   # 付けると既存画像も取り直す
IMG_WEB = "/assets/blog-img"
DEFAULT_KW = ["business office team", "corporate teamwork meeting", "modern office workspace"]
LOCAL_FALLBACK = ["/assets/hero/business-team.jpg", "/assets/hero/modern-office.jpg",
                  "/assets/hero/desk-work.jpg", "/assets/hero/laptop-desk.jpg",
                  "/assets/hero/office-meeting.jpg", "/assets/hero/laptop-code.jpg"]
_fb = [0]
def _fallback():
    p = LOCAL_FALLBACK[_fb[0] % len(LOCAL_FALLBACK)]; _fb[0] += 1; return p

# ============ frontmatter パーサ ============
def parse_front(text):
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end+4:].lstrip("\n")
    meta = {}
    key = None
    for line in raw.split("\n"):
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                meta[key] = []
            elif val.startswith("[") and val.endswith("]"):
                meta[key] = [v.strip().strip('"\'') for v in val[1:-1].split(",") if v.strip()]
            else:
                meta[key] = val.strip().strip('"\'')
        elif line.lstrip().startswith("-") and key is not None:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(line.lstrip()[1:].strip().strip('"\''))
    return meta, body

# ============ ユーティリティ ============
def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

def reading_time(plain):
    n = len(re.sub(r"\s", "", plain))
    return max(1, round(n / 500))

def jp_date(s):
    try:
        d = datetime.date.fromisoformat(s)
        return f"{d.year}年{d.month}月{d.day}日", d.isoformat()
    except Exception:
        return s, s

def excerpt(meta, plain):
    if meta.get("description"):
        return meta["description"]
    t = plain.strip().replace("\n", " ")
    return (t[:108] + "…") if len(t) > 108 else t

def og_url(path):
    return path if path.startswith("http") else SITE + path

# ============ 目次HTML ============
def build_toc(tokens):
    # tokens: markdown toc_tokens（level2,3 のみ採用）
    items = []
    for t in tokens:
        if t["level"] == 2:
            items.append((2, t["id"], t["name"]))
            for c in t.get("children", []):
                if c["level"] == 3:
                    items.append((3, c["id"], c["name"]))
    if not items:
        return ""
    li = []
    for lv, _id, name in items:
        cls = "lv3" if lv == 3 else "lv2"
        li.append(f'<li class="{cls}"><a href="#{_id}">{html.escape(name)}</a></li>')
    return '<ul class="toc-list">' + "".join(li) + "</ul>"

# ============ 中間CTA挿入（2つ目のH2直前） ============
MID_CTA = (
    '<div class="cta-mid">'
    '<h4>AI導入、自己流で進めて大丈夫ですか？</h4>'
    '<p>情報漏えい・社内ルール・法規制のリスクを整理し、全社で“使える状態”まで伴走します。'
    'まずは無料相談で、御社の状況に合わせた最初の一歩をお伝えします。</p>'
    f'<a class="btn btn-line" href="{LINE_URL}" target="_blank" rel="noopener">'
    f'<img class="linelogo" src="{LINE_SVG}" alt="LINE"/>公式LINEで無料相談する</a>'
    '</div>'
)
def inject_mid(body_html):
    idxs = [m.start() for m in re.finditer(r"<h2", body_html)]
    if len(idxs) >= 3:
        pos = idxs[1]
        return body_html[:pos] + MID_CTA + body_html[pos:]
    return body_html

# ============ 共通パーツ ============
def header(active=""):
    def cur(name): return " current" if name == active else ""
    return f'''<div class="progress" id="progress"></div>
<header class="site-header">
  <div class="wrap nav">
    <a class="brand" href="/index_rebuild.html" aria-label="{ORG} ホーム"><img class="brand-logo" src="{LOGO_TRANS}" alt="{ORG_EN} {ORG}"/></a>
    <nav class="menu">
      <a class="link" href="/index_rebuild.html#service">サービス</a>
      <a class="link link-cc" href="/claude-code.html">Claude Code実装支援</a>
      <a class="link" href="/index_rebuild.html#pricing">料金</a>
      <a class="link{cur('blog')}" href="/blog/">ブログ</a>
      <a class="link" href="/index_rebuild.html#about">会社概要</a>
      <a class="btn btn-line" href="{LINE_URL}" target="_blank" rel="noopener"><img class="linelogo" src="{LINE_SVG}" alt="LINE"/>無料相談</a>
    </nav>
    <button class="burger" id="burger" aria-label="メニュー"><span></span><span></span><span></span></button>
  </div>
</header>
<div class="mobile-menu" id="mobileMenu">
  <a href="/index_rebuild.html#service">サービス</a>
  <a href="/claude-code.html" style="color:var(--teal)">Claude Code実装支援 →</a>
  <a href="/index_rebuild.html#pricing">料金</a>
  <a href="/blog/">ブログ</a>
  <a href="/index_rebuild.html#about">会社概要</a>
  <a class="btn btn-line" href="{LINE_URL}" target="_blank" rel="noopener"><img class="linelogo" src="{LINE_SVG}" alt="LINE"/>公式LINEで無料相談</a>
</div>'''

def footer():
    return f'''<footer>
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-brand">
        <img class="foot-logo" src="{LOGO_WHITE}" alt="{ORG_EN} {ORG}"/>
        <p>{ORG}｜AI導入の不安を、先回りして取り除く。セキュリティに強いAI伴走支援。</p>
      </div>
      <div class="foot-nav">
        <div class="col"><h5>サービス</h5>
          <a href="/index_rebuild.html#service">AI伴走支援</a><a href="/claude-code.html">Claude Code実装支援</a><a href="/index_rebuild.html#pricing">料金</a><a href="/blog/">ブログ</a><a href="/lp.html">3分AIリスクチェック</a>
        </div>
        <div class="col"><h5>会社情報</h5>
          <a href="/index_rebuild.html#about">会社概要</a><a href="/index_rebuild.html#ceo">代表者</a><a href="/index_rebuild.html#privacy">プライバシーポリシー</a><a href="/tokushoho.html">特定商取引法に基づく表記</a>
        </div>
        <div class="col"><h5>お問い合わせ</h5>
          <a href="{LINE_URL}" target="_blank" rel="noopener">公式LINEで無料相談</a>
        </div>
      </div>
    </div>
    <div class="foot-bottom"><span>© 2026 {ORG}（{ORG_EN}）</span><span>AI導入の不安を、先回りして取り除く。</span></div>
  </div>
</footer>
<script src="/assets/blog.js"></script>'''

def head(title, desc, canonical, ogimg, og_type="article", extra=""):
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8"/>
<script defer src="/assets/ga.js"></script>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}"/>
<link rel="canonical" href="{canonical}"/>
<meta property="og:type" content="{og_type}"/>
<meta property="og:title" content="{html.escape(title)}"/>
<meta property="og:description" content="{html.escape(desc)}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:image" content="{og_url(ogimg)}"/>
<meta property="og:site_name" content="{ORG} {ORG_EN}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{html.escape(title)}"/>
<meta name="twitter:description" content="{html.escape(desc)}"/>
<meta name="twitter:image" content="{og_url(ogimg)}"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&family=Noto+Sans+JP:wght@400;500;700;900&family=Noto+Serif+JP:wght@500;600;700;900&display=swap" rel="stylesheet"/>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
<link rel="icon" href="/favicon-32x32.png" sizes="32x32" type="image/png"/>
<link rel="apple-touch-icon" href="/apple-touch-icon.png"/>
<link rel="icon" href="/favicon.ico" sizes="any"/>
<link rel="stylesheet" href="/assets/blog.css?v=2"/>
{extra}
</head>
<body>'''

# ============ 画像の自動取得（カバー＋本文挿絵） ============
def prepare_images(slug, meta, body):
    """記事ごとに無料画像を取得。カバー(サムネ)＋本文挿絵を用意し、bodyを書き換えて返す。"""
    imgdir = os.path.join(ROOT, "assets", "blog-img", slug)
    os.makedirs(imgdir, exist_ok=True)
    cfile = os.path.join(imgdir, "_credits.json")
    try:
        credits = json.load(open(cfile, encoding="utf-8")) if os.path.exists(cfile) else {}
    except Exception:
        credits = {}

    kw = meta.get("image_keywords")
    if not isinstance(kw, list) or not kw:
        kw = list(DEFAULT_KW)
    kw = [str(k).strip() for k in kw if str(k).strip()] or list(DEFAULT_KW)

    req_credits = []
    def grab(query, fname, offset):
        dest = os.path.join(imgdir, fname)
        web = f"{IMG_WEB}/{slug}/{fname}"
        info = None
        if os.path.exists(dest) and not REFRESH_IMAGES:
            info = credits.get(fname)
        else:
            info = fetch_images.fetch(query, dest, offset=offset)
            if info:
                credits[fname] = info
        if info:
            if info.get("req") and info.get("credit"):
                req_credits.append(info["credit"])
            return web
        return None

    # カバー（サムネ）: thumbnail未指定 or "auto" のとき取得
    th = str(meta.get("thumbnail", "")).strip()
    if not th or th.lower() == "auto":
        meta["thumbnail"] = grab(kw[0] + " business", "cover.jpg", 0) or _fallback()

    # 本文プレースホルダ  ![alt](auto[:keyword])  を画像に置換
    pat = re.compile(r'!\[([^\]]*)\]\(\s*auto(?::\s*([^)]*))?\s*\)')
    cnt = [0]
    def repl(m):
        cnt[0] += 1
        q = (m.group(2) or "").strip() or kw[cnt[0] % len(kw)]
        web = grab(q + " business", f"body-{cnt[0]}.jpg", cnt[0] + 1)
        return f'![{m.group(1)}]({web or _fallback()})'
    body = pat.sub(repl, body)

    # プレースホルダが無い記事には、2番目・4番目のH2直後に自動で挿絵
    if cnt[0] == 0:
        out, h2, ins = [], 0, 0
        for ln in body.split("\n"):
            out.append(ln)
            if ln.startswith("## "):
                h2 += 1
                if h2 in (2, 4):
                    ins += 1
                    web = grab(kw[ins % len(kw)] + " business", f"body-{ins}.jpg", ins + 1)
                    out.append("")
                    out.append(f'![{ln[3:].strip()}]({web or _fallback()})')
        body = "\n".join(out)

    try:
        json.dump(credits, open(cfile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass

    seen, uniq = set(), []
    for c in req_credits:
        if c and c not in seen:
            seen.add(c); uniq.append(c)
    return body, uniq

# ============ 記事ロード ============
def load_articles():
    arts = []
    for path in glob.glob(os.path.join(ART_DIR, "*.md")):
        if os.path.basename(path).startswith("_"):  # _README.md 等は除外
            continue
        with open(path, encoding="utf-8") as f:
            meta, body = parse_front(f.read())
        if meta.get("draft") in ("true", "True", True):
            continue
        slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
        body, img_credits = prepare_images(slug, meta, body)  # 画像を自動取得・本文に挿入
        md = markdown.Markdown(extensions=["extra", "sane_lists", "toc"],
                               extension_configs={"toc": {"toc_depth": "2-4"}})
        body_html = md.convert(body)
        plain = strip_tags(body_html)
        disp_date, iso_date = jp_date(meta.get("date", ""))
        arts.append({
            "slug": slug, "meta": meta, "body_html": body_html, "plain": plain,
            "img_credits": img_credits,
            "toc": getattr(md, "toc_tokens", []),
            "title": meta.get("title", slug),
            "desc": excerpt(meta, plain),
            "category": meta.get("category", "AI活用"),
            "tags": meta.get("tags", []) if isinstance(meta.get("tags", []), list) else [],
            "thumb": meta.get("thumbnail", ""),
            "date": meta.get("date", ""), "disp_date": disp_date, "iso_date": iso_date,
            "updated": meta.get("updated", meta.get("date", "")),
            "rt": reading_time(plain),
        })
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts

# ============ 記事ページ生成 ============
def render_article(a, others):
    canonical = f"{SITE}/blog/{a['slug']}/"
    ogimg = a["thumb"] or DEFAULT_OG
    toc_html = build_toc(a["toc"])
    body_html = inject_mid(a["body_html"])

    # cover
    if a["thumb"]:
        cover = f'<div class="a-cover"><img src="{a["thumb"]}" alt="{html.escape(a["title"])}" loading="eager"/></div>'
    else:
        cover = ""

    # 目次（インライン＝モバイル）
    toc_inline = (f'<nav class="toc-inline"><div class="toc-ttl">目次</div>{toc_html}</nav>'
                  if toc_html else "")
    # 右レール（PC）
    rail_toc = (f'<div class="toc-card"><div class="toc-ttl">目次</div>{toc_html}</div>'
                if toc_html else "")

    # 関連記事
    rel = [o for o in others if o["slug"] != a["slug"]][:3]
    rel_cards = "".join(card_html(o) for o in rel)
    related = (f'<section class="related"><h3>あわせて読みたい</h3><div class="rel-grid">{rel_cards}</div></section>'
               if rel else "")

    # 構造化データ
    ld_article = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a["title"], "description": a["desc"],
        "image": [og_url(ogimg)], "datePublished": a["iso_date"] + "T09:00:00+09:00",
        "dateModified": jp_date(a["updated"])[1] + "T09:00:00+09:00",
        "author": {"@type": "Organization", "name": ORG, "url": SITE},
        "publisher": {"@type": "Organization", "name": ORG,
                      "logo": {"@type": "ImageObject", "url": LOGO_PUB}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "inLanguage": "ja",
        "keywords": ", ".join(a["tags"]) if a["tags"] else a["category"],
    }
    ld_crumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "ブログ", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": a["title"], "item": canonical},
        ],
    }
    ld = (f'<script type="application/ld+json">{json.dumps(ld_article, ensure_ascii=False)}</script>'
          f'<script type="application/ld+json">{json.dumps(ld_crumb, ensure_ascii=False)}</script>')

    tags_html = ("".join(f'<span class="chip" style="background:var(--gold-soft);color:#8a6d1f;margin-right:6px">#{html.escape(t)}</span>' for t in a["tags"]))

    # 画像クレジット（表示が必要なライセンスのときだけ）
    credit_html = ""
    if a.get("img_credits"):
        items = " ／ ".join(html.escape(c) for c in a["img_credits"])
        credit_html = f'<p style="font-size:11px;color:var(--muted);margin-top:16px">画像：{items}</p>'

    out = head(f'{a["title"]}｜{ORG} {ORG_EN}', a["desc"], canonical, ogimg, "article", ld)
    out += header("blog")
    out += f'''
<div class="wrap">
  <div class="crumb"><a href="/index_rebuild.html">ホーム</a><span>›</span><a href="/blog/">ブログ</a><span>›</span>{html.escape(a["category"])}</div>
</div>
<main class="article"><div class="wrap"><div class="article-grid">
  <article class="article-main">
    <div class="a-head">
      <span class="chip">{html.escape(a["category"])}</span>
      <h1 class="a-title">{html.escape(a["title"])}</h1>
      <div class="a-meta">
        <span class="who"><img src="{PORTRAIT}" alt="{AUTHOR}" onerror="this.style.display='none'"/>{ORG}</span>
        <span class="dot"></span><time datetime="{a["iso_date"]}">{a["disp_date"]}</time>
        <span class="dot"></span><span>約{a["rt"]}分で読めます</span>
      </div>
    </div>
    {cover}
    {toc_inline}
    <div class="prose">
{body_html}
    </div>
    <div style="margin-top:28px">{tags_html}</div>
    {credit_html}

    <!-- ===== 記事末CTA（自動） ===== -->
    <div class="a-cta">
      <div class="cta-line-box">
        <div class="lead">AI導入の不安、ひとりで抱えていませんか？</div>
        <p>「何から始めればいいか分からない」段階こそ相談どき。御社の状況に合わせた最初の一歩を、無料でお伝えします。</p>
        <a class="btn" href="{LINE_URL}" target="_blank" rel="noopener"><img class="linelogo" src="{LINE_SVG}" alt="LINE"/>公式LINEで無料相談する</a>
      </div>
      <div class="cta-3">
        <a href="/index_rebuild.html"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/></svg></span><span class="t">トップページへ</span><span class="d">IZANAIのサービス全体を見る</span></a>
        <a href="/index_rebuild.html#about"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/></svg></span><span class="t">私たちについて</span><span class="d">{ORG}の想い・実績を知る</span></a>
        <a href="/claude-code.html"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="m7.5 9 3 3-3 3"/><path d="M12.5 15h4"/></svg></span><span class="t">Claude Code実装支援</span><span class="d">全社AI自動化の導入支援</span></a>
      </div>
    </div>

    <!-- 執筆者 -->
    <div class="author-box">
      <img src="{PORTRAIT}" alt="{AUTHOR}" onerror="this.style.visibility='hidden'"/>
      <div>
        <div class="nm">{ORG}（{ORG_EN}）／ {AUTHOR}</div>
        <div class="bio">「AI導入の不安を、先回りして取り除く」をミッションに、セキュリティに強いAI伴走支援を提供。情報漏えい・社内ルール・法規制のリスクを整理しながら、全社で“使える状態”まで伴走します。<a href="/index_rebuild.html#about">会社概要を見る →</a></div>
      </div>
    </div>

    {related}
  </article>

  <aside class="rail">
    {rail_toc}
    <div class="line-card">
      <div class="t">まずは無料相談</div>
      <div class="d">AI導入の最初の一歩を、御社に合わせてご提案します。</div>
      <a class="btn btn-line" href="{LINE_URL}" target="_blank" rel="noopener"><img class="linelogo" src="{LINE_SVG}" alt="LINE"/>公式LINE</a>
    </div>
  </aside>
</div></div></main>
'''
    out += footer()
    out += "\n</body>\n</html>"
    return out

# ============ 一覧カード ============
def card_html(a):
    href = f'/blog/{a["slug"]}/'
    if a["thumb"]:
        thumb = f'<div class="post-thumb"><img src="{a["thumb"]}" alt="{html.escape(a["title"])}" loading="lazy"/><span class="ph-cat">{html.escape(a["category"])}</span></div>'
    else:
        thumb = f'<div class="post-thumb"><span class="ph-cat">{html.escape(a["category"])}</span></div>'
    return f'''<a class="post-card" href="{href}">
  {thumb}
  <div class="post-body">
    <h2>{html.escape(a["title"])}</h2>
    <p class="ex">{html.escape(a["desc"])}</p>
    <div class="pm"><time datetime="{a["iso_date"]}">{a["disp_date"]}</time>・約{a["rt"]}分</div>
  </div>
</a>'''

# ============ 一覧ページ ============
def render_index(arts):
    canonical = f"{SITE}/blog/"
    title = f"ブログ｜AI導入のお役立ち記事｜{ORG} {ORG_EN}"
    desc = "AI導入のセキュリティ・社内ルール・法規制・全社活用のリアルなノウハウを、実務目線で発信。中小企業のAI伴走支援を行う株式会社いざない（IZANAI）公式ブログ。"
    cards = "".join(card_html(a) for a in arts) if arts else '<p class="blog-empty">記事を準備中です。近日公開します。</p>'
    ld = {
        "@context": "https://schema.org", "@type": "Blog",
        "name": f"{ORG} ブログ", "url": canonical, "description": desc,
        "publisher": {"@type": "Organization", "name": ORG, "logo": {"@type": "ImageObject", "url": LOGO_PUB}},
    }
    out = head(title, desc, canonical, DEFAULT_OG, "website",
               f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    out += header("blog")
    out += f'''
<section class="blog-hero"><div class="wrap">
  <span class="eyebrow">IZANAI BLOG</span>
  <h1>AI導入の“つまずき”を、先回りで解く。</h1>
  <p>セキュリティ・社内ルール・法規制・全社活用まで。中小企業のAI伴走支援で見えてきた実務ノウハウを発信します。</p>
</div></section>
<div class="wrap"><div class="post-grid">{cards}</div></div>
'''
    out += footer()
    out += "\n</body>\n</html>"
    return out

# ============ サイトマップ ============
def write_sitemap(arts):
    static = [("/index_rebuild.html", "1.0", "weekly"),
              ("/claude-code.html", "0.8", "monthly"),
              ("/lp.html", "0.6", "monthly"),
              ("/blog/", "0.9", "daily"),
              ("/tokushoho.html", "0.3", "yearly")]
    urls = []
    for path, pr, freq in static:
        urls.append(f"  <url><loc>{SITE}{path}</loc><changefreq>{freq}</changefreq><priority>{pr}</priority></url>")
    for a in arts:
        lm = jp_date(a["updated"])[1]
        urls.append(f"  <url><loc>{SITE}/blog/{a['slug']}/</loc><lastmod>{lm}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

# ============ メイン ============
def main():
    os.makedirs(ART_DIR, exist_ok=True)
    os.makedirs(BLOG_DIR, exist_ok=True)
    arts = load_articles()

    for a in arts:
        d = os.path.join(BLOG_DIR, a["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_article(a, arts))

    with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(arts))

    write_sitemap(arts)

    print(f"🖼  画像ソース: {fetch_images.source_name()}（記事ごとに自動取得・キャッシュ）")
    print(f"✅ 記事 {len(arts)} 本を生成")
    for a in arts:
        print(f"   - /blog/{a['slug']}/  「{a['title']}」({a['rt']}分)")
    print("✅ /blog/ 一覧・sitemap.xml・robots.txt を更新")

if __name__ == "__main__":
    main()
