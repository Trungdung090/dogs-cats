import numpy as np
import pandas as pd
from keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import os
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense, BatchNormalization
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.optimizers import Adam
import imghdr

# Định dạng lại ảnh đầu vào
Image_Width, Image_Height = 64, 64
Image_Size = (Image_Width, Image_Height)
Image_Channels = 3

# Hàm kiểm tra ảnh hợp lệ
def is_valid_image(file_path):
    return imghdr.what(file_path) is not None

# Tải danh sách giống chó mèo
class_indices_path = 'class_indices.txt'
def load_class_indices(filepath):
    class_indices = {}
    with open(filepath, 'r', encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if ":" not in line or not line:
                continue
            index, label = line.strip().split(':')
            class_indices[int(index)] = label
    return class_indices
class_indices = load_class_indices(class_indices_path)
num_classes = len(class_indices)  # Sử dụng số lớp từ class_indices.txt

# Lấy dữ liệu train
image_dir = r"D:\Pycharm\btl\dogs-vs-cats\train1"
filenames = [f for f in os.listdir(image_dir) if is_valid_image(os.path.join(image_dir, f))]
categories = [filename.split('.')[0] for filename in filenames]
df = pd.DataFrame({'filename': filenames, 'category': categories})
df = df[df['category'].isin(class_indices.values())]  # Chỉ lấy ảnh có nhãn hợp lệ

# Chia tập train và validation
train_df, validate_df = train_test_split(df, test_size=0.2, random_state=42)
train_df = train_df.reset_index(drop=True)
validate_df = validate_df.reset_index(drop=True)

# Khởi tạo mô hình CNN
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(Image_Width, Image_Height, Image_Channels)),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.25),

    Conv2D(64, (3, 3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.3),

    Conv2D(128, (3, 3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.4),

    Flatten(),
    Dense(512, activation='relu'),
    BatchNormalization(),
    Dropout(0.5),

    Dense(num_classes, activation='softmax')
])

# Biên dịch mô hình
model.compile(loss='categorical_crossentropy', optimizer=Adam(learning_rate=0.0001), metrics=['accuracy'])

# Callbacks
earlystop = EarlyStopping(patience=5)
learning_rate_reduction = ReduceLROnPlateau(monitor='val_accuracy', patience=2, verbose=1, factor=0.5, min_lr=0.00001)
callbacks = [earlystop, learning_rate_reduction]

# Data augmentation
train_datagen = ImageDataGenerator(rotation_range=20,
                                   rescale=1. / 255,
                                   shear_range=0.2,
                                   zoom_range=0.3,
                                   horizontal_flip=True,
                                   width_shift_range=0.2,
                                   height_shift_range=0.2,
                                   brightness_range=[0.7, 1.3],
                                   channel_shift_range=30,
                                   )

train_generator = train_datagen.flow_from_dataframe(train_df,
                                                    "./dogs-vs-cats/train1/",
                                                    x_col='filename',
                                                    y_col='category',
                                                    target_size=Image_Size,
                                                    class_mode='categorical',
                                                    batch_size=20,
                                                    shuffle=True,
                                                    )

validation_datagen = ImageDataGenerator(rescale=1. / 255)
validation_generator = validation_datagen.flow_from_dataframe(validate_df,
                                                              "./dogs-vs-cats/train1/",
                                                              x_col='filename',
                                                              y_col='category',
                                                              target_size=Image_Size,
                                                              class_mode='categorical',
                                                              batch_size=20)

if __name__ == "__main__":
    history = model.fit(
        train_generator,
        epochs=100,
        validation_data=validation_generator,
        steps_per_epoch=len(train_df) // 20,
        validation_steps=len(validate_df) // 20,
        callbacks=callbacks
    )

    # Vẽ biểu đồ loss và accuracy
    plt.figure(figsize=(12, 5))

    # Loss plot
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Train vs Validation Loss')
    plt.legend()

    # Accuracy plot
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Train vs Validation Accuracy')
    plt.legend()
    plt.show()

# Lưu mô hình
model.save("dog_cat_breed_classifier.h5")
print("✅ Mô hình đã lưu thành công: dog_cat_breed_classifier.h5")



