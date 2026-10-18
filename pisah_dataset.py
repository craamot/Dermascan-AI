import pandas as pd
import shutil
import os

csv_file = "HAM10000_metadata.csv"

folder1 = r"C:\Users\gitma\Downloads\archive\HAM10000_images_part_1"
folder2 = r"C:\Users\gitma\Downloads\archive\HAM10000_images_part_2"

dataset_dir = "dataset"

os.makedirs(dataset_dir, exist_ok=True)
os.makedirs(os.path.join(dataset_dir, "melanoma"), exist_ok=True)
os.makedirs(os.path.join(dataset_dir, "nevus"), exist_ok=True)
os.makedirs(os.path.join(dataset_dir, "Basal_Cell_Carcinoma"), exist_ok=True)

df = pd.read_csv(csv_file)

for _, row in df.iterrows():

    image_id = row["image_id"]
    dx = row["dx"]

    src = os.path.join(folder1, image_id + ".jpg")

    if not os.path.exists(src):
        src = os.path.join(folder2, image_id + ".jpg")

    if not os.path.exists(src):
        continue

    if dx == "mel":
        dst = os.path.join(dataset_dir, "melanoma")

    elif dx == "nv":
        dst = os.path.join(dataset_dir, "nevus")

    elif dx == "bcc":
        dst = os.path.join(dataset_dir, "Basal_Cell_Carcinoma")

    else:
        continue

    shutil.copy(src, dst)

print("Dataset berhasil dipisahkan!")