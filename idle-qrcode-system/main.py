from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import qrcode, segno, uuid, shutil, os, ssl
from pathlib import Path
from database import init_db, get_item, save_item
from datetime import datetime, timedelta

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# 创建文件夹
Path("static/qr").mkdir(parents=True, exist_ok=True)
Path("static/uploads").mkdir(parents=True, exist_ok=True)
init_db()

# 生成自签名证书
def generate_self_signed_cert():
    if not Path("cert.pem").exists() or not Path("key.pem").exists():
        import subprocess
        try:
            # 尝试使用openssl生成证书
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:4096", 
                "-nodes", "-out", "cert.pem", "-keyout", "key.pem", 
                "-days", "365", "-subj", "/CN=localhost"
            ], check=True)
            print("自签名证书生成成功")
        except Exception as e:
            # 如果openssl不可用，使用Python内置模块生成
            print(f"openssl生成证书失败，尝试使用Python内置模块: {e}")
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            
            # 生成证书签名请求
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # 保存私钥
            with open("key.pem", "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            
            # 保存证书
            with open("cert.pem", "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            print("使用Python内置模块生成自签名证书成功")

# 主函数，用于直接运行时启动HTTPS服务
if __name__ == "__main__":
    import uvicorn
    import os
    
    # 配置HTTPS证书
    # 如果服务器有默认证书，取消下面两行的注释并修改为实际证书路径
    # ssl_keyfile = "/etc/ssl/private/server.key"  # Linux服务器默认证书路径示例
    # ssl_certfile = "/etc/ssl/certs/server.crt"   # Linux服务器默认证书路径示例
    
    # Windows服务器默认证书路径示例（请根据实际情况修改）
    # ssl_keyfile = "C:\\Windows\\System32\\certs\\server.key"
    # ssl_certfile = "C:\\Windows\\System32\\certs\\server.crt"
    
    # 默认使用自签名证书（如果上面的证书路径未配置）
    ssl_keyfile = "key.pem"
    ssl_certfile = "cert.pem"
    
    # 如果使用自签名证书且证书不存在，则生成
    if not (os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)):
        print("未找到指定的SSL证书，正在生成自签名证书...")
        generate_self_signed_cert()
    
    # 启动HTTPS服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )

# 电脑打开这个页面批量生成二维码
@app.get("/", response_class=HTMLResponse)
async def admin():
    return open("templates/admin.html", encoding="utf-8").read()

# 生成新二维码（返回JSON，供前端调用）
@app.get("/api/new")
def new_qr():
    item_id = str(uuid.uuid4())[:8].upper()
    url = f"https://localhost:8000/item/{item_id}"   # ←←←←← 使用HTTPS协议的本地地址
    
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