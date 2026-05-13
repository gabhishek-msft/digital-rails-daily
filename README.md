# Digital Rails Daily 📰

A fully automated daily news aggregator covering blockchain, zero-knowledge proofs, digital assets, and institutional finance — published as a static site on GitHub Pages.

## Categories

| Section | Coverage |
|---------|----------|
| 🛡️ **Zero-Knowledge Proofs** | ZKP research, Nova, zk-SNARKs/STARKs, privacy tech |
| 🏦 **Financial Institutions** | Tokenization, CBDC, stablecoins, institutional blockchain adoption |
| 🏥 **Beyond Finance** | Supply chain, healthcare, energy, enterprise blockchain |
| 🚀 **Tech Players** | Startups (funding, launches) and Hyperscalers (Azure, AWS, GCP) |

## How It Works

1. **GitHub Actions** runs daily at 6:00 AM UTC
2. **Python script** fetches latest news via [NewsAPI](https://newsapi.org)
3. **Static HTML** is generated and committed to `docs/`
4. **GitHub Pages** serves the site automatically

## Setup

1. Fork/clone this repo
2. Get a free API key from [newsapi.org](https://newsapi.org/register)
3. Add it as a repository secret: `Settings → Secrets → NEWS_API_KEY`
4. Enable GitHub Pages: `Settings → Pages → Source: Deploy from branch → /docs`
5. Trigger the workflow manually or wait for the daily schedule

## Local Development

```bash
# Set your API key
export NEWS_API_KEY=your_key_here

# Run the fetcher
python src/fetch_news.py

# Open the site
open docs/index.html
```

## Customization

Edit `src/fetch_news.py` to:
- Add/remove news categories
- Change search queries
- Adjust article count per category
- Modify the HTML template/styling

## Live Site

📍 `https://gabhishek_microsoft.github.io/digital-rails-daily/`
