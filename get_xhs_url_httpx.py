# save as get_xhs_url_httpx.py
import argparse
import asyncio
import json
import re
import sys
import os
from pathlib import Path
from typing import Dict, List

import httpx

class XHSSpider:
    def __init__(self, config: Dict):
        self.retry_limit = int(config.get('retry', 3))
        self.timeout = int(config.get('timeout', 10))
        self.proxy = config.get('proxy')
        self.cookies = config.get('cookies', '')
        
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'),
            'Referer': 'https://www.xiaohongshu.com/',
            'Cookie': self.cookies
        }
        
        transport = None
        if self.proxy:
            transport = httpx.Proxy(self.proxy)
        
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            transport=transport
        )

    async def _fetch_with_retry(self, url: str) -> httpx.Response:
        for attempt in range(self.retry_limit):
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    return response
                await asyncio.sleep(pow(2, attempt))
            except (httpx.RequestError, asyncio.TimeoutError):
                if attempt == self.retry_limit - 1:
                    raise
                await asyncio.sleep(pow(2, attempt))
        return None

    def _parse_note_data(self, html: str) -> Dict:
        result = {
            "user_id": "", "note_id": "", "note_title": "",
            "note_desc": "", "liked": "0", "collected": "0",
            "comments": "0", "shared": "0", "cnt": 0,
            "urls": [], "note_text": ""
        }

        result['urls'] = re.findall(r'<meta\s+name="og:image"[^>]+content="([^"]+)"', html)
        result['cnt'] = len(result['urls'])

        json_match = re.search(r'<script>window.__INITIAL_STATE__=(.*?)</script>', html)
        if json_match:
            try:
                json_str = json_match.group(1).replace('undefined', 'null')
                json_data = json.loads(json_str)
                
                note_id = json_data.get('note', {}).get('firstNoteId', '')
                note_detail = json_data.get('note', {}).get('noteDetailMap', {}).get(note_id, {}).get('note', {})

                note_title = note_detail.get('title', '')
                if isinstance(note_title, tuple):
                    note_title = note_title[0]
                note_title = note_title.replace('\n', '<br>')

                desc = note_detail.get('desc', '')
                desc = '<br>'.join([p.strip() for p in re.split(r'\r\n|\n|\r|\b|<br\s*/?\s*>', desc, flags=re.IGNORECASE) if p.strip()])

                result.update({
                    "user_id": note_detail.get('user', {}).get('userId', ''),
                    "note_id": note_detail.get('noteId', ''),
                    "note_title": note_title,
                    "note_desc": desc,
                    "liked": str(note_detail.get('interactInfo', {}).get('likedCount', 0)),
                    "collected": str(note_detail.get('interactInfo', {}).get('collectedCount', 0)),
                    "comments": str(note_detail.get('interactInfo', {}).get('commentCount', 0)),
                    "shared": str(note_detail.get('interactInfo', {}).get('shareCount', 0)),
                    "note_text": f"{note_title}<br>{desc}"
                })
            except Exception as e:
                sys.stderr.write(f"JSON解析异常: {str(e)}\n")
                result['user_id'] = f"ERROR: {str(e)}"
        return result

    async def run(self, url: str) -> Dict:
        if not url.startswith('https://www.xiaohongshu.com'):
            return {"user_id": "ERROR: Invalid URL"}
        
        try:
            response = await self._fetch_with_retry(url)
            if not response or response.status_code != 200:
                return {"user_id": f"ERROR: 请求失败 {getattr(response, 'status_code', '未知')}"}
            return self._parse_note_data(response.text)
        except Exception as e:
            return {
                "user_id": f"ERROR: {str(e)}",
                "note_id": "Status: 请求异常"
            }

async def async_main(args):
    with open(args.config) as f:
        config = json.load(f)
    
    spider = XHSSpider(config)
    try:
        result = await spider.run(args.url)
    finally:
        await spider.client.aclose()
    
    # ========== 新增目录创建逻辑 ==========
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # ====================================
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def main():
    parser = argparse.ArgumentParser(description='小红书笔记抓取工具 (httpx版)')
    parser.add_argument('--url', required=True)
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--output', required=True)
    
    args = parser.parse_args()
    asyncio.run(async_main(args))

if __name__ == "__main__":
    main()