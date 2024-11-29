import os
from flask import Flask, request, render_template, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps, ImageFilter
import io
import traceback
import random
import numpy as np
from datetime import datetime
import base64
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# 配置上傳設定
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 預設 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SECRET_KEY=os.getenv('SECRET_KEY', os.urandom(24).hex())
)

# 確保上傳目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/fonts', exist_ok=True)

# 下載字體（如果不存在）
FONT_PATH = 'static/fonts/Orbitron-Bold.ttf'
if not os.path.exists(FONT_PATH):
    import requests
    font_url = "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron-Bold.ttf"
    response = requests.get(font_url)
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
    with open(FONT_PATH, 'wb') as f:
        f.write(response.content)

def compress_image(img, max_size_kb=500):
    """壓縮圖片到指定大小"""
    quality = 95
    img_buffer = io.BytesIO()
    
    while quality > 5:
        img_buffer.seek(0)
        img_buffer.truncate()
        img.save(img_buffer, format='JPEG', quality=quality)
        if img_buffer.tell() / 1024 <= max_size_kb:
            break
        quality -= 5
    
    img_buffer.seek(0)
    return Image.open(img_buffer)

def add_watermark(img, text, position='bottom'):
    """添加浮水印文字"""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # 根據圖片大小調整字體大小
    font_size = int(width * 0.05)  # 圖片寬度的 5%
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()
    
    # 計算文字大小
    text_width = draw.textlength(text, font=font)
    text_height = font_size
    
    # 設定文字位置
    padding = 20
    if position == 'top':
        text_position = ((width - text_width) // 2, padding)
    elif position == 'bottom':
        text_position = ((width - text_width) // 2, height - text_height - padding)
    else:  # center
        text_position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # 添加文字陰影效果
    shadow_offset = 2
    # 繪製陰影
    draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset),
              text, font=font, fill='black')
    # 繪製主要文字
    draw.text(text_position, text, font=font, fill='#00ffff')  # 使用青色
    
    return img

# 賽博龐克風格的濾鏡效果
def apply_cyberpunk_filter(img, style='neon'):
    """應用不同的賽博龐克風格濾鏡"""
    if style == 'none':
        return img
        
    if style == 'neon':
        # 增加對比度和飽和度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.8)
        
        # 調整色彩
        img = ImageOps.colorize(
            ImageOps.grayscale(img),
            '#000046',  # 深藍色
            '#00ffff'   # 青色
        )
    
    elif style == 'matrix':
        # Matrix風格：綠色色調
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        img = ImageOps.colorize(
            ImageOps.grayscale(img),
            '#001100',  # 深綠
            '#00ff00'   # 亮綠
        )

    elif style == 'vaporwave':
        # 蒸氣波風格：粉紫色調
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.5)
        r, g, b = img.split()
        r = r.point(lambda x: x * 1.2)
        b = b.point(lambda x: x * 1.1)
        img = Image.merge('RGB', (r, g, b))
        
    elif style == 'retro':
        # 復古風格：褪色效果
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.7)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        img = img.filter(ImageFilter.SMOOTH)
        
    elif style == 'glitch':
        # 故障藝術風格
        img = add_glitch_effect(img)
        
    return img

def add_glitch_effect(img):
    """添加故障效果"""
    # 轉換為numpy數組
    img_array = np.array(img)
    
    # 隨機選擇區域進行位移
    for _ in range(random.randint(5, 10)):
        x1 = random.randint(0, img_array.shape[0] - 50)
        x2 = x1 + random.randint(10, 50)
        y1 = random.randint(0, img_array.shape[1] - 50)
        y2 = y1 + random.randint(10, 50)
        
        # 隨機位移
        offset = random.randint(-20, 20)
        if x2 + offset < img_array.shape[0]:
            img_array[x1:x2, y1:y2] = np.roll(img_array[x1:x2, y1:y2], offset, axis=0)
    
    # 隨機添加RGB通道偏移
    channels = []
    for i in range(3):
        channel = img_array[:, :, i]
        offset = random.randint(-5, 5)
        channels.append(np.roll(channel, offset))
    
    img_array = np.dstack(channels)
    return Image.fromarray(img_array)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(img, target_size=(800, 800)):
    """智能調整圖片尺寸，保持比例並添加背景填充"""
    # 獲取原始尺寸
    original_width, original_height = img.size
    
    # 計算目標尺寸，保持比例
    target_width, target_height = target_size
    aspect_ratio = original_width / original_height
    
    if aspect_ratio > 1:
        # 寬圖片
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        # 高圖片
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    # 調整圖片大小
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 創建新的背景圖片
    background = Image.new('RGB', target_size, (0, 0, 0))  # 黑色背景
    
    # 計算貼上位置（置中）
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    
    # 貼上調整後的圖片
    background.paste(img, (paste_x, paste_y))
    
    return background

def process_image(img, filter_style='neon', watermark='', target_size=(800, 800)):
    """處理單張圖片：調整大小、添加濾鏡和浮水印"""
    try:
        # 確保圖片為 RGB 模式
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 調整圖片大小並保持比例
        img = resize_image(img, target_size)
        
        # 應用濾鏡效果
        img = apply_cyberpunk_filter(img, filter_style)
        
        # 添加浮水印
        if watermark:
            img = add_watermark(img, watermark)
        
        return img
    except Exception as e:
        print(f"圖片處理錯誤: {str(e)}")
        traceback.print_exc()
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        files = request.files.getlist('files[]')
        if not files or not files[0].filename:
            return jsonify({'error': '請選擇至少一個圖片檔案'}), 400

        # 取得參數
        fps = float(request.form.get('fps', 2))
        filter_style = request.form.get('filter', 'none')
        watermark_text = request.form.get('watermark', '')
        watermark_position = request.form.get('position', 'bottom')
        
        # 處理所有圖片
        processed_images = []
        for file in files:
            if file and allowed_file(file.filename):
                # 讀取圖片
                img = Image.open(file)
                
                # 確保圖片是 RGB 模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 調整圖片大小
                img = resize_image(img)
                
                # 應用濾鏡效果
                if filter_style != 'none':
                    img = apply_cyberpunk_filter(img, filter_style)
                
                # 添加浮水印
                if watermark_text:
                    img = add_watermark(img, watermark_text, watermark_position)
                
                processed_images.append(img)
            else:
                return jsonify({'error': '不支援的檔案格式'}), 400

        if not processed_images:
            return jsonify({'error': '沒有可處理的圖片'}), 400

        # 生成唯一的檔案名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        output_filename = f'cybermeme_{timestamp}_{random_str}.gif'

        # 創建 GIF
        output = io.BytesIO()
        
        # 確保所有圖片大小一致
        first_size = processed_images[0].size
        for i in range(1, len(processed_images)):
            if processed_images[i].size != first_size:
                processed_images[i] = processed_images[i].resize(first_size, Image.Resampling.LANCZOS)

        # 保存 GIF
        try:
            processed_images[0].save(
                output,
                format='GIF',
                save_all=True,
                append_images=processed_images[1:],
                duration=int(1000/fps),  # 轉換 FPS 為毫秒
                loop=0,
                optimize=False,  # 關閉優化以避免顏色問題
                quality=100      # 最高品質
            )
        except Exception as e:
            print(f"GIF 生成錯誤: {str(e)}")
            # 嘗試使用備用方法
            processed_images[0].save(
                output,
                format='GIF',
                save_all=True,
                append_images=processed_images[1:],
                duration=int(1000/fps),
                loop=0,
                optimize=True,
                quality=95
            )
        
        output.seek(0)

        # 設定回應標頭
        response = make_response(output.getvalue())
        response.headers.set('Content-Type', 'image/gif')
        response.headers.set('Content-Disposition', 'attachment; filename=' + output_filename)

        return response

    except Exception as e:
        error_msg = f"生成錯誤: {str(e)}"
        print(f"詳細錯誤: {traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@app.route('/preview', methods=['POST'])
def preview_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        file = request.files['file']
        filter_style = request.form.get('filter', 'none')
        watermark_text = request.form.get('watermark', '')
        watermark_position = request.form.get('position', 'bottom')
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': '無效的檔案格式'}), 400

        # 讀取並處理圖片
        img = Image.open(file)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # 調整圖片大小
        img = resize_image(img)
        
        # 應用濾鏡效果
        if filter_style != 'none':
            img = apply_cyberpunk_filter(img, filter_style)
        
        # 添加浮水印
        if watermark_text:
            img = add_watermark(img, watermark_text, watermark_position)
        
        # 將處理後的圖片轉換為 base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'preview': f'data:image/jpeg;base64,{img_str}'
        })
        
    except Exception as e:
        error_msg = f"預覽錯誤: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/preview-gif', methods=['POST'])
def preview_gif():
    try:
        print("開始處理 GIF 預覽請求")
        if 'files[]' not in request.files:
            print("錯誤：沒有找到上傳的檔案")
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        files = request.files.getlist('files[]')
        print(f"收到 {len(files)} 個檔案")
        if not files or not files[0].filename:
            print("錯誤：檔案列表為空或第一個檔案沒有檔名")
            return jsonify({'error': '請選擇至少一個圖片檔案'}), 400

        # 取得參數
        fps = float(request.form.get('fps', 2))
        filter_style = request.form.get('filter', 'none')
        watermark_text = request.form.get('watermark', '')
        watermark_position = request.form.get('position', 'bottom')
        
        print(f"參數: fps={fps}, filter={filter_style}, watermark={watermark_text}, position={watermark_position}")
        
        # 處理所有圖片
        processed_images = []
        for index, file in enumerate(files):
            print(f"處理第 {index + 1} 張圖片: {file.filename}")
            if file and allowed_file(file.filename):
                try:
                    img = Image.open(file)
                    print(f"圖片模式: {img.mode}, 大小: {img.size}")
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # 調整圖片大小
                    img = resize_image(img)
                    print(f"調整後大小: {img.size}")
                    
                    # 應用濾鏡效果
                    if filter_style != 'none':
                        print(f"正在應用濾鏡: {filter_style}")
                        img = apply_cyberpunk_filter(img, filter_style)
                    
                    # 添加浮水印
                    if watermark_text:
                        print(f"添加浮水印: {watermark_text}")
                        img = add_watermark(img, watermark_text, watermark_position)
                    
                    processed_images.append(img)
                    print(f"第 {index + 1} 張圖片處理完成")
                except Exception as img_error:
                    print(f"處理圖片時發生錯誤: {str(img_error)}")
                    return jsonify({'error': f'處理圖片 {file.filename} 時發生錯誤: {str(img_error)}'}), 500
            else:
                print(f"不支援的檔案格式: {file.filename}")
                return jsonify({'error': '不支援的檔案格式'}), 400

        if not processed_images:
            print("錯誤：沒有可處理的圖片")
            return jsonify({'error': '沒有可處理的圖片'}), 400

        print(f"開始生成 GIF，共 {len(processed_images)} 張圖片")
        # 創建 GIF
        output = io.BytesIO()
        try:
            processed_images[0].save(
                output,
                format='GIF',
                save_all=True,
                append_images=processed_images[1:],
                duration=int(1000/fps),  # 轉換 FPS 為毫秒
                loop=0
            )
            print("GIF 生成完成")
            output.seek(0)
            
            # 轉換為 base64
            gif_base64 = base64.b64encode(output.getvalue()).decode()
            print("Base64 轉換完成")
            
            return jsonify({
                'preview': f'data:image/gif;base64,{gif_base64}'
            })
        except Exception as gif_error:
            print(f"生成 GIF 時發生錯誤: {str(gif_error)}")
            return jsonify({'error': f'生成 GIF 時發生錯誤: {str(gif_error)}'}), 500
        
    except Exception as e:
        error_msg = f"預覽生成錯誤: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/generate-gif', methods=['POST'])
def generate_gif():
    """生成最終的 GIF 檔案"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': '未找到上傳的檔案'}), 400

        files = request.files.getlist('files[]')
        if not files or not any(file.filename for file in files):
            return jsonify({'error': '請選擇至少一個檔案'}), 400

        # 獲取參數
        filter_style = request.form.get('filter', 'none')
        speed = int(request.form.get('speed', '800'))
        watermark = request.form.get('watermark', '')

        # 先讀取所有圖片以確定最大尺寸
        images = []
        max_width = 0
        max_height = 0
        for file in files:
            if file and allowed_file(file.filename):
                img = Image.open(file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
                max_width = max(max_width, img.size[0])
                max_height = max(max_height, img.size[1])

        if not images:
            return jsonify({'error': '沒有可處理的圖片'}), 400

        # 設定目標尺寸為最大圖片的尺寸
        target_size = (max_width, max_height)

        # 處理每個圖片
        processed_images = []
        for img in images:
            # 調整大小並保持比例
            img = resize_image(img, target_size)
            
            # 應用濾鏡效果
            if filter_style != 'none':
                img = apply_cyberpunk_filter(img, filter_style)
            
            # 添加浮水印
            if watermark:
                img = add_watermark(img, watermark)
            
            processed_images.append(img)

        # 創建 GIF
        output = io.BytesIO()
        processed_images[0].save(
            output,
            format='GIF',
            save_all=True,
            append_images=processed_images[1:],
            duration=speed,
            loop=0,
            optimize=True
        )
        output.seek(0)

        # 轉換為 base64
        gif_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
        
        return jsonify({
            'preview': f'data:image/gif;base64,{gif_base64}',
            'message': 'GIF 生成成功'
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'生成 GIF 時發生錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
