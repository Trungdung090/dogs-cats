import os
import shutil
import random

# Đường dẫn thư mục train và validation
train_dir = r"D:\Pycharm\btl\dogs-vs-cats\train"
val_dir = r"D:\Pycharm\btl\dogs-vs-cats\validation"

# Tỷ lệ validation (20%)
val_split = 0.2

# Đảm bảo thư mục validation tồn tại
os.makedirs(val_dir, exist_ok=True)

# Duyệt qua từng thư mục giống chó/mèo
for class_name in os.listdir(train_dir):
    class_path = os.path.join(train_dir, class_name)
    val_class_path = os.path.join(val_dir, class_name)

    if os.path.isdir(class_path):
        os.makedirs(val_class_path, exist_ok=True)

        # Lấy danh sách file ảnh
        images = os.listdir(class_path)
        num_val_images = int(len(images) * val_split)

        # Chọn ngẫu nhiên ảnh để đưa vào validation
        val_images = random.sample(images, num_val_images)

        for img in val_images:
            shutil.move(os.path.join(class_path, img), os.path.join(val_class_path, img))
print("✅ Validation dataset created successfully!")
