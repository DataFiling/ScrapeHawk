from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional
import asyncio
from functools import lru_cache
import hashlib
import time

app = FastAPI(
    title="Web Scraper API",
    description="A fast, lightweight web scraper for RapidAPI",
    version="1.0.0"
)

# Simple in-memory cache (consider Redis for production)
cache = {}
CACHE_TTL = 300  # 5 minutes

class ScrapeRequest(BaseModel):
    url: str
    selector: Optional[str] = None

class ScrapeResponse(BaseModel):
    url: str
    title: Optional[str]
    content: list[str]
    cached: bool = False

def get_cache_key(url: str, selector: str = "") -> str:
    return hashlib.md5(f"{url}:{selector}".encode()).hexdigest()

def get_cached(key: str) -> Optional[dict]:
    if key in cache:
        entry = cache[key]
        if time.time() - entry["timestamp"] < CACHE_TTL:
            return entry["data"]
        del cache[key]
    return None

def set_cache(key: str, data: dict):
    cache[key] = {"data": data, "timestamp": time.time()}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Scraper API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/scrape")
async def scrape_url(
    url: str = Query(..., description="URL to scrape"),
    selector: Optional[str] = Query(None, description="CSS selector to extract specific elements")
):
    """
    Scrape a webpage and extract content.
    
    - **url**: The webpage URL to scrape
    - **selector**: Optional CSS selector to target specific elements
    """
    cache_key = get_cache_key(url, selector or "")
    cached_data = get_cached(cache_key)
    
    if cached_data:
        cached_data["cached"] = True
        return JSONResponse(content=cached_data)
    
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract title
    title = soup.title.string if soup.title else None
    
    # Extract content based on selector or default to paragraphs
    if selector:
        elements = soup.select(selector)
        content = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
    else:
        # Default: extract all paragraph text
        paragraphs = soup.find_all("p")
        content = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    
    result = {
        "url": url,
        "title": title,
        "content": content,
        "cached": False
    }
    
    set_cache(cache_key, result)
    return JSONResponse(content=result)

@app.get("/scrape/links")
async def scrape_links(
    url: str = Query(..., description="URL to scrape links from"),
    external_only: bool = Query(False, description="Only return external links")
):
    """
    Extract all links from a webpage.
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    from urllib.parse import urlparse, urljoin
    base_domain = urlparse(url).netloc
    
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(url, href)
        link_domain = urlparse(full_url).netloc
        
        if external_only and link_domain == base_domain:
            continue
            
        links.append({
            "text": a.get_text(strip=True),
            "url": full_url,
            "external": link_domain != base_domain
        })
    
    return {
        "url": url,
        "total_links": len(links),
        "links": links
    }

@app.get("/scrape/meta")
async def scrape_metadata(url: str = Query(..., description="URL to extract metadata from")):
    """
    Extract metadata (title, description, OG tags, etc.) from a webpage.
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    metadata = {
        "url": url,
        "title": soup.title.string if soup.title else None,
        "description": None,
        "og": {},
        "twitter": {}
    }
    
    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        metadata["description"] = desc_tag.get("content")
    
    # Open Graph tags
    for tag in soup.find_all("meta", attrs={"property": lambda x: x and x.startswith("og:")}):
        key = tag["property"].replace("og:", "")
        metadata["og"][key] = tag.get("content")
    
    # Twitter cards
    for tag in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
        key = tag["name"].replace("twitter:", "")
        metadata["twitter"][key] = tag.get("content")
    
    return metadata

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
