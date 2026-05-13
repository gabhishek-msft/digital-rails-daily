"""
Digital Rails Daily - Automated News Fetcher
Fetches daily news across 4 categories using NewsAPI and generates a static HTML site.
"""

import json
import os
import re
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "docs")

CATEGORIES = {
    "zkp-finance": {
        "title": "ZKP in Finance",
        "icon": "🛡️",
        "color": "#ffb900",
        "queries": [
            "zero knowledge proof finance",
            "ZKP blockchain settlement",
            "zk-rollup payments",
            "Nova folding scheme",
            "zero knowledge compliance banking",
        ],
    },
    "zkp-beyond": {
        "title": "ZKP Beyond Finance",
        "icon": "🔐",
        "color": "#e6a200",
        "queries": [
            "zero knowledge proof identity",
            "ZKP healthcare privacy",
            "zero knowledge supply chain",
            "zk-SNARK OR zk-STARK application",
            "zero knowledge voting OR credential",
        ],
    },
    "finserv": {
        "title": "Financial Institutions & Digital Assets",
        "icon": "🏦",
        "color": "#00a4ef",
        "queries": [
            "tokenization securities bank",
            "digital asset institutional",
            "blockchain settlement financial",
            "CBDC central bank digital currency",
            "stablecoin regulation",
            "DTCC OR LSEG OR JPMorgan blockchain",
        ],
    },
    "industries": {
        "title": "Blockchain Beyond Finance",
        "icon": "🏥",
        "color": "#00cc88",
        "queries": [
            "blockchain supply chain",
            "healthcare blockchain",
            "blockchain energy OR sustainability",
            "enterprise blockchain adoption",
        ],
    },
    "players": {
        "title": "Technology Players & Headwinds",
        "icon": "🚀",
        "color": "#7b68ee",
        "subcategories": {
            "startups": {
                "title": "Startups",
                "icon": "💡",
                "queries": [
                    "blockchain startup funding",
                    "crypto startup Series",
                    "web3 startup raise",
                    "ZKP startup",
                ],
            },
            "hyperscalers": {
                "title": "Hyperscalers",
                "icon": "☁️",
                "queries": [
                    "Microsoft Azure blockchain",
                    "AWS blockchain",
                    "Google Cloud web3",
                    "Oracle blockchain cloud",
                ],
            },
        },
    },
}


def fetch_news_api(query, page_size=5):
    """Fetch news from NewsAPI."""
    if not NEWS_API_KEY:
        return []

    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={quote(query)}&from={from_date}&sortBy=publishedAt"
        f"&pageSize={page_size}&language=en&apiKey={NEWS_API_KEY}"
    )

    try:
        req = Request(url, headers={"User-Agent": "DigitalRailsDaily/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("articles", [])
    except (URLError, json.JSONDecodeError) as e:
        print(f"  Warning: Failed to fetch '{query}': {e}")
        return []


def fetch_category_news(category_config):
    """Fetch and deduplicate news for a category."""
    articles = []
    seen_titles = set()

    queries = category_config.get("queries", [])
    for query in queries:
        results = fetch_news_api(query, page_size=3)
        for article in results:
            title = article.get("title", "")
            if title and title not in seen_titles and "[Removed]" not in title:
                seen_titles.add(title)
                articles.append(
                    {
                        "title": title,
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "published": article.get("publishedAt", ""),
                        "image": article.get("urlToImage", ""),
                    }
                )

    # Sort by published date
    articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    return articles[:8]


def fetch_all_news():
    """Fetch news for all categories."""
    news_data = {"date": datetime.now().strftime("%B %d, %Y"), "categories": {}}

    for cat_id, config in CATEGORIES.items():
        print(f"Fetching: {config['title']}...")

        if "subcategories" in config:
            news_data["categories"][cat_id] = {
                "title": config["title"],
                "icon": config["icon"],
                "color": config["color"],
                "subcategories": {},
            }
            for sub_id, sub_config in config["subcategories"].items():
                articles = fetch_category_news(sub_config)
                news_data["categories"][cat_id]["subcategories"][sub_id] = {
                    "title": sub_config["title"],
                    "icon": sub_config["icon"],
                    "articles": articles,
                }
                print(f"  {sub_config['title']}: {len(articles)} articles")
        else:
            articles = fetch_category_news(config)
            news_data["categories"][cat_id] = {
                "title": config["title"],
                "icon": config["icon"],
                "color": config["color"],
                "articles": articles,
            }
            print(f"  {len(articles)} articles")

    return news_data


def generate_html(news_data):
    """Generate the static HTML site with read/unread tracking and refresh."""

    def make_article_id(article):
        """Create a stable ID for an article based on title."""
        title = article.get('title', '')
        return title.replace(' ', '_')[:60]

    def article_card(article, color, idx):
        art_id = make_article_id(article)
        img_html = ""
        if article.get("image"):
            img_html = f'<img src="{article["image"]}" alt="" loading="lazy" onerror="this.style.display=\'none\'">'

        pub_date = ""
        if article.get("published"):
            try:
                dt = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
                pub_date = dt.strftime("%b %d, %H:%M")
            except ValueError:
                pub_date = ""

        return f"""
        <div class="card" data-article-id="{art_id}" onclick="toggleRead(this)">
            <div class="read-badge" title="Click card to mark as read/unread">&#x2713;</div>
            {img_html}
            <div class="card-body">
                <div class="card-meta">
                    <span class="source">{article.get('source', '')}</span>
                    <span class="date">{pub_date}</span>
                </div>
                <h3><a href="{article.get('url', '#')}" target="_blank" rel="noopener" onclick="event.stopPropagation()">{article.get('title', '')}</a></h3>
                <p>{article.get('description', '')[:150]}</p>
            </div>
        </div>"""

    sections_html = ""
    idx = 0
    for cat_id, cat_data in news_data["categories"].items():
        color = cat_data.get("color", "#00a4ef")
        sections_html += f"""
        <section class="category" id="{cat_id}">
            <h2><span class="cat-icon">{cat_data['icon']}</span> {cat_data['title']}</h2>
            <div class="accent" style="background:{color};"></div>"""

        if "subcategories" in cat_data:
            for sub_id, sub_data in cat_data["subcategories"].items():
                sections_html += f"""
            <h3 class="sub-heading">{sub_data['icon']} {sub_data['title']}</h3>
            <div class="cards-grid">"""
                for article in sub_data.get("articles", []):
                    sections_html += article_card(article, color, idx)
                    idx += 1
                sections_html += "</div>"
        else:
            sections_html += '<div class="cards-grid">'
            for article in cat_data.get("articles", []):
                sections_html += article_card(article, color, idx)
                idx += 1
            sections_html += "</div>"

        sections_html += "</section>"

    # Build nav links from categories
    nav_links = ""
    for cat_id, cat_data in news_data["categories"].items():
        nav_links += f'<a href="#{cat_id}">{cat_data["icon"]} {cat_data["title"]}</a>\n    '

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Digital Rails Daily</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#0a0f1a; color:#e0e8f0; line-height:1.6; }}
header {{ background:linear-gradient(135deg,#080d18,#13243b); padding:40px 20px; text-align:center; border-bottom:1px solid #1a3050; }}
header h1 {{ font-size:2.5rem; font-weight:700; }}
header h1 span {{ color:#00a4ef; }}
header .subtitle {{ color:#8899aa; margin-top:8px; font-size:1rem; }}
.toolbar {{ background:#0d1520; padding:12px 20px; display:flex; gap:12px; align-items:center; justify-content:center; flex-wrap:wrap; border-bottom:1px solid #1a3050; position:sticky; top:0; z-index:100; }}
.toolbar a {{ color:#8899aa; text-decoration:none; padding:6px 14px; border-radius:8px; font-size:0.85rem; transition:all 0.2s; }}
.toolbar a:hover {{ background:rgba(0,164,239,0.1); color:#00a4ef; }}
.toolbar .divider {{ width:1px; height:24px; background:#1a3050; }}
.btn {{ padding:8px 16px; border-radius:8px; border:1px solid #1a3050; background:#111927; color:#e0e8f0; font-size:0.85rem; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; gap:6px; }}
.btn:hover {{ border-color:#00a4ef; color:#00a4ef; }}
.btn.active {{ background:rgba(0,164,239,0.15); border-color:#00a4ef; color:#00a4ef; }}
.btn svg {{ width:14px; height:14px; }}
.refresh-spin {{ animation:spin 1s linear infinite; }}
@keyframes spin {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
.stats {{ font-size:0.8rem; color:#667788; padding:0 8px; }}
main {{ max-width:1400px; margin:0 auto; padding:30px 20px; }}
.category {{ margin-bottom:50px; }}
.category h2 {{ font-size:1.6rem; font-weight:700; margin-bottom:4px; }}
.cat-icon {{ font-size:1.4rem; }}
.accent {{ width:60px; height:3px; border-radius:2px; margin:8px 0 20px; }}
.sub-heading {{ font-size:1.1rem; color:#8899aa; margin:20px 0 12px; font-weight:600; }}
.cards-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:20px; margin-bottom:20px; }}
.card {{ background:#111927; border:1px solid #1a3050; border-radius:12px; overflow:hidden; transition:all 0.3s; cursor:pointer; position:relative; }}
.card:hover {{ transform:translateY(-2px); border-color:rgba(0,164,239,0.4); }}
.card.read {{ opacity:0.5; }}
.card.read .read-badge {{ opacity:1; background:#00cc88; }}
.read-badge {{ position:absolute; top:10px; right:10px; width:24px; height:24px; border-radius:50%; background:#334455; color:white; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; opacity:0.5; transition:all 0.2s; z-index:10; }}
.card:hover .read-badge {{ opacity:1; }}
.card img {{ width:100%; height:160px; object-fit:cover; }}
.card-body {{ padding:16px; }}
.card-meta {{ display:flex; justify-content:space-between; font-size:0.75rem; color:#667788; margin-bottom:8px; }}
.card h3 {{ font-size:0.95rem; font-weight:600; margin-bottom:8px; line-height:1.4; }}
.card h3 a {{ color:#e0e8f0; text-decoration:none; }}
.card h3 a:hover {{ color:#00a4ef; }}
.card p {{ font-size:0.82rem; color:#8899aa; line-height:1.5; }}
footer {{ text-align:center; padding:30px; color:#445566; font-size:0.8rem; border-top:1px solid #1a3050; }}
.empty {{ color:#556677; font-style:italic; padding:20px; text-align:center; }}
.hidden {{ display:none !important; }}
@media(max-width:768px) {{ header h1 {{ font-size:1.8rem; }} .cards-grid {{ grid-template-columns:1fr; }} .toolbar {{ gap:6px; }} }}
</style>
</head>
<body>
<header>
    <h1>Digital <span>Rails</span> Daily</h1>
    <div class="subtitle">Your daily digest of blockchain, ZKP, and digital asset news &mdash; {news_data['date']}</div>
</header>
<div class="toolbar">
    {nav_links}
    <span class="divider"></span>
    <button class="btn" id="btn-refresh" onclick="refreshFeed()" title="Refresh news feed">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
        Refresh
    </button>
    <button class="btn" id="btn-filter" onclick="toggleFilter()" title="Show only unread">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        Unread Only
    </button>
    <button class="btn" onclick="markAllRead()" title="Mark all as read">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        Mark All Read
    </button>
    <span class="stats" id="stats"></span>
</div>
<main>
{sections_html}
</main>
<footer>
    Digital Rails Daily &bull; Auto-generated via GitHub Actions &bull; Powered by NewsAPI
</footer>
<script>
// Read/Unread state management using localStorage
const STORAGE_KEY = 'digital-rails-read-articles';
let showUnreadOnly = false;

function getReadArticles() {{
    try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}'); }}
    catch {{ return {{}}; }}
}}

function saveReadArticles(data) {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}}

function toggleRead(card) {{
    const id = card.dataset.articleId;
    if (!id) return;
    const readMap = getReadArticles();
    if (readMap[id]) {{
        delete readMap[id];
        card.classList.remove('read');
    }} else {{
        readMap[id] = Date.now();
        card.classList.add('read');
    }}
    saveReadArticles(readMap);
    updateStats();
    applyFilter();
}}

function markAllRead() {{
    const readMap = getReadArticles();
    document.querySelectorAll('.card[data-article-id]').forEach(card => {{
        const id = card.dataset.articleId;
        readMap[id] = Date.now();
        card.classList.add('read');
    }});
    saveReadArticles(readMap);
    updateStats();
    applyFilter();
}}

function toggleFilter() {{
    showUnreadOnly = !showUnreadOnly;
    const btn = document.getElementById('btn-filter');
    btn.classList.toggle('active', showUnreadOnly);
    btn.innerHTML = showUnreadOnly
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Show All'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Unread Only';
    applyFilter();
}}

function applyFilter() {{
    document.querySelectorAll('.card[data-article-id]').forEach(card => {{
        if (showUnreadOnly && card.classList.contains('read')) {{
            card.classList.add('hidden');
        }} else {{
            card.classList.remove('hidden');
        }}
    }});
}}

function updateStats() {{
    const total = document.querySelectorAll('.card[data-article-id]').length;
    const read = document.querySelectorAll('.card.read').length;
    document.getElementById('stats').textContent = `${{read}}/${{total}} read`;
}}

function refreshFeed() {{
    const btn = document.getElementById('btn-refresh');
    const svg = btn.querySelector('svg');
    svg.classList.add('refresh-spin');
    btn.disabled = true;
    // Reload the page to pick up any new data
    setTimeout(() => location.reload(), 300);
}}

// Initialize: restore read state on page load
document.addEventListener('DOMContentLoaded', () => {{
    const readMap = getReadArticles();
    document.querySelectorAll('.card[data-article-id]').forEach(card => {{
        if (readMap[card.dataset.articleId]) {{
            card.classList.add('read');
        }}
    }});
    updateStats();
}});
</script>
</body>
</html>"""
    return html


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 50)
    print("Digital Rails Daily - Fetching News")
    print("=" * 50)

    news_data = fetch_all_news()

    # Save JSON for reference
    with open(os.path.join(OUTPUT_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(news_data, f, indent=2, ensure_ascii=False)

    # Generate HTML
    html = generate_html(news_data)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Site generated: {OUTPUT_DIR}/index.html")
    print(f"   Articles fetched: {sum(len(c.get('articles', [])) for c in news_data['categories'].values() if 'articles' in c)}")


if __name__ == "__main__":
    main()
