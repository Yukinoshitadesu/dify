import asyncio
import json
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
import uvicorn

app = FastAPI(title="Threads Playwright Scraper Service")

# --- 您的 Threads Session Cookies (由您提供) ---
THREADS_COOKIES = [
    {"domain": ".threads.com", "expiry": 1809392408, "httpOnly": False, "name": "csrftoken", "path": "/", "sameSite": "Lax", "secure": True, "value": "EdU491A4Z38rf4l0slWVhKKWaq0jdn6J"},
    {"domain": ".threads.com", "expiry": 1782608408, "httpOnly": False, "name": "ds_user_id", "path": "/", "sameSite": "None", "secure": True, "value": "75269686564"},
    {"domain": ".threads.com", "expiry": 1803534352, "httpOnly": False, "name": "ig_did", "path": "/", "sameSite": "Lax", "secure": True, "value": "C5CC11D1-AF3F-44BB-905B-0A5F83309E98"},
    {"domain": ".threads.com", "expiry": 1806558453, "httpOnly": False, "name": "mid", "path": "/", "sameSite": "Lax", "secure": True, "value": "aZ6M7gALAAHqbrYF7aCGffz9g-Ki"},
    {"domain": ".threads.com", "httpOnly": True, "name": "rur", "path": "/", "sameSite": "Lax", "secure": True, "value": "\"HIL\\05475269686564\\0541806368422:01fe9fe18f73c84abbdd710b0270bfbc5f5274fdc5e6d8c43932d5838d9fd050e4667e8a\""},
    {"domain": ".threads.com", "expiry": 1806368406, "httpOnly": True, "name": "sessionid", "path": "/", "sameSite": "Lax", "secure": True, "value": "75269686564%3Aqp1dkFucBFlaqr%3A15%3AAYj28t8WZDBRimb0JTULyM9WvZqnCfnupaeySnYK-Q"}
]

async def scrape_threads(keyword: str, max_posts: int = 10):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # 建議正式環境用 True
        context = await browser.new_context()
        
        # 注入 Cookies
        await context.add_cookies(THREADS_COOKIES)
        
        page = await context.new_page()
        search_url = f"https://www.threads.net/search?q={keyword}"
        
        print(f"[*] 正在爬取: {search_url}")
        await page.goto(search_url)
        
        # 等待貼文加載 (Threads 結構較複雜，這裡使用常見的選擇器)
        try:
            await page.wait_for_selector('div[style*="flex-direction: column"]', timeout=15000)
        except:
            print("[!] 等待超時，可能未成功登入或頁面結構改變")
            
        # 簡單抓取貼文文本內容
        posts = []
        post_elements = await page.query_selector_all('div[dir="auto"]')
        
        for el in post_elements[:max_posts * 3]: # 多抓一點再過濾
            text = await el.inner_text()
            if text and len(text) > 10:
                posts.append({"content": text})
                if len(posts) >= max_posts:
                    break
        
        await browser.close()
        return posts

@app.get("/scrape")
async def run_scrape(keyword: str, limit: int = 10):
    if not keyword:
        raise HTTPException(status_code=400, detail="Missing keyword")
    
    try:
        results = await scrape_threads(keyword, limit)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("--- Threads Playwright Scraper 服務已啟動 ---")
    print("預設網址: http://127.0.0.1:8000/scrape?keyword=你的關鍵字")
    uvicorn.run(app, host="0.0.0.0", port=8000)
