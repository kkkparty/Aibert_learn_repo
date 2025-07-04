#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
import subprocess
import json
from binance_filter import filter_binance_coins

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # 设置命令行参数解析
        parser = argparse.ArgumentParser(description='菜价分析工具')
        parser.add_argument('--cache-only', action='store_true', help='仅使用缓存数据，不发送API请求')
        parser.add_argument('--limit', '--coins', type=int, default=100, help='限制分析的蔬菜数量，使用最受欢迎的前N种蔬菜')
        parser.add_argument('--sort-by', type=str, default='score', 
                           choices=['score', 'market_cap', 'price_change_24h', 'price_change_7d', 'rsi', 'volume_24h'], 
                           help='推荐结果排序方式: score(综合评分), market_cap(受欢迎度), price_change_24h(24h价格变化), price_change_7d(7d价格变化), rsi, volume_24h(交易量)')
        parser.add_argument('--no-save', action='store_true', help='不保存时间戳结果文件')
        parser.add_argument('--save-raw', '--save-all', action='store_true', help='保存所有获取的原始蔬菜数据')
        parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，减少输出信息')
        parser.add_argument('--email', type=str, help='发送结果到指定邮箱地址')
        parser.add_argument('--qq-email', type=str, help='发送结果到指定QQ邮箱地址(简化流程)')
        parser.add_argument('--no-obfuscation', action='store_true', help='不使用术语混淆，直接使用加密货币术语')
        parser.add_argument('--use-proxies', action='store_true', help='启用代理IP池，避免API请求限制')
        parser.add_argument('--no-short-term', action='store_true', help='不进行短线分析，仅分析长线数据')
        parser.add_argument('--binance-only', action='store_true', help='仅显示币安支持的币种')
        
        # 可选参数 - 默认值已经是优化配置 (这些参数在bn20617.py中不支持)
        parser.add_argument('--workers', type=int, default=6, help='并行处理的工作线程数量 (默认: 6)')
        parser.add_argument('--cache-expiry', type=int, default=24, help='缓存有效期(小时) (默认: 24)')
        parser.add_argument('--no-clean-cache', action='store_true', help='不清理过期缓存文件')
        parser.add_argument('--max-risk-level', type=str, default='medium', 
                           choices=['low', 'medium', 'high', 'very_high'], 
                           help='设置最大风险级别，高于此级别的币种不推荐 (默认: medium)')
        parser.add_argument('--risk-adjustment', type=float, default=0.8, 
                           help='风险调整系数 (0.5-2.0)，较低值会降低整体风险 (默认: 0.8)')
        parser.add_argument('--enhanced-analysis', action='store_true', default=True,
                           help='启用增强分析，提供更详细的技术指标 (默认开启)')
        parser.add_argument('--no-enhanced-analysis', action='store_true', 
                           help='禁用增强分析')
        
        args = parser.parse_args()
        
        # 输出默认优化配置
        print("\n菜价分析工具 - 已启用优化配置")
        print(f"系统默认配置:")
        print(f"- 并行处理: {args.workers} 个工作线程")
        print(f"- 缓存过期时间: {args.cache_expiry} 小时")
        print(f"- 自动清理缓存: {'已启用' if not args.no_clean_cache else '已禁用'}")
        print(f"- 最大风险级别: {args.max_risk_level} (风险调整系数: {args.risk_adjustment})")
        print(f"- 增强分析: {'已启用' if args.enhanced_analysis and not args.no_enhanced_analysis else '已禁用'}")
        if args.binance_only:
            print(f"- 币安过滤: 已启用 (只显示币安支持的币种)")
        print()
        
        # 调整标志 - 如果指定了--no-enhanced-analysis，则关闭enhanced_analysis
        if args.no_enhanced_analysis:
            args.enhanced_analysis = False
        
        # 准备临时输出文件，用于捕获bn20617.py的输出
        temp_output_file = "temp_output.json"
        if os.path.exists(temp_output_file):
            try:
                os.remove(temp_output_file)
            except:
                pass
        
        # 调用原始脚本的运行命令，传递所有参数
        import subprocess
        import sys
        
        # 从bn20617.py运行（这是备份版本，而不是有问题的bn2.py）
        cmd = ["python", "bn20617.py"]
        
        # 构建命令行参数 - 只包含bn20617.py支持的参数
        if args.cache_only:
            cmd.append("--cache-only")
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.sort_by:
            cmd.extend(["--sort-by", args.sort_by])
        if args.no_save:
            cmd.append("--no-save")
        else:
            # 确保保存结果，以便后处理
            cmd.append("--save-raw")
        if args.quiet:
            cmd.append("--quiet")
        if args.email:
            cmd.extend(["--email", args.email])
        if args.qq_email:
            cmd.extend(["--qq-email", args.qq_email])
        if args.no_obfuscation:
            cmd.append("--no-obfuscation")
        if args.use_proxies:
            cmd.append("--use-proxies")
        if args.no_short_term:
            cmd.append("--no-short-term")
        
        # 以下参数在打印时显示，但不传递给bn20617.py，因为该脚本不支持这些参数：
        # --workers, --cache-expiry, --no-clean-cache, --max-risk-level, --risk-adjustment, --enhanced-analysis
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        
        # 如果需要币安过滤，处理最新的输出文件
        if args.binance_only and result.returncode == 0:
            # 查找最新的推荐文件
            crypto_data_dir = "crypto_data"
            recommendation_files = [f for f in os.listdir(crypto_data_dir) if f.startswith("recommendations_") and f.endswith(".json")]
            
            if recommendation_files:
                # 按时间戳排序，获取最新的文件
                latest_file = sorted(recommendation_files)[-1]
                file_path = os.path.join(crypto_data_dir, latest_file)
                
                try:
                    # 读取推荐文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    
                    # 应用币安过滤
                    filtered_results = filter_binance_coins(results, True)
                    
                    # 保存过滤后的结果
                    filtered_file_path = file_path.replace('.json', '_binance_only.json')
                    with open(filtered_file_path, 'w', encoding='utf-8') as f:
                        json.dump(filtered_results, f, ensure_ascii=False, indent=2)
                    
                    print(f"\n已保存币安过滤后的结果到: {filtered_file_path}")
                except Exception as e:
                    logger.error(f"处理币安过滤时出错: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning("未找到推荐文件，无法应用币安过滤")
        
        sys.exit(result.returncode)
        
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
if __name__ == "__main__":
    main() 