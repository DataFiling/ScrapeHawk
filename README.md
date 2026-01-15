# ScrapeHawk

A fast, lightweight web scraping API built with FastAPI, designed for deployment on Railway and integration with RapidAPI.

## Features

- **`/scrape`** - Extract text content from any webpage with optional CSS selectors
- **`/scrape/links`** - Extract all links from a page (with external-only filter)
- **`/scrape/meta`** - Extract metadata, Open Graph, and Twitter card info
- Built-in caching (5-minute TTL)
- Async requests for fast performance
- Auto-generated OpenAPI docs

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Deploy to Railway

1. Push this code to a GitHub repository

2. Go to [Railway](https://railway.app) and create a new project

3. Select "Deploy from GitHub repo" and choose your repository

4. Railway will auto-detect the Python app and deploy it

5. Once deployed, go to Settings → Networking → Generate Domain

6. Your API is now live at `https://your-app.up.railway.app`

## Connect to RapidAPI

1. Go to [RapidAPI Provider Dashboard](https://rapidapi.com/provider)

2. Click "Add New API"

3. Fill in the details:
   - **Name**: ScrapeHawk
   - **Base URL**: `https://your-app.up.railway.app`

4. Add your endpoints:

   ```
   GET /scrape
   Parameters:
     - url (required): URL to scrape
     - selector (optional): CSS selector
   
   GET /scrape/links
   Parameters:
     - url (required): URL to scrape
     - external_only (optional): boolean
   
   GET /scrape/meta
   Parameters:
     - url (required): URL to scrape
   ```

5. Set pricing, documentation, and publish!

## API Endpoints

### GET /scrape
Scrape text content from a webpage.

```bash
curl "https://your-app.up.railway.app/scrape?url=https://example.com"

# With CSS selector
curl "https://your-app.up.railway.app/scrape?url=https://example.com&selector=h1"
```

### GET /scrape/links
Extract all links from a webpage.

```bash
curl "https://your-app.up.railway.app/scrape/links?url=https://example.com"

# External links only
curl "https://your-app.up.railway.app/scrape/links?url=https://example.com&external_only=true"
```

### GET /scrape/meta
Extract metadata from a webpage.

```bash
curl "https://your-app.up.railway.app/scrape/meta?url=https://example.com"
```

## Environment Variables (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port (set by Railway) | 8000 |
| `CACHE_TTL` | Cache duration in seconds | 300 |

## Tips for Production

1. **Add Redis caching** - Replace the in-memory cache with Redis for persistence across restarts
2. **Add rate limiting** - Use `slowapi` to prevent abuse
3. **Add authentication** - RapidAPI handles this, but you can add API key validation
4. **Monitor usage** - Railway provides built-in metrics

## License

MIT
