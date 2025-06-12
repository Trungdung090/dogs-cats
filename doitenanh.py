import os

folder_path = r"D:\Pycharm\btl\ảnh đã train\cho_corgi"  # Đường dẫn thư mục chứa ảnh
new_name = "corgi"   # Tên mới cho ảnh

# Lặp qua các file trong thư mục và đổi tên
for i, filename in enumerate(os.listdir(folder_path), start=1):
    if filename.endswith((".jpg", ".png", ".jpeg", ".avif")):  # Chỉ đổi tên file ảnh
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, f"{new_name}.{i}.jpg")
        os.rename(old_path, new_path)

print("Đổi tên hoàn tất!")

