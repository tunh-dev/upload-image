from flask import Flask, render_template, request, url_for, jsonify
import os
from datetime import datetime
import json
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/generate', methods=['POST'])
def generate():
    urls_json = request.form.get('urls')
    try:
        urls = json.loads(urls_json)
    except:
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
            if file.filename != '':
                ext = file.filename.split('.')[-1].lower()
                filename = generate_filename(ext)

                # Đảm bảo không trùng tên
                while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                    filename = generate_filename(ext)

                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)
                image_urls.append(url_for('static', filename=f'uploads/{filename}'))

    # Load ảnh đã lưu
    for file in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        if file.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
            image_urls.append(url_for('static', filename=f'uploads/{file}'))

    return render_template('index.html', image_urls=image_urls)


@app.route('/delete', methods=['DELETE'])
def delete_image():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)