import tkinter as tk
from tkinter import filedialog
from tkinter import *
from PIL import ImageTk, Image
import numpy as np
from tensorflow.keras.models import load_model

# Load mô hình đã train1
model = load_model('dog_cat_breed_classifier1.h5')
class_indices_path = 'class_indices.txt'

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

# Hàm đọc class_indices từ file
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

# Tạo giao diện
top = tk.Tk()
top.geometry('800x600')
top.title('Phân loại giống chó mèo')
top.configure(background='#CDCDCD')

# Label hiển thị kết quả
breed_label = Label(top, background='#CDCDCD', font=('arial', 15, 'bold'))
sign_image = Label(top)

def classify(file_path):
    image = Image.open(file_path).convert("RGB")
    image = image.resize((128, 128))  # Resize ảnh về kích thước phù hợp
    image = np.array(image) / 255.0  # Chuyển thành NumPy array và chuẩn hóa
    image = np.expand_dims(image, axis=0)  # Thêm batch dimension

    # Dự đoán ảnh
    predictions = model.predict(image)
    predicted_class = np.argmax(predictions, axis=1)[0]
    breed = class_indices.get(predicted_class, "Không xác định")
    breed_vi = tran(breed)
    breed_label.configure(foreground='#011638', text=f'Giống: {breed_vi}')

def show_classify_button(file_path):
    classify_b = Button(top, text="Phân loại", command=lambda: classify(file_path),
                        padx=10, pady=5)
    classify_b.configure(background='#364156', foreground='white',
                         font=('arial', 10, 'bold'))
    classify_b.place(relx=0.79, rely=0.46)

def upload_image():
        file_path = filedialog.askopenfilename()
        uploaded = Image.open(file_path)
        uploaded.thumbnail((top.winfo_width() / 2.25, top.winfo_height() / 2.25))

        im = ImageTk.PhotoImage(uploaded)
        sign_image.configure(image=im)
        sign_image.image = im
        breed_label.configure(text='')
        show_classify_button(file_path)

# Nút tải ảnh lên
upload = Button(top, text="Tải ảnh lên", command=upload_image, padx=10, pady=5)
upload.configure(background='#364156', foreground='black', font=('arial', 10, 'bold'))
upload.pack(side=BOTTOM, pady=50)

# Hiển thị ảnh
sign_image.pack(side=BOTTOM, expand=True)
breed_label.pack(side=BOTTOM, expand=True)

# Tiêu đề
heading = Label(top, text="Phân loại giống chó mèo", pady=20, font=('arial', 20, 'bold'))
heading.configure(background='#CDCDCD', foreground='black')
heading.pack()

top.mainloop()

