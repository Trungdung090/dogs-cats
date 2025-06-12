# Huấn luyện 2 mô hình: 1 mô hình phân loại chó/mèo, 1 mô hình phân loại chi tiết giống trong nhóm
import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from PIL import Image

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 30

def check_and_filter_images(root_dir, output_txt_path="bad_images.txt"):
    bad_images = []
    print(f"🔍 Kiểm tra ảnh lỗi trong thư mục: {root_dir}")
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            file_path = os.path.join(subdir, file)
            try:
                with Image.open(file_path) as img:
                    img.verify()  # Kiểm tra ảnh có bị hỏng
                    img.close()
                    with Image.open(file_path) as img2:
                        img2 = img2.convert("RGB")
            except Exception as e:
                print(f"⚠️ Ảnh lỗi: {file_path} ({e})")
                bad_images.append(file_path)
                os.remove(file_path)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for path in bad_images:
            f.write(path + "\n")
    print(f"✅ Hoàn tất kiểm tra ảnh. Tổng ảnh lỗi: {len(bad_images)}")
    if bad_images:
        print(f"Danh sách ảnh lỗi được lưu tại: {output_txt_path}")

# Đường dẫn đến dữ liệu
base_dir = "./dogs-vs-cats-hierarchical/"

# Kiểm tra ảnh lỗi trước khi huấn luyện
check_and_filter_images(base_dir + "dog_vs_cat")
check_and_filter_images(base_dir + "dogs_only")
check_and_filter_images(base_dir + "cats_only")

# Tạo model chung
def build_model(num_classes):
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    for layer in base_model.layers[:-10]:   # Fine-tuning
        layer.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation=None)(x)
    x = BatchNormalization()(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.1)(x)
    x = Dropout(0.3)(x)

    x = Dense(128, activation=None)(x)
    x = BatchNormalization()(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.1)(x)
    x = Dropout(0.3)(x)

    output = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=output)
    model.compile(
        optimizer=Adam(learning_rate=0.0005),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

# Data generators
def get_generators(directory, class_mode, classes):
    datagen = ImageDataGenerator(rescale=1.0 / 255, validation_split=0.2)
    train_gen = datagen.flow_from_directory(
        directory,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        classes=classes,
        class_mode=class_mode,
        subset='training'
    )
    val_gen = datagen.flow_from_directory(
        directory,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        classes=classes,
        class_mode=class_mode,
        subset='validation'
    )
    return train_gen, val_gen

print("\n=== Huấn luyện mô hình 1: Phân loại Chó / Mèo ===")
dog_cat_classes = ['dog', 'cat']
dog_cat_train, dog_cat_val = get_generators(base_dir + "dog_vs_cat", 'categorical', dog_cat_classes)
model_dc = build_model(num_classes=2)
model_dc.fit(
    dog_cat_train,
    validation_data=dog_cat_val,
    epochs=EPOCHS,
    callbacks=[
        ModelCheckpoint("dog_cat_model.h5", save_best_only=True, monitor="val_accuracy", mode="max"),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3),
        EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True)
    ]
)

print("\n=== Huấn luyện mô hình 2: Phân loại giống chó ===")
dog_classes = ['beagle', 'bulldog', 'corgi', 'pomeranian', 'poodle']
dog_train, dog_val = get_generators(base_dir + "dogs_only", 'categorical', dog_classes)
model_dog = build_model(num_classes=len(dog_classes))
model_dog.fit(
    dog_train,
    validation_data=dog_val,
    epochs=EPOCHS,
    callbacks=[
        ModelCheckpoint("dog_breed_model.h5", save_best_only=True, monitor="val_accuracy", mode="max"),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3),
        EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True)
    ]
)

print("\n=== Huấn luyện mô hình 3: Phân loại giống mèo ===")
cat_classes = ['bengal', 'ragdoll', 'persian', 'british_shorthair', 'maine_coon']
cat_train, cat_val = get_generators(base_dir + "cats_only", 'categorical', cat_classes)
model_cat = build_model(num_classes=len(cat_classes))
model_cat.fit(
    cat_train,
    validation_data=cat_val,
    epochs=EPOCHS,
    callbacks=[
        ModelCheckpoint("cat_breed_model.h5", save_best_only=True, monitor="val_accuracy", mode="max"),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3),
        EarlyStopping(monitor="val_loss", patience=7, restore_best_weights=True)
    ]
)
print("\n✅ Đã huấn luyện xong 3 mô hình phân cấp!")
