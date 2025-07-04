#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    此文件仅用于向continuous_binance_crypto.py转发调用，
    以保持与批处理文件的兼容性
    """
    logger.info("使用兼容性包装器 - 转发到 continuous_binance_crypto.py")
    
    try:
        # 构建命令行参数
        args = sys.argv[1:]
        cmd_args = ' '.join(args)
        
        # 导入并调用主脚本
        try:
            from continuous_binance_crypto import main as continuous_main
            logger.info("成功导入主模块，直接调用...")
            continuous_main()
        except ImportError:
            # 如果导入失败，尝试作为独立进程运行
            logger.warning("导入主模块失败，尝试作为独立进程运行...")
            os.system(f"python continuous_binance_crypto.py {cmd_args}")
    
    except Exception as e:
        logger.error(f"转发时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 