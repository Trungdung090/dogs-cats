# Dự đoán ảnh đầu vào theo mô hình phân cấp: chó/mèo → giống + tích hợp Flask API
import numpy as np
from PIL import Image
import sqlite3
import time
from datetime import datetime, date, timedelta
import threading
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from flask import (Flask, request, redirect, jsonify, render_template, send_from_directory,
                   url_for, flash, session)
from werkzeug.security import generate_password_hash, check_password_hash
import sys
import sqlite3
import cv2
import os

IMG_WIDTH, IMG_HEIGHT = 224, 224
IMAGE_SIZE = (IMG_WIDTH, IMG_HEIGHT)
IMG_CHANNELS = 3
# Danh sách lớp
DOG_CAT_CLASSES = ['dog', 'cat']
DOG_CLASSES = ['beagle', 'bulldog', 'corgi', 'pomeranian', 'poodle']
CAT_CLASSES = ['bengal', 'ragdoll', 'persian', 'british_shorthair', 'maine_coon']
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect("access_control.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        breed TEXT NOT NULL,
        confidence REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        image_path TEXT NOT NULL UNIQUE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'user'
    )''')

    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = generate_password_hash('admin')
        cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                       ('admin', admin_password, 'admin@example.com', 'admin'))
    conn.commit()
    conn.close()

# Hàm dịch tên giống sang tiếng Việt
def translate_breed(english_name):
    name_dict = {
        "beagle": "Chó Beagle",
        "bulldog": "Chó Bull",
        "corgi": "Chó Corgi",
        "pomeranian": "Chó Phốc Sóc",
        "poodle": "Chó Poodle",
        "bengal": "Mèo Bengal",
        "british_shorthair": "Mèo Anh Lông Ngắn",
        "maine_coon": "Mèo Maine Coon",
        "persian": "Mèo Ba Tư",
        "ragdoll": "Mèo Ragdoll"
    }
    return name_dict.get(english_name.lower(), english_name)

# Tải mô hình
print("⬆️ Đang tải các mô hình...")
model_dogcat = load_model("dog_cat_model.h5")
model_dog = load_model("dog_breed_model.h5")
model_cat = load_model("cat_breed_model.h5")

def preprocess_image(image_path):
    try:
        # Đọc ảnh bằng PIL
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Resize và chuẩn hóa
        img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img) / 255.0
        return img_array
    except Exception as e:
        print(f"Lỗi tiền xử lý ảnh: {str(e)}")
        raise

# Kiểm tra chất lượng ảnh
def is_valid_image(img_array, brightness_thresh=(40, 220), blur_thresh=100):
    try:
        gray = cv2.cvtColor((img_array * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        brightness = np.mean(gray)
        if brightness < brightness_thresh[0] or brightness > brightness_thresh[1]:
            print(f"Ảnh bị loại do brightness: {brightness:.2f}")
            return False
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < blur_thresh:
            print(f"Ảnh bị loại do mờ (blur): {laplacian_var:.2f}")
            return False
        return True
    except Exception as e:
        print(f"Lỗi kiểm tra ảnh: {str(e)}")
        return False

# Hàm phân loại ảnh
def classify_image(file_path):
    try:
        if not os.path.exists(file_path):
            return "error", "Ảnh không tồn tại", 0.0
        processed_image = preprocess_image(file_path)
        if not is_valid_image(processed_image):
            print("Ảnh không đủ điều kiện phân loại.")
            return "unknown", "Không xác định", 0.0
        image = np.expand_dims(processed_image, axis=0)
        # Bước 1: Chó hay mèo
        pred_dogcat = model_dogcat.predict(image, verbose=0)
        label_index = np.argmax(pred_dogcat)
        label_main = DOG_CAT_CLASSES[label_index]
        # Bước 2: Phân loại giống
        if label_main == 'dog':
            pred = model_dog.predict(image, verbose=0)
            breed_index = np.argmax(pred)
            breed_en = DOG_CLASSES[breed_index]
        else:
            pred = model_cat.predict(image, verbose=0)
            breed_index = np.argmax(pred)
            breed_en = CAT_CLASSES[breed_index]
        breed_vi = translate_breed(breed_en)
        confidence = float(np.max(pred))
        return breed_en, breed_vi, confidence
    except Exception as e:
        print(f"Lỗi khi phân loại ảnh: {str(e)}")
        return "error", "Lỗi phân loại", 0.0

# Flask app
app = Flask(__name__)
app.secret_key = 'dung'

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/classify')
def classify_page():
    return render_template('classify.html')

@app.route('/blog')
def blog_page():
    return render_template('blog.html')

@app.route('/blog_detail')
def blog_detail():
    return render_template('blog_detail.html')
# @app.route('/statistics')
# def statistics_page():
#     return render_template('statistics.html')

# @app.route('/forum')
# def forum():
#     try:
#         conn = sqlite3.connect("access_control.db")
#         cursor = conn.cursor()
#         cursor.execute('''SELECT fp.id, fp.title, fp.content, fp.image_path, fp.created_at, fp.likes,
#                           u.username FROM forum_posts fp
#                           JOIN users u ON fp.user_id = u.id
#                           ORDER BY fp.created_at DESC''')
#         posts = cursor.fetchall()
#         conn.close()
#
#         formatted_posts = []
#         for post in posts:
#             formatted_posts.append({
#                 'id': post[0], 'title': post[1], 'content': post[2],
#                 'image_path': post[3], 'created_at': post[4],
#                 'likes': post[5], 'username': post[6]
#             })
#         return render_template('forum.html', posts=formatted_posts)
#     except Exception as e:
#         return render_template('forum.html', posts=[])

# @app.route('/like_post/<int:post_id>', methods=['POST'])
# def like_post(post_id):
#     if 'user_id' not in session:
#         return jsonify({'error': 'Chưa đăng nhập'}), 401
#
#     conn = sqlite3.connect("access_control.db")
#     cursor = conn.cursor()
#     cursor.execute("UPDATE forum_posts SET likes = likes + 1 WHERE id = ?", (post_id,))
#     conn.commit()
#     conn.close()
#     return jsonify({'success': True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input  = request.form['password']
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password_input ) and user[5] == 'admin':
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[5]
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Tên đăng nhập hoặc mật khẩu không đúng!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # # Không cho phép đăng ký nếu đã có admin
    # conn = sqlite3.connect("access_control.db")
    # cursor = conn.cursor()
    # cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    # has_admin = cursor.fetchone()[0] > 0
    # conn.close()
    # if has_admin:
    #     return redirect(url_for('index'))  # Chặn truy cập
    if request.method == 'POST':
        username = request.form['username']
        password_raw = request.form['password']
        email = request.form['email']
        confirm_password = request.form['confirm_password']
        if password_raw != confirm_password:
            return render_template('register.html', error='Mật khẩu không khớp!')
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Tên đăng nhập hoặc email đã tồn tại!', 'error')
        else:
            hashed_password = generate_password_hash(password_raw)
            cursor.execute("INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)",
                           (username, hashed_password, email, created_at))
            conn.commit()
            conn.close()
            flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
            return redirect(url_for('login'))
        conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất!', 'info')
    return redirect(url_for('index'))

# @app.route('/profile')
# # @login_required
# def profile():
#     conn = sqlite3.connect("access_control.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
#     user = cursor.fetchone()
#     conn.close()
#     return render_template('profile.html', user={
#         'username': user[1],
#         'email': user[3],
#         'joined_date': user[4],
#         'avatar': user[5]
#     })

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect("access_control.db")
    cursor = conn.cursor()
    # Thống kê tổng quan
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_classifications = cursor.fetchone()[0]
    # Danh sách users
    cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    # Logs gần đây
    cursor.execute("SELECT breed, confidence, timestamp FROM logs ORDER BY timestamp DESC LIMIT 20")
    recent_logs = cursor.fetchall()
    conn.close()
    return render_template('admin.html',
                           total_users=total_users,
                           total_classifications=total_classifications,
                           users=users,
                           recent_logs=recent_logs)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'success': False, 'error': 'Không có file!'})
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'success': False, 'error': 'Chưa chọn file!'})
#     try:
#         # Lưu file gốc
#         file_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.jpg"
#         file_path = os.path.join(UPLOAD_FOLDER, file_name)
#         file.save(file_path)
#
#         # Lưu phiên bản đã tiền xử lý
#         processed_img = preprocess_image(file_path)
#         processed_img = (processed_img * 255).astype(np.uint8)
#         processed_path = os.path.join(UPLOAD_FOLDER, f"processed_{file_name}")
#         Image.fromarray(processed_img).save(processed_path)
#         return jsonify({
#             'success': True,
#             'image_name': file_name,
#             'processed_name': f"processed_{file_name}"
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})

@app.route('/classify', methods=['POST'])
def classify_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file!'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Chưa chọn file!'}), 400
    try:
        # Tạo tên file duy nhất và lưu vào static/uploads
        filename = f"classified_{int(time.time())}.jpg"
        save_path = os.path.join("static/uploads", filename)
        file.save(save_path)
        breed_en, breed_vi, confidence = classify_image(save_path)  # Phân loại
        if breed_en == "error":
            os.remove(save_path)
            return jsonify({'success': False, 'error': 'Lỗi phân loại ảnh'})
        conn = sqlite3.connect("access_control.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs (breed, confidence, timestamp, image_path)
            VALUES (?, ?, datetime('now'), ?)
        """, (breed_vi, confidence, save_path))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'breed_en': breed_en,
            'breed_vi': breed_vi,
            'confidence': round(confidence, 4)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/statistics')
def admin_statistics():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect("access_control.db")
    cursor = conn.cursor()

    # Tổng số người dùng
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Tổng số lượt phân loại
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_classifications = cursor.fetchone()[0]

    # Số lượt phân loại hôm nay
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM logs WHERE DATE(timestamp) = ?", (today,))
    today_classifications = cursor.fetchone()[0]

    # Độ chính xác trung bình
    cursor.execute("SELECT AVG(confidence) FROM logs")
    avg_accuracy = round((cursor.fetchone()[0] or 0) * 100, 2)

    # Tạo danh sách 7 ngày gần nhất
    days = [(datetime.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
    day_labels = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

    # Truy vấn số lượt phân loại theo ngày
    cursor.execute("""
        SELECT DATE(timestamp) as date_only, COUNT(*) 
        FROM logs
        WHERE DATE(timestamp) >= DATE('now', '-6 days')
        GROUP BY date_only
    """)
    raw_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Đưa dữ liệu về đủ 7 ngày
    time_activity = []
    for d in days:
        weekday = day_labels[d.weekday()] if d.weekday() != 6 else 'CN'
        time_activity.append({
            'day': weekday,
            'count': raw_counts.get(str(d), 0)
        })

    # Phân bổ giống thú cưng
    cursor.execute("""
        SELECT breed, COUNT(*) as count 
        FROM logs 
        GROUP BY breed ORDER BY count DESC LIMIT 10
    """)
    breed_distribution = [{
        'label': row[0],
        'count': row[1]
    } for row in cursor.fetchall()]

    # Hoạt động gần đây
    cursor.execute("""
        SELECT breed, confidence, timestamp 
        FROM logs 
        ORDER BY timestamp DESC LIMIT 10
    """)
    recent = [{
        'breed': row[0],
        'confidence': round(row[1], 2),
        'timestamp': row[2]
    } for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        'total_users': total_users,
        'total_classifications': total_classifications,
        'today_classifications': today_classifications,
        'avg_accuracy': avg_accuracy,
        'time_activity': time_activity,
        'breed_distribution': breed_distribution,
        'recent': recent
    })
# @app.route('/api/statistics')
# def get_statistics():
#     with sqlite3.connect("access_control.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT COUNT(*) FROM logs")
#         total = cursor.fetchone()[0]
#         cursor.execute("SELECT AVG(confidence) FROM logs")
#         avg_conf = cursor.fetchone()[0] or 0
#         cursor.execute("SELECT breed, COUNT(*) FROM logs GROUP BY breed ORDER BY COUNT(*) DESC")
#         breed_counts = cursor.fetchall()
#         popular = breed_counts[0][0] if breed_counts else "Không rõ"
#         # Lấy dữ liệu hoạt động theo ngày trong tuần
#         cursor.execute("""
#                     SELECT
#                         CASE strftime('%w', timestamp)
#                             WHEN '0' THEN 'CN'
#                             WHEN '1' THEN 'T2'
#                             WHEN '2' THEN 'T3'
#                             WHEN '3' THEN 'T4'
#                             WHEN '4' THEN 'T5'
#                             WHEN '5' THEN 'T6'
#                             WHEN '6' THEN 'T7'
#                         END as day_name,
#                         COUNT(*) as count
#                     FROM logs
#                     WHERE timestamp >= datetime('now', '-7 days')
#                     GROUP BY strftime('%w', timestamp)
#                     ORDER BY strftime('%w', timestamp)
#                 """)
#         time_activity = cursor.fetchall()
#
#         cursor.execute("""
#             SELECT breed, confidence, timestamp, image_path
#             FROM logs
#             ORDER BY timestamp DESC LIMIT 10
#         """)
#         recent = cursor.fetchall()
#     return jsonify({
#         'total': total,
#         'avg_accuracy': round(avg_conf * 100, 2),
#         'popular_breed': popular,
#         'breed_distribution': [{'label': b, 'count': c} for b, c in breed_counts],
#         'time_activity': [{'day': d, 'count': c} for d, c in time_activity],
#         'recent': [{
#             'breed': b,
#             'confidence': round(c * 100, 2),
#             'timestamp': t,
#             'image_path': '/' + p.replace('\\', '/')
#         } for b, c, t, p in recent]
#     })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
