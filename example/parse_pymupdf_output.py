#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解析 PyMuPDF 提取的化合物数据
处理每行之间有 --- 分隔符的格式
"""

from pathlib import Path
import re
import csv

def parse_compound_data(lines):
    """解析化合物数据"""
    
    compounds = []
    
    # 状态跟踪
    in_compound_table = False
    current_alias = None
    current_name = None
    x_count = 0
    
    # 查找表头模式
    alias_header_found = False
    name_header_found = False
    db_header_found = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过分隔符
        if line == "---":
            i += 1
            continue
        
        # 检查是否是化合物表头
        if line == "Alias":
            alias_header_found = True
            print(f"找到 Alias 表头 at line {i+1}")
            i += 1
            continue
            
        if alias_header_found and line == "Name":
            name_header_found = True
            print(f"找到 Name 表头 at line {i+1}")
            i += 1
            continue
            
        if alias_header_found and name_header_found and re.match(r"P11.*P10.*P93.*P856.*PCD", line):
            db_header_found = True
            in_compound_table = True
            print(f"找到数据库表头 at line {i+1}")
            print("开始解析化合物数据...")
            i += 1
            continue
        
        # 检查表格结束
        if in_compound_table and (
            line.startswith("===== PAGE") or
            "Available in Databank" in line or
            line.startswith("Aqueous Component") or
            line.startswith("Combust Component") or
            line.startswith("Electrolytes") or
            "Component Databank" in line
        ):
            # 保存当前化合物（如果有）
            if current_alias and current_name:
                compounds.append({
                    'alias': current_alias,
                    'name': current_name,
                    'pure11': x_count >= 1  # 第一个X表示PURE11
                })
            
            # 重置状态
            in_compound_table = False
            alias_header_found = False
            name_header_found = False
            db_header_found = False
            current_alias = None
            current_name = None
            x_count = 0
            i += 1
            continue
        
        # 解析化合物数据
        if in_compound_table and line:
            if line == "X":
                x_count += 1
            elif is_chemical_formula(line):
                # 保存之前的化合物
                if current_alias and current_name:
                    compounds.append({
                        'alias': current_alias,
                        'name': current_name,
                        'pure11': x_count >= 1
                    })
                
                # 开始新的化合物
                current_alias = line
                current_name = None
                x_count = 0
            elif is_compound_name(line) and current_alias and not current_name:
                current_name = line
        
        i += 1
    
    # 保存最后一个化合物
    if current_alias and current_name:
        compounds.append({
            'alias': current_alias,
            'name': current_name,
            'pure11': x_count >= 1
        })
    
    return compounds

def is_chemical_formula(text):
    """判断是否是化学式"""
    
    # 基本模式检查
    if not text or len(text) > 30:
        return False
    
    # 化学式模式：大写字母开头，包含字母、数字、括号等
    if not re.match(r'^[A-Z][A-Z0-9\(\)\-\.\:\*]*$', text):
        return False
    
    # 排除明显不是化学式的
    exclude_patterns = [
        r'^(NAME|ALIAS|AVAILABLE|DATABANK|TABLE|PAGE)$',
        r'^[A-Z]{10,}$',  # 太多连续字母
        r'^\d+$',  # 纯数字
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    return True

def is_compound_name(text):
    """判断是否是化合物名称"""
    
    if not text or len(text) < 3 or len(text) > 100:
        return False
    
    # 化合物名称模式：通常包含大写字母、连字符等
    if not re.match(r'^[A-Z][A-Z0-9\-\.\:\*\,\(\)\s]*$', text):
        return False
    
    # 排除明显不是化合物名称的
    exclude_patterns = [
        r'^X+$',
        r'^(NAME|ALIAS|AVAILABLE|DATABANK|TABLE|PAGE)$',
        r'^\d+$'
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    return True

def main():
    input_file = Path("example/data/PP.txt")
    output_file = Path("example/data/compounds_final.csv")
    
    if not input_file.exists():
        print(f"❌ 输入文件未找到: {input_file}")
        return
    
    print(f"📖 读取文件: {input_file}")
    
    # 读取文本行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lines = [line.strip() for line in lines]
    print(f"📝 总行数: {len(lines):,}")
    
    # 解析化合物
    print("🔍 解析化合物数据...")
    compounds = parse_compound_data(lines)
    
    # 过滤 PURE11 化合物
    pure11_compounds = [c for c in compounds if c['pure11']]
    
    print(f"✅ 总计化合物: {len(compounds)}")
    print(f"🎯 PURE11 化合物: {len(pure11_compounds)}")
    
    # 写入 CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['databank', 'alias_or_code', 'registered_name'])
        
        for compound in pure11_compounds:
            writer.writerow([
                'PURE11',
                compound['alias'],
                compound['name']
            ])
    
    print(f"💾 保存到: {output_file}")
    
    # 显示示例
    print(f"\n📋 前 15 个 PURE11 化合物:")
    for i, compound in enumerate(pure11_compounds[:15], 1):
        print(f"{i:2d}. {compound['alias']:15s} -> {compound['name']}")
    
    # 统计信息
    if pure11_compounds:
        alias_lengths = [len(c['alias']) for c in pure11_compounds]
        name_lengths = [len(c['name']) for c in pure11_compounds]
        
        print(f"\n📊 统计:")
        print(f"   别名长度: {min(alias_lengths)}-{max(alias_lengths)} 字符")
        print(f"   名称长度: {min(name_lengths)}-{max(name_lengths)} 字符")

if __name__ == "__main__":
    main() 