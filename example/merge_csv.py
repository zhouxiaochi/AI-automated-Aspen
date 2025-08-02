#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV合并工具：将所有解析后的table CSV文件合并为最终的化合物数据库
"""

from pathlib import Path
import csv
import re

def merge_csv_files(input_dir, output_file):
    """合并所有CSV文件"""
    
    print("🔧 CSV文件合并工具")
    print("=" * 50)
    
    # 获取所有CSV文件
    csv_files = sorted(input_dir.glob("table_*.csv"))
    
    if not csv_files:
        print(f"❌ 没有找到CSV文件在 {input_dir}")
        return
    
    print(f"📁 输入目录: {input_dir}")
    print(f"📄 找到 {len(csv_files)} 个CSV文件")
    print(f"💾 输出文件: {output_file}")
    print()
    
    # 统计数据
    total_compounds = 0
    processed_files = 0
    failed_files = []
    all_compounds = []
    seen_pairs = set()  # 去重用
    
    # 逐个处理CSV文件
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                file_compounds = 0
                
                for row in reader:
                    databank = row.get('databank', '').strip()
                    alias = row.get('alias_or_code', '').strip().upper()
                    name = row.get('registered_name', '').strip().upper()
                    
                    # 基本验证
                    if alias and name and databank:
                        # 去重：检查是否已存在相同的alias-name对
                        pair_key = (alias, name)
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            all_compounds.append({
                                'databank': databank,
                                'alias_or_code': alias,
                                'registered_name': name,
                                'source_table': csv_file.stem
                            })
                            file_compounds += 1
                
                total_compounds += file_compounds
                processed_files += 1
                print(f"✅ {csv_file.name}: {file_compounds:3d} 化合物")
                
        except Exception as e:
            error_msg = f"读取失败: {e}"
            failed_files.append((csv_file.name, error_msg))
            print(f"❌ {csv_file.name}: {error_msg}")
    
    # 按alias排序
    all_compounds.sort(key=lambda x: x['alias_or_code'])
    
    # 写入合并后的CSV文件
    try:
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if all_compounds:
                fieldnames = ['databank', 'alias_or_code', 'registered_name', 'source_table']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_compounds)
        
        print(f"\n✅ 合并完成!")
        print(f"📊 处理统计:")
        print(f"   - 成功文件: {processed_files}/{len(csv_files)} 个")
        print(f"   - 总化合物: {total_compounds:,} 个")
        print(f"   - 去重后: {len(all_compounds):,} 个")
        print(f"   - 去重率: {((total_compounds - len(all_compounds))/total_compounds*100):.1f}%" if total_compounds > 0 else "   - 去重率: 0%")
        print(f"💾 输出文件: {output_file}")
        print(f"📏 文件大小: {output_file.stat().st_size:,} 字节")
        
        # 显示失败文件
        if failed_files:
            print(f"\n❌ 失败文件:")
            for filename, error in failed_files:
                print(f"   {filename}: {error}")
        
        return len(all_compounds)
        
    except Exception as e:
        print(f"❌ 写入输出文件失败: {e}")
        return 0

def analyze_compounds(csv_file):
    """分析化合物数据"""
    
    if not csv_file.exists():
        print(f"❌ 文件不存在: {csv_file}")
        return
    
    print(f"\n📊 化合物数据分析:")
    print("=" * 50)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            compounds = list(reader)
        
        print(f"📝 总化合物数: {len(compounds):,}")
        
        # 按数据库分类统计
        databank_stats = {}
        for compound in compounds:
            db = compound.get('databank', 'Unknown')
            databank_stats[db] = databank_stats.get(db, 0) + 1
        
        print(f"\n📋 按数据库分类:")
        for db, count in sorted(databank_stats.items()):
            print(f"   {db}: {count:,} 个")
        
        # 显示前10个化合物样例
        print(f"\n🔍 前10个化合物样例:")
        for i, compound in enumerate(compounds[:10], 1):
            alias = compound.get('alias_or_code', '')
            name = compound.get('registered_name', '')
            print(f"   {i:2d}. {alias} → {name}")
        
        if len(compounds) > 10:
            print(f"   ... (还有 {len(compounds)-10:,} 个)")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    # 输入和输出路径
    input_dir = Path("example/data/parsed_csv")
    output_file = Path("example/data/final_compounds.csv")
    
    # 检查输入目录
    if not input_dir.exists():
        print(f"❌ 输入目录不存在: {input_dir}")
        print("请先运行 parse_tables.py 来解析表格")
        return
    
    # 合并CSV文件
    compound_count = merge_csv_files(input_dir, output_file)
    
    # 分析结果
    if compound_count > 0:
        analyze_compounds(output_file)
        print(f"\n🎉 任务完成！")
        print(f"🎯 最终结果: {compound_count:,} 个化合物 alias-name 配对")
        print(f"📁 保存在: {output_file}")
    else:
        print("❌ 合并失败！")

if __name__ == "__main__":
    main() 