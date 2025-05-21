import numpy as np
import os
import math
import pickle
import matplotlib.pyplot as plt
from PIL import Image
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Kích thước ảnh
IMG_WIDTH, IMG_HEIGHT = 128, 128
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)
IMG_CHANNELS = 3

# Load class indices
class_indices_path = "class_indices.txt"
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
num_classes = len(class_indices)

# Xây dựng mô hình CNN tối ưu cho CPU
model = Sequential([
    Conv2D(32, (3, 3), activation="relu", padding="same", input_shape=(IMG_WIDTH, IMG_HEIGHT, IMG_CHANNELS)),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.25),

    Conv2D(64, (3, 3), activation="relu", padding="same"),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.3),

    Conv2D(128, (3, 3), activation="relu", padding="same"),
    BatchNormalization(),
    MaxPooling2D(pool_size=(2, 2)),
    Dropout(0.4),

    Flatten(),
    Dense(512, activation="relu"),
    BatchNormalization(),
    Dropout(0.5),

    Dense(num_classes, activation="softmax")
])

# Biên dịch mô hình
model.compile(loss="categorical_crossentropy", optimizer=Adam(learning_rate=0.0001), metrics=["accuracy"])

# Callbacks
earlystop = EarlyStopping(patience=5, restore_best_weights=True)
learning_rate_reduction = ReduceLROnPlateau(monitor="val_accuracy", patience=3, factor=0.5, min_lr=0.00001)
callbacks = [earlystop, learning_rate_reduction]

# Data augmentation tối ưu CPU
train_datagen = ImageDataGenerator(
    rotation_range=20,
    rescale=1.0 / 255,
    shear_range=0.2,
    zoom_range=0.3,
    horizontal_flip=True,
    width_shift_range=0.2,
    height_shift_range=0.2,
    brightness_range=[0.7,1.3],
    channel_shift_range=30,
)

train_generator = train_datagen.flow_from_directory(
    "./dogs-vs-cats/train/",
    target_size=IMG_SIZE,
    class_mode="categorical",
    batch_size=32,
    shuffle=True
)

validation_datagen = ImageDataGenerator(rescale=1.0 / 255)
validation_generator = validation_datagen.flow_from_directory(
    "./dogs-vs-cats/validation/",
    target_size=IMG_SIZE,
    class_mode="categorical",
    batch_size=32
)
# In thông tin dataset
print(f"Train samples: {train_generator.samples}")
print(f"Validation samples: {validation_generator.samples}")
print("Class mapping:", train_generator.class_indices)

# Train mô hình
if __name__ == "__main__":
    history = model.fit(
        train_generator,
        epochs=100,
        workers=4,
        validation_data=validation_generator,
        validation_freq=1,
        steps_per_epoch=math.ceil(train_generator.samples / train_generator.batch_size),
        validation_steps = math.ceil(validation_generator.samples / validation_generator.batch_size),
        callbacks=callbacks
    )
    # Load history từ file
    with open('history.pkl', 'rb') as f:
        history = pickle.load(f)

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
model.save("dog_cat_breed_classifier2.h5")
print("✅ Mô hình đã lưu thành công: dog_cat_breed_classifier2.h5")
