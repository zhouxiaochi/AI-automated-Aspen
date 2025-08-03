# -*- coding: utf-8 -*-
"""
Aspen Plus (Apwn.Document) 组件自动添加脚本
- 支持用 别名/常用名/分子式/CAS 号 添加组件
- 让 Aspen 自行解析为规范 Component ID 后再正式写入
- 关键修正：RowCount/InsertRow/RemoveRow/Label/SetLabel 都需传入维度 dimension=0
"""

import sys
import traceback
import win32com.client


# —— 常量：组件表的“行维度” —— #
ROW_DIM = 0  # 行维度固定用 0


def boot_aspen():
    # 也可以用 Dispatch("Apwn.Document")
    aspen = win32com.client.gencache.EnsureDispatch("Apwn.Document")
    print(aspen)  # 例：Aspen Plus 40.0 OLE Services
    aspen.InitNew2()
    aspen.Visible = True
    aspen.SuppressDialogs = 1  # 压制弹窗
    return aspen


def set_property_method(aspen_doc, method_name="WILSON"):
    """设置热力学方法（可按需调整）"""
    try:
        aspen_doc.Tree.FindNode(
            r"\Data\Properties\Specifications\Input\GOPSETNAME"
        ).Value = method_name
    except Exception:
        print("WARN: 设置热力学方法失败：", traceback.format_exc(limit=1).strip())


# —— 工具函数：组件表对象与行数 —— #
def _get_comp_table(aspen_doc):
    """
    返回组件表对象（与你原脚本一致的路径/接口）
    """
    return (
        aspen_doc.Tree.FindNode(r"Data\Components\Specifications\Input")
        .Elements("TYPE")
        .Elements
    )


def _row_count(tbl):
    """行数 = RowCount(ROW_DIM)。"""
    f = getattr(tbl, "RowCount", None)
    if callable(f):
        return int(f(ROW_DIM))
    # 兜底：极少数环境下可尝试 Count()/len()
    f2 = getattr(tbl, "Count", None)
    if callable(f2):
        return int(f2())
    return int(len(tbl))


def _existing_ids(tbl):
    """读取当前表中已有的规范 ID，便于去重。"""
    ids = set()
    n = _row_count(tbl)
    for i in range(n):
        try:
            # Label(dimension, location, [force])
            ids.add(str(tbl.Label(ROW_DIM, i)).strip())
        except Exception:
            pass
    return ids


# —— 核心：解析别名 -> 规范 ID —— #
def resolve_component_id(aspen_doc, alias_text):
    """
    让 Aspen 用自身数据库把 alias_text(常用名/分子式/CAS/别名) 解析成标准 Component ID。
    返回解析后的 ID（如 'H2O', 'CH4'），解析失败则抛出异常。
    """
    tbl = _get_comp_table(aspen_doc)

    # 在表尾插入一行作为“临时解析行”
    tmp_row = _row_count(tbl)
    # InsertRow(dimension, location)
    tbl.InsertRow(ROW_DIM, tmp_row)

    # 在该行写入别名（等同 GUI 输入）
    # SetLabel(dimension, location, force, text)
    tbl.SetLabel(ROW_DIM, tmp_row, False, str(alias_text))

    # 触发一次处理，确保规范化生效
    try:
        aspen_doc.Tree.Process()
    except Exception:
        pass

    # 读取 Aspen 解析出的规范ID
    resolved = None
    try:
        # Label(dimension, location, [force])
        resolved = tbl.Label(ROW_DIM, tmp_row)
    except Exception:
        resolved = None

    # 如未取到，尝试从树节点读值（兜底）
    if not resolved:
        for p in (
            fr"\Data\Components\Specifications\Input\COMP\#{tmp_row + 1}\ID",
            fr"\Data\Components\Specifications\Input\COMPONENT\#{tmp_row + 1}\ID",
            fr"\Data\Components\Specifications\Input\COMP\#{tmp_row + 1}\LABEL",
        ):
            try:
                node = aspen_doc.Tree.FindNode(p)
                if node is not None and getattr(node, "Value", None):
                    resolved = node.Value
                    if resolved:
                        break
            except Exception:
                pass

    # 清理临时行
    try:
        # RemoveRow(dimension, location)
        tbl.RemoveRow(ROW_DIM, tmp_row)
    except Exception:
        pass

    if not resolved:
        raise RuntimeError(
            f"无法把别名 '{alias_text}' 解析为标准 Component ID，请确认该别名在 Aspen 数据库中存在。"
        )
    return str(resolved).strip()


# —— 对外：按别名添加组件（带去重） —— #
def add_component_by_alias(aspen_doc, alias_text, dedup=True):
    """
    使用别名添加组件：自动解析 -> 获取规范ID ->（可选去重）-> 正式插入。
    """
    cid = resolve_component_id(aspen_doc, alias_text)
    tbl = _get_comp_table(aspen_doc)

    if dedup:
        ids = _existing_ids(tbl)
        if cid in ids:
            print(f"[Skip] 已存在：alias='{alias_text}' -> ID='{cid}'")
            return cid

    row = _row_count(tbl)
    # 插入正式行并写入规范 ID
    tbl.InsertRow(ROW_DIM, row)
    tbl.SetLabel(ROW_DIM, row, False, cid)
    print(f"[Add] alias='{alias_text}' -> ID='{cid}'")
    return cid


def main():
    print("Add components!!")
    aspen = boot_aspen()

    # 可选：设置热力学方法
    set_property_method(aspen, "WILSON")

    # —— 示例：按别名/分子式/CAS 批量添加 —— #
    to_add = ["Water", "Methane", "7732-18-5", "APHA4HYD","C10H16N2O8" , "CH4", "4-HYDROXYACETOPHENONE", "C4H10O-5", "C10H16O4-D1"]

    tbl = _get_comp_table(aspen)
    print("RowCount (before):", _row_count(tbl))

    added = []
    for alias in to_add:
        try:
            cid = add_component_by_alias(aspen, alias, dedup=True)
            added.append(cid)
        except Exception as e:
            print("Failed:", alias, "=>", e)

    # 刷新一次
    try:
        aspen.Tree.Process()
    except Exception:
        pass

    print("RowCount (after):", _row_count(_get_comp_table(aspen)))
    print("Added IDs:", added)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
