# تثبيت المكتبات المطلوبة
# !pip install rembg pillow flask flask-cors opencv-python numpy

from flask import Flask, request, send_file, render_template_string
from flask_cors import CORS
from rembg import remove
from PIL import Image, ImageEnhance, ImageOps
import io
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# واجهة المستخدم HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Product Studio</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
        input, button { margin: 20px; padding: 10px; font-size: 16px; cursor: pointer; }
        img { margin-top: 20px; max-width: 90%; border: 1px solid #ccc; }
        a { display:block; margin-top: 10px; font-weight:bold; }
    </style>
</head>
<body>
    <h1>AI Product Studio</h1>
    <p>ارفع صورة منتجك لتحصل على نسخة احترافية 4K جاهزة للإعلانات</p>
    <input type="file" id="upload" accept="image/*"><br>
    <button id="processBtn">تحويل الصورة</button><br>
    <img id="result" src=""><br>
    <a id="downloadLink" href="" download="product_final.png" style="display:none;">تحميل الصورة بجودة عالية</a>
    <script>
        const upload = document.getElementById('upload');
        const result = document.getElementById('result');
        const processBtn = document.getElementById('processBtn');
        const downloadLink = document.getElementById('downloadLink');

        processBtn.addEventListener('click', async () => {
            if(upload.files.length === 0) { alert("اختر صورة أولاً!"); return; }
            const file = upload.files[0];
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch('/process_image', { method: 'POST', body: formData });
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            result.src = url;
            downloadLink.href = url;
            downloadLink.style.display = "inline";
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/process_image", methods=["POST"])
def process_image():
    try:
        file = request.files['file']
        img_data = file.read()

        # إزالة الخلفية
        img_no_bg = remove(img_data)
        img = Image.open(io.BytesIO(img_no_bg)).convert("RGBA")

        # تحسين الألوان والإضاءة
        img = ImageEnhance.Color(img).enhance(1.4)
        img = ImageEnhance.Contrast(img).enhance(1.35)
        img = ImageEnhance.Brightness(img).enhance(1.25)

        # إضافة خلفية بيضاء احترافية
        bg = Image.new("RGBA", img.size, (255,255,255,255))
        img = Image.alpha_composite(bg, img)

        # إضافة ظل خفيف لإحساس العمق
        shadow = Image.new("RGBA", img.size, (0,0,0,0))
        shadow_offset = max(img.size)//50  # حجم الظل بالنسبة للصورة
        shadow_mask = Image.new("L", img.size, 0)
        shadow_mask = ImageOps.expand(shadow_mask, border=shadow_offset, fill=120)
        shadow.putalpha(shadow_mask)
        img = Image.alpha_composite(shadow, img)

        # تحويل PIL إلى OpenCV لرفع الجودة إلى تقريبًا 4K
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)
        scale_factor = 2.5  # تكبير الصورة للحصول على جودة عالية
        width = int(cv_img.shape[1] * scale_factor)
        height = int(cv_img.shape[0] * scale_factor)
        cv_img_resized = cv2.resize(cv_img, (width, height), interpolation=cv2.INTER_CUBIC)

        # تحويل مرة أخرى إلى PIL
        img_final = Image.fromarray(cv2.cvtColor(cv_img_resized, cv2.COLOR_BGRA2RGBA))

        # حفظ الصورة في الذاكرة
        output = io.BytesIO()
        img_final.save(output, format="PNG", quality=100)
        output.seek(0)
        return send_file(output, mimetype='image/png')

    except Exception as e:
        return f"حدث خطأ: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
