#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表格解析工具：将分割后的table文件解析为CSV格式
检测并处理极端情况（如数据不成对的情况）
"""

from pathlib import Path
import csv
import re

def parse_table_content(lines):
    """解析表格内容，返回(alias, name)对列表"""
    aliases_names = []
    
    # 跳过表头，找到 P11 P10 (完整或简化格式) 之后的内容
    start_idx = -1
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # 支持两种格式: "P11 P10 P93 P856PCD" 或 "P11 P10"
        if line_stripped == "P11 P10" or line_stripped == "P11 P10 P93 P856PCD":
            start_idx = i + 2  # 跳过表头行和下一个 "---"
            break
    
    if start_idx == -1:
        return aliases_names, "未找到 P11 P10 表头"
    
    # 提取数据行（排除 "---" 和 "X"），遇到页面标记时停止
    data_lines = []
    stop_keywords = ["Pure Component", "Databanks", "===== PAGE", "Physical Property Data", "Available in Databank"]
    
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        
        # 检查是否遇到停止关键词
        if any(keyword in line for keyword in stop_keywords):
            break
            
        if line and line != "---" and line != "X":
            data_lines.append(line)
    
    # 检查数据行数是否为偶数
    if len(data_lines) % 2 != 0:
        return aliases_names, f"数据行数为奇数 ({len(data_lines)} 行)，应该是偶数（alias-name配对）"
    
    # 按照 alias, name 配对处理
    for i in range(0, len(data_lines), 2):
        alias = data_lines[i].strip().upper()
        name = data_lines[i + 1].strip().upper()
        
        # 基本验证
        if alias and name:
            aliases_names.append((alias, name))
    
    return aliases_names, None

def detect_extreme_cases(table_file):
    """检测极端情况的表格"""
    
    # 已知的极端情况表格
    extreme_cases = {
        "table_72.txt": "GLYC数据格式异常"
    }
    
    return table_file.name in extreme_cases, extreme_cases.get(table_file.name, "")

def process_single_table(table_file, output_dir):
    """处理单个表格文件"""
    
    print(f"📋 处理表格: {table_file.name}")
    
    # 检测极端情况
    is_extreme, extreme_reason = detect_extreme_cases(table_file)
    if is_extreme:
        print(f"⚠️  跳过极端情况: {extreme_reason}")
        return False, 0, extreme_reason
    
    # 读取文件
    try:
        with open(table_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        error_msg = f"读取文件失败: {e}"
        print(f"❌ {error_msg}")
        return False, 0, error_msg
    
    # 解析内容
    aliases_names, error = parse_table_content(lines)
    
    if error:
        print(f"❌ 解析错误: {error}")
        return False, 0, error
    
    if not aliases_names:
        print(f"⚠️  没有找到有效的 alias-name 配对")
        return False, 0, "没有有效数据"
    
    # 生成输出文件
    csv_file = output_dir / f"{table_file.stem}.csv"
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['databank', 'alias_or_code', 'registered_name'])
            
            for alias, name in aliases_names:
                writer.writerow(['PURE11', alias, name])
        
        print(f"✅ 成功输出: {len(aliases_names)} 对 → {csv_file.name}")
        return True, len(aliases_names), None
        
    except Exception as e:
        error_msg = f"写入CSV失败: {e}"
        print(f"❌ {error_msg}")
        return False, 0, error_msg

def process_all_tables(tables_dir, output_dir):
    """处理所有表格文件"""
    
    print("🔧 化合物表格解析工具")
    print("=" * 60)
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    # 获取所有表格文件
    table_files = sorted(tables_dir.glob("table_*.txt"))
    
    if not table_files:
        print(f"❌ 没有找到表格文件在 {tables_dir}")
        return
    
    print(f"📁 输入目录: {tables_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"📄 找到 {len(table_files)} 个表格文件")
    print()
    
    # 统计变量
    success_count = 0
    total_pairs = 0
    failed_tables = []
    extreme_tables = []
    
    # 逐个处理
    for table_file in table_files:
        success, pairs, error = process_single_table(table_file, output_dir)
        
        if success:
            success_count += 1
            total_pairs += pairs
        else:
            failed_tables.append((table_file.name, error))
            if "极端情况" in str(error):
                extreme_tables.append(table_file.name)
    
    # 输出统计结果
    print()
    print("📊 处理结果统计")
    print("=" * 60)
    print(f"✅ 成功处理: {success_count} 个表格")
    print(f"📝 提取配对: {total_pairs:,} 对 alias-name")
    print(f"❌ 失败表格: {len(failed_tables)} 个")
    print(f"⚠️  极端情况: {len(extreme_tables)} 个")
    
    # 显示失败详情
    if failed_tables:
        print(f"\n❌ 失败表格详情:")
        for table_name, error in failed_tables:
            print(f"   {table_name}: {error}")
    
    # 显示极端情况
    if extreme_tables:
        print(f"\n⚠️  极端情况表格:")
        for table_name in extreme_tables:
            print(f"   {table_name}")
    
    print(f"\n🎯 成功率: {success_count}/{len(table_files)} ({success_count/len(table_files)*100:.1f}%)")

def main():
    # 输入和输出路径
    tables_dir = Path("example/data/tables")
    output_dir = Path("example/data/parsed_csv")
    
    # 检查输入目录
    if not tables_dir.exists():
        print(f"❌ 表格目录不存在: {tables_dir}")
        print("请先运行 split_tables.py 来分割表格")
        return
    
    # 处理所有表格
    process_all_tables(tables_dir, output_dir)

if __name__ == "__main__":
    main() 