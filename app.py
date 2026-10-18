from flask import Flask, render_template, request, redirect, session, send_from_directory
import mysql.connector
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import os

app = Flask(__name__)
app.secret_key = "skinscan_secret"

# ==========================
# LOAD MODEL AI
# ==========================
model = load_model("model/skin_model.keras")


# DATABASE
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="skinkulit_ai"
)

# ==========================
# FOLDER UPLOAD
# ==========================
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# HOME
# ==========================
@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].lower()
        password = request.form["password"]

        cursor = db.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=%s AND password=%s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()

        if user:
            session["username"] = username
            return redirect("/")

        return "Username atau Password Salah"

    return render_template("login.html")


# ==========================
# REGISTER
# ==========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].lower()
        password = request.form["password"]

        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        cek_user = cursor.fetchone()

        if cek_user:
            cursor.close()
            return "Username sudah digunakan"

        cursor.execute(
            """
            INSERT INTO users(username,password)
            VALUES(%s,%s)
            """,
            (username, password)
        )

        db.commit()
        cursor.close()

        return redirect("/login")

    return render_template("daftar.html")


# ==========================
# HALAMAN SCAN
# ==========================
@app.route("/scan")
def scan():

    if "username" not in session:
        return redirect("/login")

    return render_template("scan.html")


# ==========================
# ANALISIS AI
# ==========================
@app.route("/analisis", methods=["POST"])
def analisis():

    if "username" not in session:
        return redirect("/login")

    file = request.files["gambar"]

    if file.filename == "":
        return "Pilih gambar terlebih dahulu"

    # ==========================
    # SIMPAN GAMBAR
    # ==========================
    path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(path)

    # ==========================
    # PREPROCESSING
    # ==========================
    img = Image.open(path).convert("RGB")
    img = img.resize((224, 224))

    img = np.array(img, dtype=np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    # ==========================
    # PREDIKSI AI
    # ==========================
    prediksi = model.predict(img, verbose=0)[0]

    label = [
        "Melanoma",
        "Nevus",
        "Basal Cell Carcinoma",
        "Non Skin"
    ]

    print("\n===== HASIL PREDIKSI =====")

    for i, nilai in enumerate(prediksi):
        print(f"{label[i]} : {nilai * 100:.2f}%")

    confidence = float(np.max(prediksi))
    kelas = int(np.argmax(prediksi))

    print("Confidence :", confidence)
    print("Argmax     :", kelas)

    # ==========================
    # THRESHOLD
    # ==========================
    THRESHOLD = 0.70

    if confidence < THRESHOLD:
        hasil = "Non Skin"
        akurasi = confidence * 100
    else:
        hasil = label[kelas]
        akurasi = confidence * 100

    print("Hasil Akhir :", hasil)

    # ==========================
    # DESKRIPSI HASIL
    # ==========================
    if hasil == "Non Skin":

        hasil_id = "Objek Tidak Dikenali"

        deskripsi = """
        Gambar yang diupload bukan gambar kulit atau lesi kulit
        yang dapat dianalisis oleh sistem.
        """

    elif hasil == "Melanoma":

        hasil_id = "Melanoma"

        deskripsi = """
        Melanoma adalah jenis kanker kulit yang berkembang dari sel melanosit
        (sel penghasil pigmen kulit).
        """

    elif hasil == "Nevus":

        hasil_id = "Nevus (Tahi Lalat Jinak)"

        deskripsi = """
        Nevus adalah pertumbuhan sel pigmen pada kulit.
        """

    elif hasil == "Basal Cell Carcinoma":

        hasil_id = "Karsinoma Sel Basal"

        deskripsi = """
        Karsinoma Sel Basal adalah jenis kanker kulit yang paling sering ditemukan.
        """

    # ==========================
    # SIMPAN RIWAYAT
    # ==========================
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO riwayat
        (
            username,
            nama_pasien,
            umur,
            jk,
            lokasi,
            gambar,
            hasil,
            akurasi
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (

        session["username"],
        request.form["nama"],
        request.form["umur"],
        request.form["jk"],
        request.form["lokasi"],
        file.filename,
        hasil,
        round(akurasi, 2)

    ))

    db.commit()
    cursor.close()

    return render_template(
        "scan.html",
        hasil=hasil,
        hasil_id=hasil_id,
        deskripsi=deskripsi,
        akurasi=round(akurasi, 2),
        gambar=file.filename
    )# ==========================
# RIWAYAT
# ==========================
@app.route("/riwayat")
def riwayat():

    if "username" not in session:
        return redirect("/login")

    cursor = db.cursor(dictionary=True)

    # data riwayat
    cursor.execute("""
        SELECT *
        FROM riwayat
        WHERE username=%s
        ORDER BY tanggal DESC
    """, (session["username"],))

    data = cursor.fetchall()

    # statistik
    cursor.execute("""
        SELECT COUNT(*) total
        FROM riwayat
        WHERE username=%s
    """,(session["username"],))

    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM riwayat
        WHERE username=%s
        AND hasil='Melanoma'
    """,(session["username"],))

    melanoma = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM riwayat
        WHERE username=%s
        AND hasil='Basal Cell Carcinoma'
    """,(session["username"],))

    basal = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM riwayat
        WHERE username=%s
        AND hasil='Nevus'
    """,(session["username"],))

    nevus = cursor.fetchone()["total"]

    cursor.close()

    return render_template(
        "riwayat.html",
        data=data,
        total=total,
        melanoma=melanoma,
        basal=basal,
        nevus=nevus
    )

@app.route("/hapus_riwayat/<int:id>")
def hapus_riwayat(id):

    if "username" not in session:
        return redirect("/login")

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM riwayat
        WHERE id=%s
        AND username=%s
    """, (id, session["username"]))

    db.commit()
    cursor.close()

    return redirect("/riwayat")

# ==========================
# TAMPILKAN GAMBAR UPLOAD
# ==========================
@app.route('/uploads/<filename>')
def uploaded_file(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

@app.route("/profil")
def profil():

    if "username" not in session:
        return redirect("/login")

    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM riwayat
        WHERE username=%s
    """,(session["username"],))

    total = cursor.fetchone()[0]

    cursor.close()

    return render_template(
        "profil.html",
        total=total
    )

# ==========================
# LOGOUT
# ==========================
@app.route("/logout")
def logout():

    session.pop("username", None)

    return redirect("/")


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)