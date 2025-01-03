import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import logging
from typing import List, Dict
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'kanji_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

# 要爬取的URL列表
URLS = [
    "https://kanji.jitenon.jp/cat/kyu10",
    "https://kanji.jitenon.jp/cat/kyu09",
    "https://kanji.jitenon.jp/cat/kyu08",
    "https://kanji.jitenon.jp/cat/kyu07",
    "https://kanji.jitenon.jp/cat/kyu06",
    "https://kanji.jitenon.jp/cat/kyu05",
    "https://kanji.jitenon.jp/cat/kyu04",
    "https://kanji.jitenon.jp/cat/kyu03",
    "https://kanji.jitenon.jp/cat/kyu02",
    "https://kanji.jitenon.jp/cat/kyu01",
    "https://kanji.jitenon.jp/cat/kyu02j",
    "https://kanji.jitenon.jp/cat/kyu01j",
    "https://kanji.jitenon.jp/cat/kyu0101j"
]

async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """异步获取页面内容"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                logging.error(f"Error fetching {url}: Status code {response.status}")
                return ""
    except Exception as e:
        logging.error(f"Exception while fetching {url}: {str(e)}")
        return ""

def extract_kanji_data(html: str, url: str) -> List[Dict]:
    """从HTML中提取汉字数据"""
    results = []
    try:
        # 从URL中提取level信息
        level = url.split('/')[-1]  # 获取URL最后的路径部分作为level
        
        soup = BeautifulSoup(html, 'html.parser')
        kanji_elements = soup.select("div.parts_box ul.search_parts li a")
        
        for element in kanji_elements:
            kanji = element.text.strip()
            kanji_url = element.get('href', '')
            if kanji and kanji_url:
                results.append({
                    "kanji": kanji,
                    "url": kanji_url,
                    "level": level  # 添加level属性
                })
                
        logging.info(f"Extracted {len(results)} kanji from {url}")
        return results
    except Exception as e:
        logging.error(f"Error parsing HTML from {url}: {str(e)}")
        return []

async def process_url_group(session: aiohttp.ClientSession, urls: List[str]) -> List[Dict]:
    """处理一组URL"""
    tasks = [fetch_page(session, url) for url in urls]
    pages = await asyncio.gather(*tasks)
    
    results = []
    for url, html in zip(urls, pages):
        if html:
            kanji_data = extract_kanji_data(html, url)
            results.extend(kanji_data)
    
    return results

async def main():
    """主函数"""
    all_results = []
    
    # 设置自定义headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 创建一个TCP连接池
    conn = aiohttp.TCPConnector(limit=10)
    
    async with aiohttp.ClientSession(headers=headers, connector=conn) as session:
        # 将URL列表分组，每组5个URL
        for i in range(0, len(URLS), 5):
            url_group = URLS[i:i+5]
            logging.info(f"Processing URLs {i+1} to {min(i+5, len(URLS))}")
            
            results = await process_url_group(session, url_group)
            all_results.extend(results)
            
            # 添加短暂延迟，避免请求过于频繁
            await asyncio.sleep(1)
    
    # 保存结果到JSON文件
    output_file = f'kanji_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving results to JSON: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting kanji scraper")
    asyncio.run(main())
    logging.info("Scraping completed")

