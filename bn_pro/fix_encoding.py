#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复缓存文件的编码问题和null字节
此脚本会递归处理crypto_data目录中的所有JSON文件
"""

import os
import json
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_json_file(file_path):
    """
    修复JSON文件中的编码问题和null字节
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 是否修复成功
    """
    try:
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含null字节
            if '\x00' in content:
                logger.info(f"发现null字节: {file_path}")
                content = content.replace('\x00', '')
                fixed = True
            else:
                fixed = False
            
            # 尝试解析JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"JSON解析失败: {file_path}")
                return False
                
            # 如果需要修复或强制重写
            if fixed:
                # 创建备份
                backup_path = str(file_path) + '.bak'
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    logger.debug(f"已创建备份: {backup_path}")
                except Exception as e:
                    logger.warning(f"创建备份失败: {e}")
                
                # 写入修复后的内容
                try:
                    # 先写入临时文件
                    temp_path = str(file_path) + '.tmp'
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # 替换原文件
                    os.replace(temp_path, file_path)
                    logger.info(f"已修复: {file_path}")
                    return True
                except Exception as e:
                    logger.error(f"写入修复内容失败: {e}")
                    return False
            
            return False
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试二进制模式
            logger.warning(f"UTF-8解码失败，尝试二进制模式: {file_path}")
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 移除null字节
            if b'\x00' in content:
                logger.info(f"发现null字节(二进制): {file_path}")
                content = content.replace(b'\x00', b'')
                
                try:
                    # 尝试解码并解析
                    text_content = content.decode('utf-8', errors='ignore')
                    data = json.loads(text_content)
                    
                    # 创建备份
                    backup_path = str(file_path) + '.bak'
                    try:
                        import shutil
                        shutil.copy2(file_path, backup_path)
                    except Exception as e:
                        logger.warning(f"创建备份失败: {e}")
                    
                    # 写入修复后的内容
                    temp_path = str(file_path) + '.tmp'
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # 替换原文件
                    os.replace(temp_path, file_path)
                    logger.info(f"已修复(二进制): {file_path}")
                    return True
                except Exception as e:
                    logger.error(f"修复二进制内容失败: {e}")
                    return False
            else:
                logger.warning(f"无法处理的编码问题: {file_path}")
                return False
    except Exception as e:
        logger.error(f"处理文件时出错: {file_path} - {e}")
        return False

def process_directory(directory):
    """
    递归处理目录中的所有JSON文件
    
    Args:
        directory: 目录路径
    
    Returns:
        tuple: (处理文件数, 修复文件数)
    """
    processed = 0
    fixed = 0
    
    try:
        for item in Path(directory).rglob('*.json'):
            if item.is_file():
                processed += 1
                if fix_json_file(item):
                    fixed += 1
    except Exception as e:
        logger.error(f"处理目录时出错: {directory} - {e}")
    
    return processed, fixed

def main():
    """主函数"""
    # 主数据目录
    data_dir = 'crypto_data'
    
    if not os.path.exists(data_dir):
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    logger.info(f"开始处理目录: {data_dir}")
    processed, fixed = process_directory(data_dir)
    logger.info(f"处理完成: 共处理 {processed} 个文件，修复 {fixed} 个文件")

if __name__ == "__main__":
    main() 