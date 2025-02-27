#!/bin/bash
# 保存到项目根目录

# 第一阶段：数据抓取
echo "=== 执行数据抓取 ==="
python3 get_xhs_url_httpx.py \
    --url "$1" \
    --config config.json \
    --output ./output/raw_data.json

# 错误检查
if [ $? -ne 0 ]; then
    echo "错误：数据抓取失败，终止流程"
    exit 1
fi

# 第二阶段：数据清洗
echo "=== 执行文本清洗 ==="
python3 text_processor.py \
    --json-input ./output/raw_data.json \
    --output ./output/cleaned

echo "✅ 流程完成！最终结果在 ./output/cleaned 目录"