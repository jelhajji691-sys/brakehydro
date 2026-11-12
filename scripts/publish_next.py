#!/usr/bin/env python3
"""Publie le prochain article en attente dans drafts/.

Chaque brouillon est un fichier drafts/NN-slug.json (NN = ordre de publication).
Le script :
  1. génère blog/<slug>/index.html à partir de scripts/article-template.html
  2. ajoute la carte de l'article en tête de blog/index.html
  3. ajoute la carte dans le blog de la page d'accueil (index.html, version FR)
  4. ajoute l'URL dans sitemap.xml
  5. déplace le brouillon dans drafts/published/

Usage : python3 scripts/publish_next.py [--date AAAA-MM-JJ] [--dry-run]
"""
import argparse
import datetime as dt
import html
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts"
MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet",
        "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


def esc(s):
    return html.escape(s, quote=True)


def render(a, date):
    tpl = (ROOT / "scripts" / "article-template.html").read_text(encoding="utf-8")
    date_fr = f"{date.day} {MOIS[date.month - 1]} {date.year}"
    url = f"https://brakehydro.com/blog/{a['slug']}/"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": a["title"],
        "description": a["description"],
        "image": "https://brakehydro.com" + a["image"],
        "datePublished": date.isoformat(),
        "dateModified": date.isoformat(),
        "inLanguage": "fr",
        "mainEntityOfPage": url,
        "keywords": ", ".join(a["tags"]),
        "author": {"@type": "Organization", "name": "BrakeHydro", "url": "https://brakehydro.com/"},
        "publisher": {"@type": "Organization", "name": "BrakeHydro",
                      "logo": {"@type": "ImageObject", "url": "https://brakehydro.com/logo.png"}},
    }
    rep = {
        "{{META_TITLE}}": esc(a["meta_title"]),
        "{{DESCRIPTION}}": esc(a["description"]),
        "{{SLUG}}": a["slug"],
        "{{TITLE}}": esc(a["title"]),
        "{{TITLE_UPPER}}": esc(a["title"].upper()),
        "{{IMAGE}}": a["image"],
        "{{JSONLD}}": json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/"),
        "{{CATEGORY}}": esc(a["category"]),
        "{{TAGS_HTML}}": "".join(f'<span class="article-tag">{esc(t)}</span>' for t in a["tags"]),
        "{{DATE_FR}}": date_fr,
        "{{READ}}": str(a["read"]),
        "{{BODY}}": a["body"],
        "{{CTA_TITLE}}": esc(a["cta_title"]),
        "{{CTA_TEXT}}": esc(a["cta_text"]),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    assert "{{" not in tpl, "placeholder non remplacé"
    return tpl, date_fr


def blog_card(a, date_fr):
    tags = "\n".join(f'        <span class="card-tag">{esc(t)}</span>' for t in a["tags"][:3])
    return f'''
  <a href="/blog/{a['slug']}/" class="article-card">
    <div class="card-img">{esc(a['card_label'])}</div>
    <div class="card-body">
      <div class="card-tags">
{tags}
      </div>
      <div class="card-title">{esc(a['title'])}</div>
      <div class="card-desc">{esc(a['description'])}</div>
      <div class="card-meta">
        <span class="card-date">{date_fr}</span>
        <span class="card-read">{a['read']} min →</span>
      </div>
    </div>
  </a>
'''


def home_card(a, date_fr):
    tags = "".join(f'<span class="article-tag">{esc(t)}</span>' for t in a["tags"][:5])
    return (f'<div class="article-card" data-cat="{a["home_cat"]}" '
            f'onclick="location.href=\'/blog/{a["slug"]}/\'">'
            f'<div class="article-thumb"><img src="{a["image"]}" alt="{esc(a["title"])}" loading="lazy">'
            f'<span class="article-cat cat-{"commercial" if a["home_cat"] == "commercial" else "technique"}">{esc(a["category"])}</span></div>'
            f'<div class="article-body"><div class="article-meta"><span>📅 {date_fr}</span>'
            f'<span>⏱ {a["read"]} min de lecture</span></div>'
            f'<div class="article-title">{esc(a["title"])}</div>'
            f'<p class="article-excerpt">{esc(a["description"])}</p>'
            f'<div class="article-tags">{tags}</div>'
            f'<div class="read-more">Lire l\'article →</div></div></div>')


def insert_after(text, marker, snippet, label):
    i = text.find(marker)
    if i < 0:
        sys.exit(f"Repère introuvable dans {label} : {marker!r}")
    i += len(marker)
    return text[:i] + snippet + text[i:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()

    # Début des publications : crédits Netlify épuisés jusqu'au 3 décembre 2026
    if not args.date and date < dt.date(2026, 12, 7):
        print("Publications en pause jusqu'au 7 décembre 2026.")
        return

    queue = sorted(DRAFTS.glob("*.json"))
    if not queue:
        print("Aucun article en attente.")
        return
    draft = queue[0]
    a = json.loads(draft.read_text(encoding="utf-8"))
    out = ROOT / "blog" / a["slug"] / "index.html"
    if out.exists():
        sys.exit(f"{out} existe déjà")

    page, date_fr = render(a, date)

    blog_index = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
    blog_index = insert_after(blog_index, '<div class="blog-grid">\n', blog_card(a, date_fr), "blog/index.html")

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    home = insert_after(home, '<div id="cards-fr">', home_card(a, date_fr), "index.html")

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    entry = f"  <url><loc>https://brakehydro.com/blog/{a['slug']}/</loc><lastmod>{date.isoformat()}</lastmod><priority>0.6</priority></url>\n"
    sitemap = sitemap.replace("</urlset>", entry + "</urlset>")
    import re
    sitemap = re.sub(r"(<loc>https://brakehydro.com/blog/</loc><lastmod>)[0-9-]+", r"\g<1>" + date.isoformat(), sitemap)

    if args.dry_run:
        print(f"[dry-run] publierait {a['slug']} le {date_fr}")
        return
    out.parent.mkdir(parents=True)
    out.write_text(page, encoding="utf-8")
    (ROOT / "blog" / "index.html").write_text(blog_index, encoding="utf-8")
    (ROOT / "index.html").write_text(home, encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DRAFTS / "published").mkdir(exist_ok=True)
    shutil.move(str(draft), str(DRAFTS / "published" / draft.name))
    print(f"Publié : {a['title']} -> /blog/{a['slug']}/")


if __name__ == "__main__":
    main()
