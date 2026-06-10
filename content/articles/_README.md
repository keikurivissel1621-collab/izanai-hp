# ブログ記事の書き方（IZANAI Blog）

このフォルダに **Markdownファイル（`.md`）を1記事＝1ファイル**で置き、生成コマンドを実行すると、
SEO対応の記事ページ・一覧ページ・サイトマップが自動生成されます。

## 1. 記事ファイルを作る

`content/articles/` に `NNNN-slug.md` の形式で作成（番号は管理用、URLには使われません）。

### frontmatter（先頭の `---` で囲む部分）

```markdown
---
title: 記事タイトル（H1になる。SEOで最重要。32〜40字目安）
description: 検索結果に出る説明文（100〜120字。キーワードを含める）
slug: english-url-slug          # 記事URL → /blog/english-url-slug/
date: 2026-06-10                # 公開日（YYYY-MM-DD）
updated: 2026-06-10             # 更新日（任意。省略時はdate）
category: AIセキュリティ          # カテゴリ（チップ表示）
tags: [AI導入, セキュリティ]      # タグ（任意）
thumbnail: /assets/hero/xxx.jpg # サムネ画像（任意。無ければグラデ表示）
draft: false                    # true にすると公開されない（下書き）
---
```

### 本文（SEOに強い見出し階層を必ず守る）

| 記法 | 役割 | 使い方 |
|---|---|---|
| `#` | H1 | **使わない**（タイトルが自動でH1になる） |
| `##` | 大見出し | 章の見出し。目次に載る |
| `###` | 中見出し | 大見出しの中の小項目。目次に載る |
| `####` | 章見出し | さらに細かい補足 |

- 太字 `**重要**`（ゴールドのマーカーが付く）／ 強調 `*ここ*`（ティール色）
- 箇条書き `- ` / 番号 `1. ` / 引用 `> ` / 表（Markdownテーブル）/ 画像 `![alt](/path.jpg)` 対応
- 内部リンクを積極的に：例 `[Claude Code実装支援](/claude-code.html)`

## 2. 生成する

```bash
python scripts/build_blog.py
```

→ 以下が自動生成・更新されます。
- `blog/<slug>/index.html`（記事ページ。CTA・目次・構造化データ・OGP自動付与）
- `blog/index.html`（記事一覧）
- `sitemap.xml` / `robots.txt`

## 3. 公開する（Netlify）

リポジトリをpushすればNetlifyが自動公開（または `npx netlify-cli deploy --prod`）。

## 自動で入るもの（書かなくてよい）
- ヘッダー／フッター（メインサイトと統一）
- 目次（H2/H3から自動生成・スクロール連動）
- CTA：記事中間・記事末（公式LINE）・「ホーム/会社を知る/Claude Code」3択・執筆者ボックス
- SEO：title / description / canonical / OGP / Twitter Card / 構造化データ(BlogPosting + Breadcrumb)
- 関連記事（最新3本）／読了時間
