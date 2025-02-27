# text_processor.py（最终稳定版）
import re
import argparse
import logging
import json  # 新增导入
from pathlib import Path
from typing import Tuple

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def clean_content(text: str) -> Tuple[str, str, str]:
    try:
        # 关键修改1：严格处理换行符
        paragraphs = [
            p.strip()
            for p in re.split(r"\r\n|\n|\r|<br>", text)
            if p.strip() and not p.isspace()
        ]
        
        full_text = "\n".join(paragraphs)
        
        # 关键修改2：精确匹配模式
        cleaned_text = re.sub(
            r'^(.*?关注.*?关注[\s\n]*)|([\s\n]*\d{4}-\d{1,2}-\d{1,2}.*条评论.*$)',
            '', 
            full_text,
            flags=re.DOTALL | re.MULTILINE
        )
        
        # 关键修改3：彻底清洗换行符
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text).strip()
        
        if (hash_pos := cleaned_text.find('#')) != -1:
            main_part = cleaned_text[:hash_pos].strip()
            tags_part = cleaned_text[hash_pos:].strip().replace('\n', '')
            return (main_part, tags_part, cleaned_text)
            
        return cleaned_text, "", cleaned_text
        
    except Exception as e:
        logging.error(f"文本处理异常: {str(e)}")
        raise

def process_file(input_path: Path, output_dir: Path, save_intermediate: bool = False):
    try:
        content = input_path.read_text(encoding='utf-8')
        logging.info(f"成功读取文件: {input_path}")
        
        main_text, tags, intermediate = clean_content(content)
        
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"processed_{input_path.name}"
        output_path.write_text(f"【清理后文本】\n{main_text}\n\n【标签】\n{tags}", encoding='utf-8')
        logging.info(f"结果已保存至: {output_path}")
        
        if save_intermediate:
            (output_dir / f"intermediate_{input_path.name}").write_text(intermediate, encoding='utf-8')
    except Exception as e:
        logging.error(f"文件处理失败: {input_path} - {str(e)}")
        raise

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='视频文本提取工具')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--json-input', type=str, help='JSON输入文件路径')
    group.add_argument('--text-input', type=str, help='直接输入文本内容')
    
    parser.add_argument('-o', '--output', type=str, default='./output', 
                       help='输出目录路径，默认为./output')
    parser.add_argument('-i', '--intermediate', action='store_true',
                       help='保存中间处理结果')
    
    args = parser.parse_args()
    setup_logger()
    
    try:
        output_dir = Path(args.output)
        if args.json_input:
            json_path = Path(args.json_input)
            if not json_path.exists():
                raise FileNotFoundError(f"JSON文件不存在: {args.json_input}")
                
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            raw_text = data.get('note_text', '')
            result, tags, _ = clean_content(raw_text)
            
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"cleaned_{json_path.stem}.txt"
            output_path.write_text(f"【清理后文本】\n{result}\n\n【标签】\n{tags}", encoding='utf-8')
            print(f"清洗结果已保存至: {output_path}")
            
        elif args.text_input:
            result, tags, _ = clean_content(args.text_input)
            print(f"清理后文本:\n{result}\n\n提取标签:\n{tags}")
            
    except Exception as e:
        logging.error(f"运行失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()