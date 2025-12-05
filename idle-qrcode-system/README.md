# 空闲物品二维码管理系统

这是一个基于 FastAPI 开发的空闲物品二维码管理系统，用于批量生成物品二维码，并通过扫描二维码快速查看和编辑物品信息。

## 项目功能

- **批量生成二维码**：支持单次或批量生成物品二维码
- **物品信息管理**：通过扫描二维码查看和编辑物品信息，包括名称、存放位置、日期、负责人、备注等
- **照片上传**：支持为物品上传照片
- **二维码下载**：可将所有生成的二维码打包为 ZIP 文件下载
- **数据持久化**：使用 SQLite 数据库存储物品信息

## 技术栈

- **后端**：FastAPI
- **前端**：Vue 3 + Element Plus
- **数据库**：SQLite
- **二维码生成**：Segno (用于生成高清二维码)、qrcode
- **模板引擎**：Jinja2

## 安装步骤

### 1. 克隆项目

```bash
git clone <项目地址>
cd idle-qrcode-system
```

### 2. 安装依赖

使用 pip 安装项目所需依赖：

```bash
pip install -r requirements.txt
```

### 3. 配置项目

编辑 `main.py` 文件，修改域名配置：

```python
# 生成新二维码（返回JSON，供前端调用）
@app.get("/api/new")
def new_qr():
    item_id = str(uuid.uuid4())[:8].upper()
    url = f"https://你的域名.com/item/{item_id}"   # ←←←←← 修改为你的域名或服务器地址
    
    # 生成超高清二维码（适合喷码）
    qr = segno.make(url, error='H')
    qr.save(f"static/qr/{item_id}.png", scale=20, border=2, dark="#000000")
    
    return {
        "id": item_id,
        "url": url,
        "qr_png": f"/static/qr/{item_id}.png"
    }
```

### 4. 启动服务

使用 uvicorn 启动 FastAPI 服务：

```bash
uvicorn main:app --reload
```

默认情况下，服务将在 `http://127.0.0.1:8000` 启动。

## 使用方法

### 1. 批量生成二维码

在浏览器中打开 `http://127.0.0.1:8000`，进入管理界面：

- 点击「生成一个新二维码」按钮生成单个二维码
- 点击「生成10个」按钮批量生成10个二维码
- 点击「下载全部二维码ZIP」按钮将所有生成的二维码打包下载

### 2. 查看和编辑物品信息

使用手机或其他设备扫描生成的二维码，将打开物品信息编辑页面：

- 填写物品名称、存放位置、日期、负责人、备注等信息
- 点击「选择文件」上传物品照片
- 点击「保存信息」按钮保存所有修改

## 项目结构

```
idle-qrcode-system/
├── __pycache__/          # Python 编译文件
├── static/               # 静态文件目录
│   ├── qr/               # 生成的二维码图片
│   └── uploads/          # 上传的物品照片
├── templates/            # HTML 模板文件
│   ├── admin.html        # 管理界面模板
│   └── index.html        # 物品信息页面模板
├── database.py           # 数据库操作模块
├── items.db              # SQLite 数据库文件
├── main.py               # 主应用文件
├── requirements.txt      # 项目依赖
└── README.md             # 项目说明文档
```

## API 接口说明

### 1. 管理界面

- **GET /**：返回管理界面，用于批量生成二维码

### 2. 生成二维码

- **GET /api/new**：生成新的二维码并返回相关信息
  - 返回格式：
    ```json
    {
      "id": "物品ID",
      "url": "二维码链接",
      "qr_png": "/static/qr/物品ID.png"
    }
    ```

### 3. 物品信息页面

- **GET /item/{item_id}**：返回指定物品的信息页面

### 4. 保存物品信息

- **POST /item/{item_id}**：保存物品信息
  - 请求参数：
    - name：物品名称
    - location：存放位置
    - buy_date：日期
    - owner：负责人
    - remark：备注
    - photo：物品照片（可选）

### 5. 下载所有二维码

- **GET /download_all**：将所有生成的二维码打包为 ZIP 文件下载

## 注意事项

1. 首次运行时会自动创建数据库文件和必要的文件夹
2. 生成的二维码图片和上传的照片会分别保存在 `static/qr/` 和 `static/uploads/` 目录中
3. 建议在生产环境中配置适当的访问权限和安全措施
4. 如果需要修改二维码尺寸或样式，可以在 `main.py` 中调整相关参数

## 许可证

[MIT License](LICENSE)