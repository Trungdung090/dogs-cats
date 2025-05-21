from PIL import ImageTk, Image
import numpy as np
import cv2
import os
import sqlite3
import threading
from datetime import datetime
from flask import Flask, render_template, send_from_directory, jsonify, request
from tensorflow.keras.models import load_model

# Load mô hình đã train
model = load_model('best_model.h5')
class_indices_path = 'class_indices.txt'
UPLOAD_FOLDER = "./uploads"  # Thư mục lưu ảnh
IMAGE_SIZE = (128, 128)  # Kích thước chuẩn cho ảnh đầu vào

# Tạo thư mục uploads nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db_worker():
    conn = sqlite3.connect("access_control.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL UNIQUE,       
        breed TEXT NOT NULL,
        image_name TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def save_log(breed, image_name):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("access_control.db")
    cursor = conn.cursor()

    # Lấy ID lớn nhất hiện tại
    cursor.execute("SELECT MAX(id) FROM logs")
    max_id = cursor.fetchone()[0]  # Lấy giá trị lớn nhất
    new_id = 1 if max_id is None else max_id + 1  # Nếu không có dữ liệu, bắt đầu từ 1
    # Chèn dữ liệu với ID mới
    cursor.execute("INSERT INTO logs (id, time, breed, image_name) VALUES (?, ?, ?, ?)",
                       (new_id, time_now, breed, image_name))
    conn.commit()
    conn.close()

# Hàm dịch tên tiếng Anh sang tiếng Việt
def tran(english_name):
    name_dict = {
        "beagle": "Chó Beagle",
        "bengal": "Mèo Bengal",
        "british_shorthair": "Mèo Anh Lông Ngắn",
        "corgi": "Chó Corgi",
        "golden_retriever": "Chó Golden Retriever",
        "husky": "Chó Husky Ngáo",
        "maine_coon": "Mèo Maine Coon",
        "pomeranian": "Chó Phốc Sóc",
        "poodle": "Chó Poodle",
        "ragdoll": "Mèo Ragdoll",
        "sphynx": "Mèo Sphynx",
        "persian": "Mèo Ba Tư",
        "siamese": "Mèo Xiêm",
        "shiba_inu": "Chó Shiba Inu"
    }
    return name_dict.get(english_name.lower(), english_name)

def load_class_indices(filepath):
    class_indices = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line or not line.strip():
                continue
            index, label = line.strip().split(":")
            class_indices[int(index)] = label
    return class_indices
class_indices = load_class_indices(class_indices_path)

def preprocess_image(image_path):
    # Tiền xử lý ảnh đầu vào với kích thước chuẩn và các bước chuẩn hóa
    # Đọc ảnh
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Chuyển BGR sang RGB

    # Giữ tỷ lệ ảnh khi resize
    h, w, _ = img.shape
    aspect = w / h

    if aspect > 1:  # Ảnh ngang
        new_w = int(IMAGE_SIZE[0] * aspect)
        resized = cv2.resize(img, (new_w, IMAGE_SIZE[1]))
        # Cắt phần giữa
        start_x = (new_w - IMAGE_SIZE[0]) // 2
        img = resized[:, start_x:start_x + IMAGE_SIZE[0], :]
    else:  # Ảnh dọc
        new_h = int(IMAGE_SIZE[1] / aspect)
        resized = cv2.resize(img, (IMAGE_SIZE[0], new_h))
        # Cắt phần giữa
        start_y = (new_h - IMAGE_SIZE[1]) // 2
        img = resized[start_y:start_y + IMAGE_SIZE[1], :, :]
    # Chuẩn hóa pixel values (0-1)
    img = img.astype(np.float32) / 255.0
    return img

def classify_image(file_path):
    # Tiền xử lý ảnh
    processed_image = preprocess_image(file_path)
    # image = Image.open(file_path).convert("RGB")
    # image = image.resize((128, 128))
    # image = np.array(image) / 255.0     # numpy array
    image = np.expand_dims(processed_image, axis=0)   # Thêm batch dimension

    pred = model.predict(image)
    predicted_class = np.argmax(pred, axis=1)[0]
    breed = class_indices.get(predicted_class, "Không xác định")
    breed_vi = tran(breed)
    return breed_vi

# Thiết lập Flask
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file!'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Chưa chọn file!'})

    file_name = f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    file.save(file_path)

    # Lưu phiên bản đã tiền xử lý để hiển thị (tùy chọn)
    processed_img = preprocess_image(file_path)
    processed_img = (processed_img * 255).astype(np.uint8)
    processed_path = os.path.join(UPLOAD_FOLDER, f"processed_{file_name}")
    cv2.imwrite(processed_path, cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR))

    return jsonify({'success': True, 'image_name': file_name})

@app.route('/classify', methods=['POST'])
def classify_file():
    data = request.get_json()
    file_name = data.get("image_name")
    if not file_name:
        return jsonify({'success': False, 'error': 'Không có file ảnh!'})
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    breed = classify_image(file_path)

    try:
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO logs (time, breed, image_name) VALUES (?, ?, ?)", (time_now, breed, file_name))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': True, 'breed': breed, 'image_name': file_name})

@app.route('/access_control')
def get_logs():
    conn = sqlite3.connect("access_control.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20")  # Lấy 20 bản ghi mới nhất
    logs = [{"id": row[0], "time": row[1], "breed": row[2], "image_name": row[3]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/stats')
def get_stats():
    conn = sqlite3.connect("access_control.db")
    cursor = conn.cursor()
    cursor.execute("SELECT breed, COUNT(*) FROM logs GROUP BY breed")
    stats = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return jsonify(stats)

@app.route('/reset_database', methods=['POST'])
def reset_database():
    try:
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")      # Xóa toàn bộ dữ liệu trong bảng logs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='logs'")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Database đã được làm mới!'})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': f'Lỗi khi reset database: {str(e)}'})

if __name__ == "__main__":
    threading.Thread(target=db_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)