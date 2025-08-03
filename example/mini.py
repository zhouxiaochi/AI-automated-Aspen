# add_components_v14_pure_search.py
import time, win32com.client

# 关键词可改：名称 / 别名 / 化学式 / CAS
keywords = ["water", "methane", "64-17-5", "4-hydroxyacetophenone"]

ROW_DIM = 0         # 行维度固定 = 0

# ---------- 启动空 Aspen ----------
asp = win32com.client.gencache.EnsureDispatch("Apwn.Document")
asp.InitNew2(); asp.SuppressDialogs = 1; asp.Visible = True
time.sleep(0.5)

# ---------- 保证 TYPE 表 ----------
def ensure_type_table():
    node = asp.Tree.FindNode(r"\Data\Components\Specifications\Input")
    if node is None:
        comp = asp.Tree.NewChild("Components")
        spec = comp.NewChild("Specifications")
        node = spec.NewChild("Input")
    tnode = node.FindNode("TYPE") or node.NewChild("TYPE")
    return tnode.Elements
tbl = ensure_type_table()

# ---------- 用 WATER 触发数据库挂接 ----------
tbl.SetLabel(ROW_DIM, 0, False, "WATER")
asp.Process("COMP-SETUP")                  # 组件向导
asp.Process("PROP-SETUP")                  # 物性向导
tbl.RemoveRow(ROW_DIM, 0)                  # 清掉占位行

# ---------- 找 PURE 数据库表 ----------
db_root = asp.Tree.FindNode(r"\Data\Components\Databanks")
if db_root is None:
    db_root = asp.Tree.FindNode(r"\Data\Components\DBANKS")
if db_root is None:
    raise RuntimeError("找不到 Databanks – 若为企业定制版，请在 GUI 进入一次 Properties 后再跑")

def children(n):
    for i in range(1, getattr(n, "Count", 0) + 1):
        yield n.Item(i)

pure_tbl = None
for bank in children(db_root):
    if bank.Name.upper().startswith("PURE"):
        pure_tbl = bank.Elements; break
if pure_tbl is None:
    raise RuntimeError("PURE databank 表不存在")

# ---------- 搜索函数：Name 列 → Alias/CAS 列 ----------
def search_cid(keyword: str) -> str | None:
    kw = keyword.lower()
    for r in range(pure_tbl.RowCount):
        cid   = str(pure_tbl.Label(r, 0)).strip()
        name1 = str(pure_tbl.Label(r, 1)).lower().strip()
        alias = str(pure_tbl.Label(r, 2) or "").lower().strip()
        if kw in (cid.lower(), name1, alias):
            return cid
    return None

# ---------- 写入组分 ----------
def existing_ids():
    return {str(tbl.Label(ROW_DIM, r)).strip() for r in range(tbl.RowCount)}

ids_in_table = existing_ids()
added = []

for key in keywords:
    cid = search_cid(key)
    if not cid:
        print(f"[WARN] '{key}' 未在 PURE 数据库找到")
        continue
    if cid in ids_in_table:
        print(f"[Skip] 已存在：{cid}")
        continue
    if tbl.RowCount == len(ids_in_table | set(added)):
        tbl.InsertRow(ROW_DIM, tbl.RowCount)
    row = len(ids_in_table | set(added))
    tbl.SetLabel(ROW_DIM, row, False, cid)
    tbl.SetLabel(ROW_DIM, row, False, "PURE")   # 第 1 列
    added.append(cid)

print("\n[OK] 写入完成:", added)
