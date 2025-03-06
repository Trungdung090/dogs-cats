import tkinter as tk
from tkinter import filedialog
from tkinter import *
from PIL import ImageTk, Image
import numpy as np
import cv2
import os
import sqlite3
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, send_from_directory, jsonify, request
from tensorflow.keras.models import load_model

# Load mô hình đã train
model = load_model('dog_cat_breed_classifier1.h5')
class_indices_path = 'class_indices.txt'
UPLOAD_FOLDER = "./uploads"  # Thư mục lưu ảnh
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
        "abyssinian": "Mèo Abyssinian",
        "shiba_inu": "Chó Shiba Inu",
        "samoyed": "Chó Samoyed"
    }
    return name_dict.get(english_name.lower(), english_name)

def load_class_indices(filepath):
    class_indices = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    index, label = parts
                    class_indices[int(index)] = label.strip()
    except Exception as e:
        print(f"Lỗi đọc class_indices: {e}")
    return class_indices

class_indices = load_class_indices(class_indices_path)

def classify_image(file_path):
    image = Image.open(file_path).convert("RGB")
    image = image.resize((128, 128))
    image = np.array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    predictions = model.predict(image)
    predicted_class = np.argmax(predictions, axis=1)[0]
    breed = class_indices.get(predicted_class, "Không xác định")
    breed_vi = tran(breed)
    return breed_vi

# Thiết lập Flask
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index1.html')

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

@app.route('/reset_database', methods=['POST'])
def reset_database():
    try:
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")  # Xóa toàn bộ dữ liệu trong bảng logs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='logs'")
        #cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Database đã được làm mới!'})
    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': f'Lỗi khi reset database: {str(e)}'})

if __name__ == "__main__":
    threading.Thread(target=db_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)