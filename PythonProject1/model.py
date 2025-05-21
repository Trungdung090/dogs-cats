import numpy as np
import os
import math
import matplotlib.pyplot as plt
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # Khắc phục tạm thời xung đột OpenMP
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import tensorflow as tf

# Kiểm tra và thiết lập số lượng thread cho CPU
num_cores = os.cpu_count()
print(f"Số lượng CPU cores: {num_cores}")
tf.config.threading.set_inter_op_parallelism_threads(num_cores)
tf.config.threading.set_intra_op_parallelism_threads(num_cores)
print("Đã tối ưu cấu hình threading cho CPU")

# Kích thước ảnh (nhỏ hơn để phù hợp với CPU)
IMG_WIDTH, IMG_HEIGHT = 224, 224
IMG_SIZE = (IMG_WIDTH, IMG_HEIGHT)
IMG_CHANNELS = 3

# Batch size nhỏ hơn để phù hợp với CPU
BATCH_SIZE = 16

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
print(f"Phân loại {num_classes} lớp: {list(class_indices.values())}")

# Đường dẫn dữ liệu
train_dir = "./dogs-vs-cats/train/"
val_dir = "./dogs-vs-cats/validation/"

# Data augmentation nâng cao
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    brightness_range=[0.8, 1.2],
    channel_shift_range=30,
)

# Preprocessing cho validation set
val_datagen = ImageDataGenerator(rescale=1.0 / 255)

# Tạo generators
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

validation_generator = val_datagen.flow_from_directory(
    val_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False  # Không shuffle validation để có kết quả đánh giá nhất quán
)

# Số bước mỗi epoch
steps_per_epoch = math.ceil(train_generator.samples / BATCH_SIZE)
validation_steps = math.ceil(validation_generator.samples / BATCH_SIZE)

print(f"Train samples: {train_generator.samples}, Validation samples: {validation_generator.samples}")
print(f"Steps per epoch: {steps_per_epoch}, Validation steps: {validation_steps}")

# Sử dụng MobileNetV2 làm backbone - nhẹ hơn và hiệu quả hơn cho CPU
def build_model():
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=(IMG_WIDTH, IMG_HEIGHT, IMG_CHANNELS)
    )

    # Freeze các layer cơ sở, chỉ mở khóa 10 layer cuối để fine-tuning
    for layer in base_model.layers[:-10]:
        layer.trainable = False

    # Thông báo các layer có thể đào tạo
    trainable_layers = sum(1 for layer in base_model.layers if layer.trainable)
    total_layers = len(base_model.layers)
    print(f"Fine-tuning {trainable_layers}/{total_layers} layers của MobileNetV2")

    # Xây dựng classifier head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)

    # Thêm dense layers với batch normalization
    x = Dense(256, activation=None)(x)
    x = BatchNormalization()(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.1)(x)
    x = Dropout(0.4)(x)

    x = Dense(128, activation=None)(x)
    x = BatchNormalization()(x)
    x = tf.keras.layers.LeakyReLU(alpha=0.1)(x)
    x = Dropout(0.3)(x)

    # Layer đầu ra
    outputs = Dense(num_classes, activation='softmax')(x)

    # Tạo model
    model = Model(inputs=base_model.input, outputs=outputs)

    # Biên dịch với Adam optimizer và learning rate thấp hơn
    model.compile(
        optimizer=Adam(learning_rate=0.0005),
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )
    return model

# Xây dựng mô hình
model = build_model()
model.summary()

# Callbacks
callbacks = [
    # Lưu mô hình tốt nhất
    ModelCheckpoint(
        'best_model.h5',
        monitor='val_accuracy',
        verbose=1,
        save_best_only=True,
        mode='max'
    ),
    # Giảm learning rate khi không cải thiện
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=0.00001,
        verbose=1
    ),
    # Dừng sớm để tránh overfitting
    EarlyStopping(
        monitor='val_loss',
        patience=8,
        restore_best_weights=True,
        verbose=1
    )
]

# Train mô hình
if __name__ == "__main__":
    print("Bắt đầu huấn luyện mô hình...")

    # Đào tạo mô hình
    history = model.fit(
        train_generator,
        epochs=30,
        steps_per_epoch=steps_per_epoch,
        validation_data=validation_generator,
        validation_steps=validation_steps,
        callbacks=callbacks,
        workers=1,  # Giới hạn số worker process
        use_multiprocessing=False,
        verbose=1
    )

    # Đánh giá mô hình cuối cùng
    final_loss, final_accuracy, final_precision, final_recall = model.evaluate(
        validation_generator,
        steps=validation_steps
    )

    print(f"\nKết quả đánh giá cuối cùng:")
    print(f"   ├── Accuracy: {final_accuracy:.4f}")
    print(f"   ├── Precision: {final_precision:.4f}")
    print(f"   ├── Recall: {final_recall:.4f}")
    print(f"   └── F1-Score: {2 * (final_precision * final_recall) / (final_precision + final_recall):.4f}")

    # Vẽ biểu đồ loss và accuracy
    plt.figure(figsize=(16, 6))

    # Loss plot
    plt.subplot(1, 3, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Train vs Validation Loss')
    plt.legend()

    # Accuracy plot
    plt.subplot(1, 3, 2)
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Train vs Validation Accuracy')
    plt.legend()

    # Learning Rate plot
    plt.subplot(1, 3, 3)
    plt.semilogy(history.history.get('lr', []), label='Learning Rate')
    plt.xlabel('Epochs')
    plt.ylabel('Learning Rate')
    plt.title('Learning Rate Change')
    plt.legend()

    plt.tight_layout()
    plt.savefig('training_history.png')
    plt.show()

    # Lưu mô hình
    model.save("dog_cat_breed_classifier_mobilenet.h5")
    print("Mô hình đã lưu thành công: dog_cat_breed_classifier_mobilenet.h5")
    print("Biểu đồ lịch sử huấn luyện đã lưu: training_history.png")

    # Tạo mô hình dự đoán nhẹ hơn cho triển khai
    print("🔧 Tạo mô hình dự đoán tối ưu...")

    # Convert to TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    # Lưu mô hình TFLite
    with open('dog_cat_breed_classifier.tflite', 'wb') as f:
        f.write(tflite_model)

    print("Đã xuất mô hình TFLite: dog_cat_breed_classifier.tflite")
