import mysql.connector

# Veritabanına bağlan
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="gulsuf201",  # Eğer MySQL'e girişte parola varsa buraya yaz
    database="diyabet_takip"
)
cur = conn.cursor()

# Fotoğrafı oku
with open("assets/doktor_pp.png", "rb") as f:
    photo_data = f.read()

# Doktoru güncelle (başlangıç doktoru)
sql = "UPDATE users SET profile_image=%s WHERE tc_kimlik_no=%s"
cur.execute(sql, (photo_data, "11111111110"))
conn.commit()

print("✅ Doktor profil fotoğrafı başarıyla yüklendi.")

cur.close()
conn.close()
