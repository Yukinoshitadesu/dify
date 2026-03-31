import asyncio
import json
from fastapi import FastAPI, HTTPException, Form
from typing import Optional
from playwright.async_api import async_playwright
import uvicorn

app = FastAPI(title="Threads Playwright Scraper Service")

# --- 您的預設 Threads Session Cookies ---
THREADS_COOKIES = [
    {"domain": ".threads.com", "expiry": 1809392408, "httpOnly": False, "name": "csrftoken", "path": "/", "sameSite": "Lax", "secure": True, "value": "EdU491A4Z38rf4l0slWVhKKWaq0jdn6J"},
    {"domain": ".threads.com", "expiry": 1782608408, "httpOnly": False, "name": "ds_user_id", "path": "/", "sameSite": "None", "secure": True, "value": "75269686564"},
    {"domain": ".threads.com", "expiry": 1803534352, "httpOnly": False, "name": "ig_did", "path": "/", "sameSite": "Lax", "secure": True, "value": "C5CC11D1-AF3F-44BB-905B-0A5F83309E98"},
    {"domain": ".threads.com", "expiry": 1806558453, "httpOnly": False, "name": "mid", "path": "/", "sameSite": "Lax", "secure": True, "value": "aZ6M7gALAAHqbrYF7aCGffz9g-Ki"},
    {"domain": ".threads.com", "httpOnly": True, "name": "rur", "path": "/", "sameSite": "Lax", "secure": True, "value": "\"HIL\\05475269686564\\0541806368422:01fe9fe18f73c84abbdd710b0270bfbc5f5274fdc5e6d8c43932d5838d9fd050e4667e8a\""},
    {"domain": ".threads.com", "expiry": 1806368406, "httpOnly": True, "name": "sessionid", "path": "/", "sameSite": "Lax", "secure": True, "value": "75269686564%3Aqp1dkFucBFlaqr%3A15%3AAYj28t8WZDBRimb0JTULyM9WvZqnCfnupaeySnYK-Q"}
]

async def scrape_threads(keyword: str, max_posts: int = 10, custom_cookies: list = None):
    async with async_playwright() as p:
        # 使用隨機 User Agent 減少被阻擋機率
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        # 優先使用傳入的自訂 Cookies，否則使用預設 Cookies
        cookies_to_use = custom_cookies if custom_cookies else THREADS_COOKIES
        await context.add_cookies(cookies_to_use)
        
        page = await context.new_page()
        search_url = f"https://www.threads.com/search?q={keyword}"
        
        print(f"[*] 正在跳轉至: {search_url}")
        await page.goto(search_url, wait_until="networkidle")
        
        # 診斷 1: 檢查是否被重新導向到登入頁面
        current_url = page.url
        print(f"[*] 當前網址: {current_url}")
        
        if "login" in current_url:
            print("[!] 警告：被重新導向到登入頁面，可能是 Cookie 已失效")
            await browser.close()
            return [{"error": "Login required - Cookies might be expired"}]

        # 診斷 2: 等待貼文容器
        try:
            # Threads 的貼文通常在特定測試 ID 或類名的 div 中
            await page.wait_for_selector('div[data-testid="search_results_list"]', timeout=10000)
            print("[+] 找到貼文列表容器")
        except:
            print("[!] 找不到貼文列表容器，嘗試通用抓取...")
            # 存下一張截圖供除錯 (在 Container 內)
            await page.screenshot(path="debug_screenshot.png")

        # 抓取貼文文本與網址 (直接透過 JS 深入提取，放寬條件並抓取相關連結)
        # Threads 通常會把使用者輸入的文字加上 dir="auto"
        posts_data = await page.evaluate('''() => {
            const elements = document.querySelectorAll('[dir="auto"]');
            const results = [];
            
            elements.forEach(el => {
                const text = el.innerText;
                // 放寬限制，只要有字就抓
                if (!text || text.trim().length < 2) return;
                
                // 嘗試抓取這個區塊「附近」(父層) 的所有連結
                let parent = el.parentElement;
                let links = [];
                // 往祖父層尋找 4 層內的所有超連結
                for(let i=0; i<4 && parent; i++) {
                    parent.querySelectorAll('a').forEach(a => {
                        if (a.href && !links.includes(a.href)) {
                            links.push(a.href);
                        }
                    });
                    parent = parent.parentElement;
                }
                
                // 優先挑出包含 '/post/' 的連結當作該貼文的主要連結
                let mainUrl = links.find(l => l.includes('/post/')) || (links.length > 0 ? links[0] : "");
                
                results.push({
                    content: text.trim(),
                    url: mainUrl,
                    all_links: links  // 把附帶的所有連結都丟給AI判讀
                });
            });
            return results;
        }''')
        
        posts = []
        seen_content = set()
        for item in posts_data:
            text = item["content"]
            # 簡單過濾完全重複的內容，但不再強力排除
            if text not in seen_content:
                seen_content.add(text)
                posts.append(item)
                if len(posts) >= max_posts * 2: # 稍微多抓一點讓AI過濾
                    break
        
        print(f"[+] 抓取完成，共 {len(posts)} 則資料 (含連結)")
        await browser.close()
        return posts



@app.post("/scrape")
async def run_scrape(
    keyword: str = Form(...),
    limit: int = Form(10),
    cookies_str: Optional[str] = Form(None)
):
    if not keyword:
        raise HTTPException(status_code=400, detail="Missing keyword")
    
    custom_cookies = None
    if cookies_str:
        try:
            custom_cookies = json.loads(cookies_str)
            if not isinstance(custom_cookies, list):
                raise ValueError("Cookies must be a JSON array")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cookies_str format: {e}")

    try:
        results = await scrape_threads(keyword, limit, custom_cookies)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("--- Threads Playwright Scraper 服務已啟動 ---")
    print("API 網址: http://127.0.0.1:8000/scrape (POST)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
