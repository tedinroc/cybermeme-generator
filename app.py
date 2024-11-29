import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import io
import traceback
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 確保上傳目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/fonts', exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 賽博龐克風格的濾鏡效果
def apply_cyberpunk_filter(img):
    # 增加對比度
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    # 調整色彩
    from PIL import ImageOps
    img = ImageOps.colorize(
        ImageOps.grayscale(img),
        '#000046',  # 深藍色
        '#00ffff'   # 青色
    )
    
    return img

def add_glitch_effect(img):
    width, height = img.size
    # 創建RGB通道偏移
    r, g, b = img.split()
    
    # 隨機偏移RGB通道
    offset = 10
    r = r.transform(img.size, Image.AFFINE, (1, 0, random.randint(-offset, offset), 0, 1, 0))
    b = b.transform(img.size, Image.AFFINE, (1, 0, random.randint(-offset, offset), 0, 1, 0))
    
    # 合併通道
    return Image.merge('RGB', (r, g, b))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        files = request.files.getlist('files[]')
        duration = int(1000 / float(request.form.get('fps', 2)))  # 將 FPS 轉換為毫秒
        apply_filter = request.form.get('filter', 'none')
        add_glitch = request.form.get('glitch', 'false') == 'true'
        
        if not files or files[0].filename == '':
            return jsonify({'error': '沒有選擇檔案'}), 400

        print(f"收到 {len(files)} 個檔案")
        frames = []
        
        for file in files:
            if file and allowed_file(file.filename):
                print(f"處理檔案: {file.filename}")
                # 讀取圖片
                img = Image.open(file)
                # 轉換為 RGB 模式（如果是 RGBA，去除透明通道）
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                # 調整圖片大小以提高效能
                img = img.resize((800, int(800 * img.size[1] / img.size[0])))
                
                # 應用濾鏡效果
                if apply_filter == 'cyberpunk':
                    img = apply_cyberpunk_filter(img)
                
                # 添加故障效果
                if add_glitch:
                    img = add_glitch_effect(img)
                
                frames.append(img)
                print(f"成功處理檔案: {file.filename}")

        if not frames:
            return jsonify({'error': '沒有有效的圖片檔案'}), 400

        print(f"開始創建 GIF，幀數: {len(frames)}")
        # 創建 GIF
        gif_buffer = io.BytesIO()
        frames[0].save(
            gif_buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        gif_buffer.seek(0)
        print("GIF 創建完成")

        return send_file(
            gif_buffer,
            mimetype='image/gif',
            as_attachment=True,
            download_name='cybermeme.gif'
        )
    except Exception as e:
        error_msg = f"錯誤: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    # 本地開發時使用
    app.run(debug=True, port=8080)
else:
    # 生產環境使用
    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app.config['PREFERRED_URL_SCHEME'] = 'https'
