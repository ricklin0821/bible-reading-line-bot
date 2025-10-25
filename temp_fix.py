import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到根路由並替換
old_pattern = r'@app\.get\("/"\)\ndef read_root\(\):\n    """根路由，用於健康檢查"""\n    return \{"Hello": "Bible Reading Bot is running!"\}'
new_code = '''@app.get("/")
def read_root():
    """根路由，提供網頁預覽介面"""
    if os.path.exists("index.html"):
        return FileResponse("index.html", media_type="text/html")
    return {"Hello": "Bible Reading Bot is running!"}'''

content = re.sub(old_pattern, new_code, content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed main.py")
