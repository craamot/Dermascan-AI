import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

os.makedirs("model", exist_ok=True)

train_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    "dataset",
    target_size=(224,224),
    batch_size=16,
    class_mode="categorical",
    subset="training"
)

val_generator = train_datagen.flow_from_directory(
    "dataset",
    target_size=(224,224),
    batch_size=16,
    class_mode="categorical",
    subset="validation"
)

print("Kelas:", train_generator.class_indices)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(224,224,3)),

    tf.keras.layers.Conv2D(32,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(64,(3,3),activation='relu'),
    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(128,activation='relu'),
    tf.keras.layers.Dense(4,activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=10
)

model.save("model/skin_model.keras")

print("Model berhasil disimpan")