# MemeMaker

一個簡單易用的 GIF 製作網站，讓你輕鬆創建有趣的動態圖片。

## 功能特點

- 上傳多張圖片製作 GIF
- 多種賽博龐克風格濾鏡效果
- 自訂 GIF 播放速度
- 添加浮水印文字
- 自動圖片優化

## 本地開發

1. 安裝所需套件：
```bash
pip install -r requirements.txt
```

2. 設定環境變數：
建立 `.env` 檔案並設定以下變數：
```env
UPLOAD_FOLDER=uploads
MAX_UPLOAD_SIZE=16777216
SECRET_KEY=your-secret-key
```

3. 執行應用程式：
```bash
python app.py
```

## 部署到 Render

1. Fork 此專案到你的 GitHub

2. 在 Render.com 建立新的 Web Service：
   - 連結你的 GitHub 儲存庫
   - 選擇 `Python` 環境
   - 使用 `Free` 方案
   - 設定環境變數：
     * `PYTHON_VERSION`: 3.12.0
     * `MAX_UPLOAD_SIZE`: 16777216
     * `SECRET_KEY`: [生成一個安全的隨機字串]

3. 部署完成後，你的應用程式將在幾分鐘內上線

## 技術細節

- 後端：Python Flask
- 圖片處理：Pillow (PIL)
- 部署：Render.com
- 字體：Orbitron (Google Fonts)

## 注意事項

- 上傳圖片大小限制：16MB
- 支援的圖片格式：PNG, JPG, JPEG, GIF
- 建議上傳相似尺寸的圖片以獲得最佳效果
