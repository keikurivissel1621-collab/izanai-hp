# -*- coding: utf-8 -*-
"""
無料画像の自動取得モジュール（記事サムネ＋本文挿絵用）

ソース優先度:
  1) Pexels API … 環境変数 PEXELS_API_KEY があれば最優先（高品質なビジネス写真）
  2) Openverse  … キー不要。CC0（著作権表示不要・商用可）を優先的に取得

使い方（build_blog.py から）:
  from fetch_images import fetch
  info = fetch("business meeting office", "/path/to/dest.jpg", offset=0)
  # info = {"credit": "...", "req": False(=表示不要) / True(=表示必要)}  失敗時 None
"""
import os, io, json, urllib.request, urllib.parse

try:
    from PIL import Image
except ImportError:
    Image = None

def _load_pexels_key():
    """環境変数 PEXELS_API_KEY、無ければ scripts/pexels_key.txt（Git管理外）から読む。"""
    k = os.environ.get("PEXELS_API_KEY", "").strip()
    if k:
        return k
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in ("pexels_key.txt", ".pexels_key"):
        p = os.path.join(here, fn)
        if os.path.exists(p):
            try:
                v = open(p, encoding="utf-8").read().strip()
                if len(v) >= 20 and "ここ" not in v and "YOUR" not in v.upper():
                    return v
            except Exception:
                pass
    return ""

PEXELS_KEY = _load_pexels_key()
UA = "Mozilla/5.0 (compatible; MUKIAI-blog-bot/1.0)"
_cache = {}

def _get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()

def _search_pexels(query, n=24):
    u = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "orientation": "landscape", "per_page": n, "size": "large"})
    d = json.loads(_get(u, {"Authorization": PEXELS_KEY, "User-Agent": UA}))
    out = []
    for p in d.get("photos", []):
        src = p.get("src", {})
        img = src.get("large2x") or src.get("large") or src.get("original")
        if img:
            out.append({"img": img, "credit": "Photo by %s on Pexels" % p.get("photographer", ""), "req": False})
    return out

def _search_openverse(query, n=24):
    out = []
    for lic in ("cc0", "commercial"):  # CC0（表示不要）を優先
        u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
            {"q": query, "license_type": lic, "size": "large",
             "aspect_ratio": "wide", "page_size": n, "mature": "false"})
        try:
            d = json.loads(_get(u))
        except Exception:
            continue
        for p in d.get("results", []):
            if not p.get("url"):
                continue
            need = p.get("license") not in ("cc0", "pdm")  # CC0/PDM以外は表示推奨
            cred = (p.get("attribution") or ("%s / %s" % (p.get("title", ""), p.get("creator", "")))).strip(" /")
            out.append({"img": p["url"], "credit": cred, "req": need})
        if out:
            break
    return out

def search(query):
    if query in _cache:
        return _cache[query]
    items = []
    if PEXELS_KEY:
        try:
            items = _search_pexels(query)
        except Exception:
            items = []
    if not items:
        try:
            items = _search_openverse(query)
        except Exception:
            items = []
    _cache[query] = items
    return items

def fetch(query, dest, offset=0, max_w=1280, quality=82):
    """query検索→offset番目をDL・横幅max_wに圧縮してdestへ保存。成功で{credit,req}、失敗でNone。"""
    items = search(query)
    if not items:
        return None
    item = items[offset % len(items)]
    try:
        raw = _get(item["img"], timeout=40)
        if Image:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            if im.width > max_w:
                im = im.resize((max_w, int(im.height * max_w / im.width)))
            im.save(dest, "JPEG", quality=quality, optimize=True)
        else:
            with open(dest, "wb") as f:
                f.write(raw)
        return {"credit": item.get("credit", ""), "req": bool(item.get("req"))}
    except Exception:
        return None

def source_name():
    return "Pexels" if PEXELS_KEY else "Openverse(CC0優先)"
