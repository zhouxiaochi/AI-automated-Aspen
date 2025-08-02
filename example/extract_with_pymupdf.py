#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用 PyMuPDF 逐行提取 PDF 文字
每一行之间添加 --- 分隔符
"""

from pathlib import Path
import sys

def extract_text_with_pymupdf(pdf_path, output_path):
    """使用 PyMuPDF 逐行提取文字"""
    try:
        import fitz  # PyMuPDF
        
        print("使用 PyMuPDF 提取文字...")
        
        # 打开PDF文件
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        
        print(f"总页数: {total_pages}")
        
        all_lines = []
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # 添加页面标记
            all_lines.append(f"===== PAGE {page_num + 1} =====")
            all_lines.append("---")
            
            # 获取页面文本块
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
            
            # 显示进度
            if (page_num + 1) % 10 == 0:
                print(f"已处理: {page_num + 1}/{total_pages} 页")
        
        doc.close()
        
        # 写入输出文件
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        
        print(f"✅ 提取完成")
        print(f"📄 总页数: {total_pages}")
        print(f"📝 总行数: {len(all_lines):,}")
        print(f"💾 文件大小: {output_path.stat().st_size:,} 字节")
        print(f"💾 保存到: {output_path}")
        
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
    print()
    
    # 执行提取
    success = extract_text_with_pymupdf(pdf_path, output_path)
    
    if success:
        print()
        print("🎉 文字提取成功！")
        print(f"现在可以检查提取的文字: {output_path}")
    else:
        print("❌ 文字提取失败！")

if __name__ == "__main__":
    main() 