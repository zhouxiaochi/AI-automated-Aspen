#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分表工具：将 PP.txt 按照表头分割成独立的子表文件
每个子表都以 "---\nAlias\n---\nName\n---" 模式开始
"""

from pathlib import Path
import re

def find_table_headers(lines):
    """查找所有表头的位置"""
    table_positions = []
    
    # 查找模式: ---\nAlias\n---\nName\n---
    for i in range(len(lines) - 4):
        if (lines[i].strip() == "---" and 
            lines[i+1].strip() == "Alias" and
            lines[i+2].strip() == "---" and
            lines[i+3].strip() == "Name" and
            lines[i+4].strip() == "---"):
            table_positions.append(i)
    
    return table_positions

def extract_table_content(lines, start_pos, end_pos=None):
    """提取单个表的内容"""
    if end_pos is None:
        end_pos = len(lines)
    
    # 从表头开始提取到下一个表头或文件结束
    table_lines = []
    for i in range(start_pos, end_pos):
        table_lines.append(lines[i])
    
    return table_lines

def split_tables(input_file, output_dir):
    """将 PP.txt 分割成独立的表文件"""
    
    print(f"📖 读取文件: {input_file}")
    
    # 读取所有行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 总行数: {len(lines):,}")
    
    # 查找所有表头位置
    table_positions = find_table_headers(lines)
    
    print(f"📋 找到 {len(table_positions)} 个表格:")
    for i, pos in enumerate(table_positions, 1):
        print(f"   表 {i}: 第 {pos+1} 行")
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    print(f"📁 创建输出目录: {output_dir}")
    
    # 分割并保存每个表
    for i, start_pos in enumerate(table_positions):
        # 确定结束位置
        if i + 1 < len(table_positions):
            end_pos = table_positions[i + 1]
        else:
            end_pos = len(lines)
        
        # 提取表内容
        table_content = extract_table_content(lines, start_pos, end_pos)
        
        # 清理空行（保留一些结构）
        cleaned_content = []
        for line in table_content:
            line = line.rstrip()  # 移除行尾空白
            if line or (cleaned_content and cleaned_content[-1] != ""):  # 避免连续空行
                cleaned_content.append(line)
        
        # 保存到文件
        table_file = output_dir / f"table_{i+1:02d}.txt"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_content))
        
        print(f"💾 表 {i+1:2d}: {len(cleaned_content):4d} 行 → {table_file.name}")
    
    return len(table_positions)

def analyze_table_summary(output_dir):
    """分析分割后的表格摘要"""
    table_files = sorted(output_dir.glob("table_*.txt"))
    
    if not table_files:
        print("❌ 没有找到表格文件")
        return
    
    print(f"\n📊 表格分析摘要:")
    print("=" * 50)
    
    total_lines = 0
    for table_file in table_files:
        with open(table_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 统计数据行（排除分隔符和表头）
        data_lines = 0
        for line in lines:
            line = line.strip()
            if line and line != "---" and line not in ["Alias", "Name", "Available in Databank"]:
                data_lines += 1
        
        size_kb = table_file.stat().st_size / 1024
        total_lines += len(lines)
        
        print(f"{table_file.name}: {len(lines):4d} 行 ({data_lines:3d} 数据行) - {size_kb:5.1f} KB")
    
    print("=" * 50)
    print(f"总计: {len(table_files)} 个表格, {total_lines:,} 行")

def main():
    # 输入和输出路径
    input_file = Path("example/data/PP.txt")
    output_dir = Path("example/data/tables")
    
    print("🔧 化合物表格分割工具")
    print("=" * 50)
    
    # 检查输入文件
    if not input_file.exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return
    
    # 执行分割
    num_tables = split_tables(input_file, output_dir)
    
    # 分析结果
    if num_tables > 0:
        analyze_table_summary(output_dir)
        print(f"\n✅ 成功分割 {num_tables} 个表格")
        print(f"📁 输出目录: {output_dir}")
        print("🎯 现在可以逐个处理每个表格了！")
    else:
        print("❌ 没有找到有效的表格")

if __name__ == "__main__":
    main() 