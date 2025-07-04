#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_file(file_path):
    """
    修复文件编码问题
    
    参数:
    file_path -- 要修复的文件路径
    
    返回:
    bool -- 是否成功修复
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复文件: {file_path}")
    
    # 创建备份目录
    backup_dir = "backup_files"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 备份原文件
    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    shutil.copy2(file_path, backup_path)
    logger.info(f"已备份原始文件到: {backup_path}")
    
    try:
        # 尝试以二进制模式读取文件
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 检查并移除null bytes
        if b'\x00' in content:
            logger.info(f"文件 {file_path} 包含null bytes，正在移除...")
            content = content.replace(b'\x00', b'')
        
        # 尝试将内容解码为UTF-8，失败时使用Latin-1（兼容所有字节值）
        try:
            text = content.decode('utf-8')
            logger.info(f"成功使用UTF-8解码")
        except UnicodeDecodeError:
            text = content.decode('latin-1')
            logger.info(f"使用Latin-1解码（兼容模式）")
        
        # 如果文件是Python文件，检查是否存在有效Python代码
        if file_path.endswith('.py'):
            if '#!/usr/bin/env python' not in text and 'import ' not in text:
                logger.error(f"文件 {file_path} 可能已严重损坏，内容不是有效的Python代码")
                logger.info(f"请考虑从备份或其他来源重新创建此文件")
                return False
        
        # 以UTF-8编码写回文件
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        
        logger.info(f"文件 {file_path} 修复完成")
        return True
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数，处理命令行参数"""
    if len(sys.argv) > 1:
        # 处理指定的文件
        return fix_file(sys.argv[1])
    else:
        # 扫描当前目录中的所有Python文件
        success_count = 0
        fail_count = 0
        
        logger.info("扫描当前目录中的所有Python文件...")
        for root, _, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if fix_file(file_path):
                        success_count += 1
                    else:
                        fail_count += 1
        
        logger.info(f"扫描完成。成功修复: {success_count}，修复失败: {fail_count}")
        return success_count > 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 