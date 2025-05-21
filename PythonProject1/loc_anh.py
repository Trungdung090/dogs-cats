import os
import cv2
import imagehash
import numpy as np
from PIL import Image

def phash_image(image_path):
    """Tính toán perceptual hash của một ảnh"""
    try:
        img = Image.open(image_path)
        return imagehash.phash(img)
    except Exception as e:
        print(f"Lỗi xử lý ảnh {image_path}: {e}")
        return None

def find_duplicate_images(folder_path):
    """Tìm các ảnh trùng lặp trong thư mục"""
    hash_dict = {}
    duplicate_images = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if not os.path.isfile(file_path):
            continue  # Bỏ qua nếu không phải file

        img_hash = phash_image(file_path)
        if img_hash is None:
            continue

        if img_hash in hash_dict:
            duplicate_images.append(file_path)
        else:
            hash_dict[img_hash] = file_path

    return duplicate_images

def delete_duplicates(duplicate_images):
    """Xóa các ảnh trùng lặp"""
    for img_path in duplicate_images:
        os.remove(img_path)
        print(f"Đã xóa: {img_path}")

if __name__ == "__main__":
    folder = r"D:\Pycharm\btl\ảnh đã train\cho_corgi"  # Thay bằng đường dẫn thư mục ảnh của bạn
    duplicates = find_duplicate_images(folder)

    if duplicates:
        print("Các ảnh trùng lặp được tìm thấy:")
        for dup in duplicates:
            print(dup)

        delete_duplicates(duplicates)
    else:
        print("Không tìm thấy ảnh trùng lặp.")
