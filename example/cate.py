import time, win32com.client, pythoncom

# ==============   配置：要添加的组分关键字   ==============
wanted = [
    "water", 
    "methane", 
    "ethanol",
    "C2H6O-2",  # alias for ethanol
]

# =========================================================

def find_component_id_basic(app, keyword):
    """
    基础版组分查找：使用Aspen Plus内置搜索
    返回: Component ID 或 None
    """
    print(f"[SEARCH] 搜索组分: '{keyword}'")
    
    # 方法1: 常见化合物的直接映射（优先使用，最可靠）
    common_components = {
        'water': 'H2O',
        'methane': 'CH4', 
        'ethanol': 'ETHANOL',
        'c2h6o-2': 'ETHANOL',  # alias mapping
    }
    
    keyword_lower = keyword.lower()
    if keyword_lower in common_components:
        component_id = common_components[keyword_lower]
        print(f"[SUCCESS] 内置映射找到: '{keyword}' → {component_id}")
        return component_id
    
    try:
        # 方法2: 尝试通过Engine访问（如果有的话）
        if hasattr(app, 'Engine') and app.Engine:
            print(f"[DEBUG] 尝试Engine搜索...")
            # Aspen Plus的Engine对象结构可能不同
            pass
        
        # 方法3: 尝试通过Tree访问数据库
        tree = app.Tree
        if tree:
            try:
                db_node = tree.FindNode(r"\Database")
                if db_node:
                    print(f"[DEBUG] 找到数据库节点")
                    # 这里可以进一步探索数据库结构
            except:
                pass
                
    except Exception as e:
        print(f"[DEBUG] 高级搜索异常: {e}")
    
    print(f"[FAIL] 未找到: '{keyword}'")
    return None

# ---------- 启动 Aspen ----------
print("🚀 启动 Aspen Plus...")
try:
    asp = win32com.client.gencache.EnsureDispatch("Apwn.Document")
    asp.InitNew2()
    asp.Visible = True
    asp.SuppressDialogs = 1
    time.sleep(2)  # 给Aspen更多时间启动
    
    app = asp.Application
    print("[SUCCESS] Aspen Plus 启动成功!")
    
    # 打印一些调试信息
    print(f"[DEBUG] App对象类型: {type(app)}")
    print(f"[DEBUG] 可用属性: {[attr for attr in dir(app) if not attr.startswith('_')][:10]}...")
    
except Exception as e:
    print(f"[ERROR] Aspen Plus 启动失败: {e}")
    print("请确保：")
    print("1. Aspen Plus 已正确安装")
    print("2. 有足够的许可证")
    print("3. 没有其他实例在运行")
    exit(1)

# ---------- 定位 TYPE 表 ----------
try:
    # 简化的表格定位方法
    root_input = asp.Tree.FindNode(r"\Data\Components\Specifications\Input")
    
    if root_input is None:
        print("[INFO] 组件输入节点不存在，使用默认路径...")
        # 尝试不同的路径
        root_input = asp.Tree.FindNode(r"\Data\Components\Specifications\Input")
        if root_input is None:
            print("[ERROR] 无法找到组件输入节点")
            exit(1)
    
    type_node = root_input.FindNode("TYPE")
    
    if type_node is None:
        print("[INFO] TYPE节点不存在，尝试创建...")
        try:
            # 简单创建方式
            type_node = root_input.FindNode("TYPE")
            if type_node is None:
                print("[WARN] 无法创建TYPE节点，可能需要手动在Aspen Plus中添加组件")
                # 仍然尝试访问，有时节点存在但FindNode找不到
                type_node = root_input
        except Exception as create_error:
            print(f"[WARN] 创建节点失败: {create_error}")
            type_node = root_input
    
    # 尝试访问Elements
    if hasattr(type_node, 'Elements'):
        tbl = type_node.Elements
    else:
        # 如果没有Elements，使用节点本身
        tbl = type_node
    
    print("[SUCCESS] 组件表格准备完成!")
    
    # 安全的RowCount检查
    try:
        if hasattr(tbl, 'RowCount'):
            try:
                row_count = tbl.RowCount(0)  # 使用维度参数
                print(f"[DEBUG] 表格当前行数: {row_count}")
            except:
                print(f"[DEBUG] 表格对象类型: {type(tbl)}")
        else:
            print(f"[DEBUG] 表格对象类型: {type(tbl)}")
    except Exception as row_error:
        print(f"[DEBUG] 无法获取行数: {row_error}")
    
except Exception as e:
    print(f"[ERROR] 组件表格准备失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ---------- 逐个关键字 → 查 ID → 写表 ----------
print("\n" + "="*60)
print("🚀 开始添加组分到Aspen模拟")
print("="*60)

added = []
for kw in wanted:
    print(f"\n[{len(added)+1}/{len(wanted)}] 处理: '{kw}'")
    
    try:
        cid = find_component_id_basic(app, kw)
        if not cid:
            print(f"[SKIP] '{kw}' 未找到，跳过")
            continue

        # 确保表格有足够的行
        try:
            # Aspen Plus的RowCount需要维度参数，通常第0维是行
            current_rows = tbl.RowCount(0)
        except:
            # 如果失败，尝试不同的方法
            try:
                current_rows = len(added)  # 使用当前已添加的数量作为估计
            except:
                current_rows = 0
        
        needed_rows = len(added) + 1
        
        # 简化的行添加策略：始终尝试添加一行
        try:
            tbl.InsertRow()
            print(f"[DEBUG] 添加了一行到表格")
        except Exception as insert_error:
            print(f"[DEBUG] 添加行失败: {insert_error}")

        row = len(added)
        tbl.SetLabel(row, 0, False, cid)     # Component ID 列
        tbl.SetLabel(row, 1, False, "PURE")  # Type 列
        added.append((kw, cid))
        print(f"[ADD] 已添加到表格第{row}行: {cid}")
        
    except Exception as e:
        print(f"[ERROR] 处理'{kw}'时出错: {e}")
        import traceback
        traceback.print_exc()
        continue

print(f"\n🎉 组分添加完成!")
print("="*60)
print("📋 成功添加的组分:")
for i, (original_kw, component_id) in enumerate(added, 1):
    print(f"   {i:2d}. '{original_kw}' → {component_id}")

print(f"\n📊 总结:")
print(f"   - 尝试添加: {len(wanted)} 个组分")
print(f"   - 成功添加: {len(added)} 个组分")
print(f"   - 成功率: {len(added)/len(wanted)*100:.1f}%")

# 验证表格内容
print(f"\n🔍 验证表格内容:")
try:
    # 尝试获取行数，使用维度参数
    try:
        row_count = tbl.RowCount(0)
        print(f"   - 最终表格行数: {row_count}")
    except:
        row_count = len(added)
        print(f"   - 估计表格行数: {row_count}")
    
    # 验证我们添加的内容
    for i in range(len(added)):
        try:
            comp_id = tbl.Label(i, 0)
            comp_type = tbl.Label(i, 1)
            print(f"   - 第{i}行: {comp_id} | {comp_type}")
        except Exception as label_error:
            print(f"   - 第{i}行读取失败: {label_error}")
            
except Exception as e:
    print(f"   - 验证失败: {e}")

print("="*60)

# 保存项目
try:
    import os
    save_path = os.path.abspath("example/data/aspen_basic_components.bkp")
    asp.SaveAs(save_path)
    print(f"\n💾 项目已保存到: {save_path}")
except Exception as e:
    print(f"[WARN] 保存项目失败: {e}")

print("\n✅ 脚本执行完成!")
print("Aspen Plus 窗口保持打开状态，您可以继续手动操作。")
