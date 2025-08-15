from flask import Flask, render_template, request, url_for, jsonify, redirect
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
        descriptions = request.form.getlist('descriptions')
        for i, file in enumerate(files):
            if file.filename != '':
                ext = file.filename.split('.')[-1].lower()
                filename = generate_filename(ext)
                description = descriptions[i] if i < len(descriptions) else ""
                save_metadata(filename, description)

                # Đảm bảo không trùng tên
                while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                    filename = generate_filename(ext)

                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)
                metadata = load_metadata()
                image_urls.append({
                    'url': url_for('static', filename=f'uploads/{file}'),
                    'description': metadata.get(file, '')
                })

    # Load ảnh đã lưu
    for file in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        if file.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
            metadata = load_metadata()
            image_urls.append({
                'url': url_for('static', filename=f'uploads/{file}'),
                'description': metadata.get(file, '')
            })

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


def save_metadata(filename, description):
    metadata_path = os.path.join(UPLOAD_FOLDER, 'metadata.json')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}

    data[filename] = description
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_metadata():
    metadata_path = os.path.join(UPLOAD_FOLDER, 'metadata.json')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


@app.route('/update-description', methods=['POST'])
def update_description():
    data = request.get_json()
    filename = data.get('filename')
    new_description = data.get('description')

    if not filename:
        return jsonify({'error': 'Thiếu filename'}), 400

    metadata_path = os.path.join(UPLOAD_FOLDER, 'metadata.json')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except:
        metadata = {}

    if filename not in metadata:
        return jsonify({'error': 'Ảnh không tồn tại trong metadata'}), 404

    metadata[filename] = new_description
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return jsonify({'status': 'success'})


@app.route('/back', methods=['GET'])
def go_back():
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
