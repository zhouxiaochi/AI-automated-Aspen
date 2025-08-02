#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
升级版 PyMuPDF PDF 文字提取器
只处理包含化合物表格的页面（含有 P11 P10 的页面）
"""

from pathlib import Path
import re

def has_compound_table(page_text):
    """检查页面是否包含化合物表格标识"""
    # 修改为更宽松的检查：只要包含 P11 P10 即可
    pattern = r'P11\s+P10'
    return bool(re.search(pattern, page_text, re.IGNORECASE))

def extract_compound_pages_with_pymupdf(pdf_path, output_path):
    """使用 PyMuPDF 只提取包含化合物表格的页面"""
    try:
        import fitz  # PyMuPDF
        
        print("使用 PyMuPDF 提取化合物页面...")
        print("过滤规则: 页面包含 'P11 P10' 即处理")
        
        # 打开PDF文件
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        
        print(f"总页数: {total_pages}")
        
        all_lines = []
        processed_pages = 0
        compound_pages = []
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # 先获取页面的完整文本用于检查
            page_text = page.get_text()
            
            # 检查是否包含化合物表格
            if has_compound_table(page_text):
                compound_pages.append(page_num + 1)
                processed_pages += 1
                
                print(f"处理化合物页面: {page_num + 1}")
                
                # 添加页面标记
                all_lines.append(f"===== PAGE {page_num + 1} =====")
                all_lines.append("---")
                
                # 获取页面详细文本块进行逐行提取
                text_dict = page.get_text("dict")
                
                # 提取每一行文字
                for block in text_dict["blocks"]:
                    if "lines" in block:  # 文本块
                        for line in block["lines"]:
                            line_text = ""
                            for span in line["spans"]:
                                line_text += span["text"]
                            
                            # 清理文字并添加
                            line_text = line_text.strip()
                            if line_text:  # 只添加非空行
                                all_lines.append(line_text)
                                all_lines.append("---")  # 每行后添加分隔符
                
                # 页面结束标记
                all_lines.append("")
                all_lines.append("---")
            
            # 显示总体进度
            if (page_num + 1) % 50 == 0:
                print(f"扫描进度: {page_num + 1}/{total_pages} 页 (找到 {len(compound_pages)} 个化合物页面)")
        
        doc.close()
        
        # 写入输出文件
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        
        print(f"\n✅ 提取完成")
        print(f"📄 扫描页数: {total_pages}")
        print(f"🎯 化合物页面: {len(compound_pages)}")
        print(f"📝 提取行数: {len(all_lines):,}")
        print(f"💾 文件大小: {output_path.stat().st_size:,} 字节")
        print(f"💾 保存到: {output_path}")
        
        # 显示化合物页面列表
        if compound_pages:
            print(f"\n📋 化合物页面列表:")
            pages_str = ", ".join(str(p) for p in compound_pages[:25])
            if len(compound_pages) > 25:
                pages_str += f" ... (共 {len(compound_pages)} 页)"
            print(f"   {pages_str}")
        
        return True
        
    except ImportError:
        print("❌ PyMuPDF 未安装")
        print("请运行: pip install PyMuPDF")
        return False
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return False

def main():
    # 输入PDF路径
    pdf_path = Path("example/data/11.pdf")
    
    # 输出文本路径
    output_path = Path("example/data/PP.txt")
    
    # 检查输入文件是否存在
    if not pdf_path.exists():
        print(f"❌ PDF文件未找到: {pdf_path}")
        print("可用文件:")
        data_dir = Path("example/data")
        if data_dir.exists():
            for file in data_dir.iterdir():
                if file.is_file():
                    print(f"  - {file.name}")
        return
    
    print(f"📖 输入PDF: {pdf_path}")
    print(f"💾 输出文件: {output_path}")
    print(f"🎯 目标: 只提取包含 'P11 P10' 的页面")
    print()
    
    # 执行提取
    success = extract_compound_pages_with_pymupdf(pdf_path, output_path)
    
    if success:
        print()
        print("🎉 化合物页面提取成功！")
        print(f"现在可以检查提取的文字: {output_path}")
        print("📌 提示: 使用宽松过滤规则，可能包含更多相关页面")
    else:
        print("❌ 文字提取失败！")

if __name__ == "__main__":
    main() 