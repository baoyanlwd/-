# data_collector.py
import re
import json
from typing import List, Dict, Any
from pydantic import BaseModel

class CollectionConfig(BaseModel):
    """数据采集配置参数"""
    pattern: str  # 正则表达式模式
    output_field: str  # 输出字段名

class DataCollector:
    def __init__(self, configs: List[CollectionConfig]):
        """
        初始化数据采集器
        :param configs: 采集配置列表
        """
        self.configs = configs
        self.collected_data = {}

    async def collect_from_source(self, raw_data: str) -> None:
        """
        从原始数据中采集信息
        :param raw_data: 原始文本数据
        """
        for config in self.configs:
            matches = re.findall(config.pattern, raw_data)
            self.collected_data[config.output_field] = matches

    def get_results(self) -> Dict[str, Any]:
        """获取采集结果"""
        return {"collected_data": self.collected_data}

async def main(args: Dict) -> Dict:
    """
    异步数据采集入口
    示例配置参数:
    {
        "patterns": [
            {"pattern": r"\d{4}-\d{2}-\d{2}", "output_field": "dates"},
            {"pattern": r"#\w+", "output_field": "hashtags"}
        ]
    }
    """
    # 初始化配置
    configs = [CollectionConfig(**c) for c in args.get("patterns", [])]
    
    collector = DataCollector(configs)
    await collector.collect_from_source(args["raw_data"])
    
    return collector.get_results()