from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import qrcode, segno, uuid, shutil, os
from pathlib import Path
from database import init_db, get_item, save_item
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# 创建文件夹
Path("static/qr").mkdir(parents=True, exist_ok=True)
Path("static/uploads").mkdir(parents=True, exist_ok=True)
init_db()

# 电脑打开这个页面批量生成二维码
@app.get("/", response_class=HTMLResponse)
async def admin():
    return open("templates/admin.html", encoding="utf-8").read()

# 生成新二维码（返回JSON，供前端调用）
@app.get("/api/new")
def new_qr():
    item_id = str(uuid.uuid4())[:8].upper()
    url = f"https://你的域名.com/item/{item_id}"   # ←←←←← 重点改这里！！！
    
    # 生成超高清二维码（适合喷码）
    qr = segno.make(url, error='H')
    qr.save(f"static/qr/{item_id}.png", scale=20, border=2, dark="#000000")
    
    return {
        "id": item_id,
        "url": url,
        "qr_png": f"/static/qr/{item_id}.png"
    }

# 扫码后打开的页面（手机）
@app.get("/item/{item_id}")
async def item_page(item_id: str, request: Request):
    item = get_item(item_id)
    return templates.TemplateResponse("index.html", {"request": request, "item": item})

# 保存信息
@app.post("/item/{item_id}")
async def save(
    item_id: str,
    name: str = Form(""),
    location: str = Form(""),
    buy_date: str = Form(""),
    owner: str = Form(""),
    remark: str = Form(""),
    photo: UploadFile = File(None)
):
    item = {"id": item_id, "name": name, "location": location,
            "buy_date": buy_date, "owner": owner, "remark": remark}
    
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1].lower()
        filename = f"{item_id}_{int(datetime.now().timestamp())}.{ext}"
        path = f"static/uploads/{filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        item["photo"] = f"/uploads/{filename}"
    
    save_item(item)
    return {"status": "success"}

# 打包下载所有二维码
@app.get("/download_all")
def download_all():
    shutil.make_archive("all_qr", "zip", "static/qr")
    return FileResponse("all_qr.zip", filename="所有二维码.zip")