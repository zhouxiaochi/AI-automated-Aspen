# -*- coding: utf-8 -*-
"""
APRSYS 'Physical Property Data' PDF 解析工具（按步骤执行）
步骤：
  1) find-pages  : 识别包含"对照表/目录"的页面
  2) extract     : 从相关页面抽取文字（尽量保留列距）
  3) parse       : 从文字解析 "别名/代码 ↔ 注册名"（聚焦 PURE11）

依赖：
  pip install pdfminer.six

作者注：
  - 针对手册中"Available in Databank"表格（列含 Alias / Name / P11 ...），
    第 3 步会找出 P11 列为 'X' 的行，输出到 CSV。
  - 若你的 PDF 版式差异较大，可调正则/阈值或发我样例我再帮你微调。
"""
import argparse
import re
import sys
import csv
import json
import unicodedata
from pathlib import Path
from typing import List, Tuple, Iterable, Optional

# --------- 文本提取：多种方法备选 ---------
def extract_text_pages(pdf_path: Path) -> Iterable[Tuple[int, str]]:
    """
    逐页返回 (page_number, text)，尝试多种方法以应对有问题的 PDF 文件
    """
    # 方法1：尝试 PyPDF2（更容错）
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as fp:
            reader = PyPDF2.PdfReader(fp)
            for i, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text()
                    yield i, text
                except Exception as page_err:
                    print(f"[WARN] PyPDF2 页面 {i} 提取失败: {page_err}")
                    yield i, ""
        return
    except ImportError:
        print("[INFO] PyPDF2 未安装，尝试 pdfminer.six...")
    except Exception as e:
        print(f"[WARN] PyPDF2 提取失败: {e}，尝试 pdfminer.six...")
    
    # 方法2：尝试 pdfminer.six
    try:
        from pdfminer.pdfpage import PDFPage
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import TextConverter
        from pdfminer.layout import LAParams
        from pdfminer.high_level import extract_text
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        import io
        
        # 方法2a：直接处理文档而不依赖页面标签
        try:
            with open(pdf_path, 'rb') as fp:
                parser = PDFParser(fp)
                doc = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                laparams = LAParams()
                
                page_count = 0
                for page in PDFPage.create_pages(doc):
                    page_count += 1
                    outfp = io.StringIO()
                    device = TextConverter(rsrcmgr, outfp, laparams=laparams)
                    interpreter = PDFPageInterpreter(rsrcmgr, device)
                    try:
                        interpreter.process_page(page)
                        text = outfp.getvalue()
                        yield page_count, text
                    except Exception as page_err:
                        print(f"[WARN] pdfminer 页面 {page_count} 处理失败: {page_err}")
                        yield page_count, ""
                    finally:
                        outfp.close()
                        device.close()
        except Exception as e1:
            print(f"[WARN] pdfminer 直接处理失败: {e1}，尝试简单文本提取...")
            
            # 方法2b：最简单的文本提取（可能失去分页信息）
            try:
                full = extract_text(str(pdf_path))
                if "\x0c" in full:  # 有分页符
                    pages = full.split("\x0c")
                    for i, page in enumerate(pages, start=1):
                        yield i, page
                else:  # 没有分页符，整个文档作为一页
                    yield 1, full
            except Exception as e2:
                print(f"[ERR] 所有方法都失败: {e2}")
                raise
                
    except ImportError:
        print("[ERR] 需要安装 pdfminer.six： pip install pdfminer.six")
        raise

# --------- 工具函数 ---------
def norm(s: str) -> str:
    """统一文本：NFKC 归一化 + 去非换行空格"""
    s = unicodedata.normalize("NFKC", s or "")
    return s.replace("\u00a0", " ")

def save_lines(path: Path, lines: List[str]):
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 写入: {path}  (共 {len(lines)} 行)")

def save_pages(path: Path, pages: List[int]):
    path.write_text("\n".join(str(p) for p in pages), encoding="utf-8")
    print(f"[OK] 页码写入: {path}  (共 {len(pages)} 页)")

def load_pages(path: Path) -> List[int]:
    pages = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln.isdigit():
            pages.append(int(ln))
    return pages

# --------- Step 1: 识别包含"对照表"的页面 ---------
def find_relevant_pages(pdf: Path) -> List[int]:
    """
    识别页面的启发式规则：
      - 出现 'Available in Databank'（目录总标题）
      - 或 同页包含表头关键词：'Alias' 和 'Name'，并且出现 'P11'（PURE11 列）
      - 或 行内大量"别名形状"的 token（如 C2H6O-2 / 大写字母数字+连字符组成的短 token）
    """
    relevant = []
    alias_shape = re.compile(r"\b[A-Z0-9][A-Z0-9\-\(\)\/\.\+]{1,15}\b")
    for pgno, raw in extract_text_pages(pdf):
        txt = norm(raw)
        up = txt.upper()
        score = 0
        if "AVAILABLE IN DATABANK" in up:
            score += 2
        if ("ALIAS" in up and "NAME" in up and "P11" in up):
            score += 2
        # 别名样式的 token 数量
        tokens = alias_shape.findall(up)
        if len(tokens) >= 40:  # 阈值可调：一页上如果出现很多短大写 token，可能是目录页
            score += 1
        if score >= 2:
            relevant.append(pgno)
    print(f"[INFO] find-pages: 命中 {len(relevant)} 页：{relevant[:12]}{' ...' if len(relevant)>12 else ''}")
    return relevant

# --------- Step 2: 抽取相关页面文本 ---------
def extract_pages_text(pdf: Path, pages: List[int]) -> List[str]:
    """
    将相关页的文本逐页抽出并返回（也可保存为 .txt）。
    """
    page_set = set(pages)
    out_lines = []
    for pgno, raw in extract_text_pages(pdf):
        if pgno in page_set:
            txt = norm(raw)
            out_lines.append(f"===== [PAGE {pgno}] =====")
            out_lines.extend(txt.splitlines())
            out_lines.append("")  # 分隔空行
    print(f"[INFO] extract: 输出行数≈{len(out_lines)}")
    return out_lines

# --------- Step 3: 从文本解析对照表（聚焦 PURE11） ---------
def parse_alias_name_from_text(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    解析逻辑：
      - 识别"Available in Databank"块，定位紧随其后的"表头行"
      - 表头中找到 'P11' 的列索引
      - 之后的非空行解析化合物条目：alias name 数据库标记...
      - 如果包含 P11 标记（通常是 X），则认为该 alias/name 属于 PURE11
    """
    out = []
    inside_table = False
    
    # 表头检测 - 更宽松的匹配
    hdr_detect = re.compile(r"alias.*name.*p11", re.IGNORECASE)
    
    # 结束块的启发关键字
    end_block_markers = (
        "===== [PAGE",
        "PURE COMPONENT DATABANK PARAMETERS", 
        "PURE COMPONENT DATABANKS:",
        "DATABANKS:",
        "•"
    )
    
    # 用于清理空格的正则
    space_clean = re.compile(r'\s+')

    for i, raw in enumerate(lines):
        L = norm(raw).strip()
        U = L.upper()

        # 查找表头行
        if hdr_detect.search(U):
            inside_table = True
            continue

        # 结束块？
        if inside_table and (not L or any(m in U for m in end_block_markers)):
            inside_table = False
            continue

        # 解析数据行
        if inside_table and L and not any(m in U for m in ("AVAILABLE IN DATABANK", "ALIAS NAME P11")):
            try:
                # 寻找化合物条目模式：别名 名称 数据库标记
                # 处理可能的格式：ALIAS NAME XXXXX 或 ALIAS-WITH-DASHES COMPOUND-NAME XXXXX
                
                # 首先尝试找到连续的X标记（表示数据库可用性）
                x_pattern = re.search(r'\bX+\b', L)
                if x_pattern:
                    # 获取X标记之前的部分
                    pre_x = L[:x_pattern.start()].strip()
                    x_marks = x_pattern.group()
                    
                    # 清理多余空格并分割
                    pre_x_clean = space_clean.sub(' ', pre_x)
                    parts = pre_x_clean.split()
                    
                    if len(parts) >= 2:
                        # 尝试识别别名和名称
                        # 通常别名较短，名称较长
                        alias_parts = []
                        name_parts = []
                        
                        # 简单启发式：如果有连字符或看起来像化学符号，可能是别名
                        found_name_start = False
                        for part in parts:
                            if not found_name_start:
                                # 检查是否看起来像化学名称的开始
                                if (len(part) > 4 and not re.match(r'^[A-Z0-9\(\)\-\+\.]+$', part)) or \
                                   any(word in part.upper() for word in ['ACID', 'OXIDE', 'CHLORIDE', 'AMINE', 'ALCOHOL']):
                                    found_name_start = True
                                    name_parts.append(part)
                                else:
                                    alias_parts.append(part)
                            else:
                                name_parts.append(part)
                        
                        # 如果没有找到明确的名称开始，按位置分割
                        if not name_parts and len(parts) >= 2:
                            alias_parts = parts[:1]
                            name_parts = parts[1:]
                        
                        if alias_parts and name_parts:
                            alias = ''.join(alias_parts).upper()
                            name = '-'.join(name_parts).upper()
                            
                            # 检查是否在 P11 中可用（第一个X通常表示P11）
                            if 'X' in x_marks:
                                # 基本过滤
                                if (alias and name and 
                                    len(alias) <= 50 and len(name) <= 100 and
                                    not alias.isdigit() and
                                    alias not in {"DATABANK", "COMPONENT", "AVAILABLE"}):
                                    out.append(("PURE11", alias, name))
                                    
            except Exception as e:
                # 忽略解析错误，继续处理下一行
                continue

    # 去重
    uniq = []
    seen = set()
    for row in out:
        if row not in seen:
            seen.add(row)
            uniq.append(row)
    
    print(f"[INFO] parse: 解析出 PURE11 条目 {len(uniq)} 条")
    return uniq

# --------- 主程序（分步/一体） ---------
def cmd_find_pages(args):
    pages = find_relevant_pages(Path(args.pdf))
    save_pages(Path(args.output), pages)

def cmd_extract(args):
    pages = load_pages(Path(args.pages))
    lines = extract_pages_text(Path(args.pdf), pages)
    save_lines(Path(args.output), lines)

def cmd_parse(args):
    # 允许从文本文件输入（更可复核）
    text_path = Path(args.pages_text)
    lines = text_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    records = parse_alias_name_from_text(lines)
    out_csv = Path(args.output)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["databank","alias_or_code","registered_name"])
        w.writerows(records)
    print(f"[OK] 写入 CSV: {out_csv}  ({len(records)} 行)")

def cmd_all(args):
    pdf = Path(args.pdf)
    # 1) 找页
    pages = find_relevant_pages(pdf)
    # 2) 抽文本
    lines = extract_pages_text(pdf, pages)
    # 3) 解析
    records = parse_alias_name_from_text(lines)
    out_csv = Path(args.output)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["databank","alias_or_code","registered_name"])
        w.writerows(records)
    # 同时把中间文本落盘便于复核
    mid_txt = out_csv.with_suffix(".pages_text.txt")
    save_lines(mid_txt, lines)
    print(f"[DONE] CSV -> {out_csv}；中间文本 -> {mid_txt}")

def build_argparser():
    p = argparse.ArgumentParser(description="Parse APRSYS Physical Property Data PDF to build alias↔name mapping for PURE11.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("find-pages", help="Step 1: find relevant pages that contain the directory table")
    p1.add_argument("pdf", help="Input PDF path")
    p1.add_argument("-o", "--output", required=True, help="Output page list file (e.g., pages.txt)")
    p1.set_defaults(func=cmd_find_pages)

    p2 = sub.add_parser("extract", help="Step 2: extract text from relevant pages")
    p2.add_argument("pdf", help="Input PDF path")
    p2.add_argument("--pages", required=True, help="Page list file generated by find-pages")
    p2.add_argument("-o", "--output", required=True, help="Output text file (pages_text.txt)")
    p2.set_defaults(func=cmd_extract)

    p3 = sub.add_parser("parse", help="Step 3: parse alias↔name mapping (PURE11 only) from extracted text")
    p3.add_argument("--pages-text", required=True, help="The text file produced by extract step")
    p3.add_argument("-o", "--output", required=True, help="Output CSV path")
    p3.set_defaults(func=cmd_parse)

    p4 = sub.add_parser("all", help="Run all steps at once")
    p4.add_argument("pdf", help="Input PDF path")
    p4.add_argument("-o", "--output", required=True, help="Output CSV path")
    p4.set_defaults(func=cmd_all)

    return p

if __name__ == "__main__":
    ap = build_argparser()
    args = ap.parse_args()
    args.func(args)
