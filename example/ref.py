print("Add components!!")
#import os
import win32com.client

#aspen = win32com.client.Dispatch("Apwn.Document")
aspen = win32com.client.gencache.EnsureDispatch("Apwn.Document")
print (aspen)
#print (dir(aspen.Tree))

aspen.InitNew2()

aspen.Visible=True
aspen.SuppressDialogs = 1 # 压制对话框的弹出，1为压制；0为不压制


print(dir(aspen.Tree))
tbl= aspen.Tree.FindNode(r"Data\Components\Specifications\Input").Elements("TYPE").Elements
print("tbl content")
print(dir(tbl))


print("tbl elements setlabel content")
# Print out all callable functions/methods for tbl
print("tbl functions/methods:")
for attr in dir(tbl):
    try:
        if callable(getattr(tbl, attr)):
            print(attr)
    except Exception:
        pass

print(dir(tbl.SetLabel))
aspen.Tree.FindNode(r"\Data\Properties\Specifications\Input\GOPSETNAME").Value="WILSON"

print('results:',tbl.SetLabel)
print('RowCount',tbl.RowCount)
#tbl.InsertRow(0)
#if tbl.RowCount()==0:
#    tbl.InsertRow(0)
print('RowCount',tbl.RowCount)

tbl.SetLabel(0,0,False,"Water")
tbl.SetLabel(0,1,False,"CH4")
tbl.SetLabel(0,2,False,"4-HYDROXYACETOPHENONE")