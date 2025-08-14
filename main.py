from flask import Flask, render_template, request, url_for, jsonify, redirect, send_from_directory, abort
import os
from datetime import datetime
import json
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Cho phép override bằng biến môi trường
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Chặn truy cập ra ngoài thư mục upload
    safe_name = os.path.basename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name)

@app.route('/generate', methods=['POST'])
def generate():
    urls_json = request.form.get('urls')
    try:
        urls = json.loads(urls_json)
    except Exception:
        urls = []
    return render_template('generate.html', urls=urls)

def generate_filename(ext):
    now = datetime.now()
    date_part = now.strftime('%d%m%Y')
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    delta_ms = int((now - midnight).total_seconds() * 1000)
    return f"{date_part}_{delta_ms}.{ext}"

@app.route('/', methods=['GET', 'POST'])
def index():
    image_urls = []

    if request.method == 'POST':
        files = request.files.getlist('images')
        for file in files:
            if not file or file.filename == '':
                continue

            original = secure_filename(file.filename)
            ext = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
            if not allowed_file(original):
                continue  # hoặc trả lỗi 400

            filename = generate_filename(ext)

            # Đảm bảo không trùng tên
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                filename = generate_filename(ext)

            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            # Tạo URL đúng route phục vụ uploads
            image_urls.append(url_for('uploaded_file', filename=filename))

    # Load ảnh đã lưu
    for fname in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        if fname.lower().endswith(tuple(ALLOWED_EXTS)):
            image_urls.append(url_for('uploaded_file', filename=fname))

    return render_template('index.html', image_urls=image_urls)

@app.route('/delete', methods=['DELETE'])
def delete_image():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    # Chỉ cho phép xóa theo basename để tránh ../
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    # Đảm bảo file nằm trong thư mục upload
    try:
        if not os.path.realpath(file_path).startswith(os.path.realpath(UPLOAD_FOLDER) + os.sep):
            return jsonify({"error": "Invalid path"}), 400
    except Exception:
        return jsonify({"error": "Invalid path"}), 400

    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "File not found"}), 404

@app.route("/generate-test-script", methods=["POST"])
def generate_test_script():
    data = request.get_json()
    try:
        res = requests.post(
            "http://14.225.36.82:5000/get-test-scenario",
            json={
                "images": data.get("images", []),
                "action": data.get("action", "")
            },
            headers={"Content-Type": "application/json"}
        )
        res_json = res.json()
        content_list = res_json.get('content', [])
        return "\n".join(content_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/back', methods=['GET'])
def go_back():
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
