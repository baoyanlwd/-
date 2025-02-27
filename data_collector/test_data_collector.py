# test_data_collector.py（简化版）
import asyncio
from data_collector import main

async def test():
    result = await main({
        "raw_data": "2024-08-20 #test",
        "patterns": [
            {"pattern": "\\d{4}-\\d{2}-\\d{2}", "output_field": "dates"},
            {"pattern": "#\\w+", "output_field": "tags"}
        ]
    })
    print(result)  # 应输出 {'collected_data': {'dates': ['2024-08-20'], 'tags': ['#test']}}

if __name__ == "__main__":
    asyncio.run(test())