import hashlib
import datetime
from db import DB


def _hash(pw: str) -> str:
    """Kullanıcı şifresi SHA‑256 hash"""
    return hashlib.sha256(pw.encode()).hexdigest()


class Repo:
    # ---------- LOGIN -------------------------------------------------
    @staticmethod
    def get_user(tc, pw):
        tc = ''.join(filter(str.isdigit, tc))
        with DB() as db:
            rows = db.query(
                "SELECT * FROM users WHERE tc_kimlik_no=%s AND password_hash=%s",
                (tc, _hash(pw))
            )
            return rows[0] if rows else None

    # ---------- YENİ: HASTA OLUŞTURMA / PROFİL ------------------------
    @staticmethod
    def create_patient(tc_no: str, raw_pw: str, doctor_id: int,
                       email: str, birth_date: datetime.date, gender: str,
                       photo_bytes: bytes | None = None):
        """Doktor yeni hasta oluşturur; users + patients iki adım."""
        with DB() as db:
            # 1. users kaydı
            db.query(
                """
                INSERT INTO users
                    (tc_kimlik_no, password_hash, email, birth_date,
                     gender, photo_blob, role)
                VALUES (%s,%s,%s,%s,%s,%s,'hasta')
                """,
                (tc_no, _hash(raw_pw), email, birth_date, gender, photo_bytes),
                fetch=False
            )
            new_uid = db.cur.lastrowid
            # 2. patients kaydı
            db.query(
                "INSERT INTO patients (id, doctor_id) VALUES (%s,%s)",
                (new_uid, doctor_id), fetch=False
            )
            return new_uid

    @staticmethod
    def update_profile(uid: int, *, email=None, birth_date=None,
                       gender=None, photo_bytes: bytes | None = None):
        """Sadece verilen alanları günceller."""
        parts, params = [], []
        if email is not None:
            parts.append("email=%s")
            params.append(email)
        if birth_date is not None:
            parts.append("birth_date=%s")
            params.append(birth_date)
        if gender is not None:
            parts.append("gender=%s")
            params.append(gender)
        if photo_bytes is not None:
            parts.append("photo_blob=%s")
            params.append(photo_bytes)
        if not parts:
            return  # değişiklik yok
        params.append(uid)
        q = f"UPDATE users SET {', '.join(parts)} WHERE id=%s"
        Repo._exec(q, tuple(params))

    @staticmethod
    def get_profile(uid: int):
        return Repo._single(
            """
            SELECT tc_kimlik_no, email, birth_date, gender, photo_blob
              FROM users WHERE id=%s
            """,
            uid
        )

    # ---------- ölçüm ----------


    @staticmethod
    def add_measurement(user_id, val, slot, date, time):
        import mysql.connector
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
<<<<<<< HEAD
                password="gulsuf201",  # ← Şifren buysa bu şekilde bırak
=======
                password="gulsuf201",  # ← Şifren buysa bu şekilde bırak. Varsa gir.
>>>>>>> ff5ba3752ee48505231700abff9bf0d5334e1272
                database="diyabet_takip"
            )
            cursor = conn.cursor()

            query = """
<<<<<<< HEAD
                INSERT INTO blood_sugar_measurements
                    (patient_id, sugar_level, time_slot, measurement_time, zaman_dilimi)
                VALUES (%s, %s, %s, %s, %s)
            """
            full_dt = datetime.datetime.combine(date, time)
# ENUM'a uymayan değer için time_slot = None → veritabanına NULL gider
            enum_values = {'Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece'}
            ts_val = slot if slot in enum_values else None
            zd_val = slot if slot else "Bilinmeyen"

 
            cursor.execute(query, (user_id, val, slot, full_dt, slot))
=======
                INSERT INTO blood_sugar_measurements (user_id, deger, zaman_dilimi, tarih, saat)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, val, slot, date, time))
>>>>>>> ff5ba3752ee48505231700abff9bf0d5334e1272
            conn.commit()

            print("✅ SQL'e başarıyla kaydedildi:", val, slot, date, time)

        except Exception as e:
            print("❌ SQL HATASI:", e)

        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            try:
                if conn:
                    conn.close()
            except:
                pass


<<<<<<< HEAD

=======
>>>>>>> ff5ba3752ee48505231700abff9bf0d5334e1272
    # ---------- özet ----------

    @staticmethod
    def daily_summary(pid):
        return Repo._single("""SELECT ortalama_kan_sekeri
                                FROM v_gunluk_kan_sekeri
                               WHERE patient_id=%s AND tarih=CURDATE()""", pid)

    @staticmethod
    def check_daily_completeness(pid):
        row = Repo._single("""SELECT COUNT(*) AS c
                                FROM blood_sugar_measurements
                               WHERE patient_id=%s
                                 AND DATE(measurement_time)=CURDATE()""", pid)
        return row['c']

    # ---------- egzersiz / diyet ----------
    @staticmethod
    def add_exercise(pid, ex_id, status):
        Repo._exec("""INSERT INTO exercise_logs
                       (patient_id, exercise_type_id, exercise_date, status)
                     VALUES (%s,%s,CURDATE(),%s)""",
                   (pid, ex_id, status))

    @staticmethod
    def exercise_percent(pid):
        return Repo._list("""SELECT exercise_date,
                                    ROUND(100*SUM(status='yapıldı')/COUNT(*),1) AS oran
                               FROM exercise_logs
                              WHERE patient_id=%s
                           GROUP BY exercise_date""", pid)

    @staticmethod
    def add_diet(pid, diet_id, status):
        Repo._exec("""INSERT INTO diet_logs
                       (patient_id, diet_type_id, diet_date, status)
                     VALUES (%s,%s,CURDATE(),%s)""",
                   (pid, diet_id, status))

    @staticmethod
    def diet_percent(pid):
        return Repo._list("""SELECT diet_date,
                                    ROUND(100*SUM(status='uygulandı')/COUNT(*),1) AS oran
                               FROM diet_logs
                              WHERE patient_id=%s
                           GROUP BY diet_date""", pid)

    # ---------- doktor ----------
    @staticmethod
    def list_patients(doc_id):
        return Repo._list("""SELECT u.id, u.tc_kimlik_no
                               FROM patients p
                               JOIN users u ON p.id=u.id
                              WHERE p.doctor_id=%s""", doc_id)

    @staticmethod
    def alerts_of_patient(pid, *, only_today=False):
        if only_today:
            return Repo._list("""
                SELECT tarih, saat, alert_type, sugar_level
                FROM v_uyari_listesi
                WHERE patient_id=%s
                AND DATE(tarih) = CURDATE()
            """, pid)
        else:
            return Repo._list("""
                SELECT tarih, saat, alert_type, sugar_level
                FROM v_uyari_listesi
                WHERE patient_id=%s
            """, pid)

    # ---------- insulin ----------

    @staticmethod
    def insulin_advice_on(pid, tarih: str):
        return Repo._single("SELECT insulin_dozu FROM v_insulin_ozet "
                            "WHERE patient_id=%s AND tarih=%s", pid, tarih)

    @staticmethod
    def slot_measurements_on(pid, date_obj: datetime.date):
        return Repo._list("""
            SELECT time_slot, sugar_level
              FROM blood_sugar_measurements
             WHERE patient_id=%s
               AND DATE(measurement_time)=%s
          ORDER BY FIELD(time_slot, 'Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
        """, pid, date_obj)

    # ==============================================================
    # 🆕 EKLENEN YÖNTEMLER (Doktor Paneli ihtiyaçları)
    # ==============================================================

    @staticmethod
    def measurement_table(pid):
        """
        Hasta bazlı tüm kan şekeri ölçümlerini (tarih-saat-değer) döndürür.
        """
        return Repo._list(
            """SELECT DATE(measurement_time)                        AS tarih,
                      TIME_FORMAT(measurement_time,'%H:%i')         AS saat,
                      sugar_level                                   AS deger
                 FROM blood_sugar_measurements
                WHERE patient_id=%s
             ORDER BY measurement_time""",
            pid
        )

    @staticmethod
    def daily_graph_data(pid):
        """
        Günlük ortalama kan şekeri listesi (grafik için).
        """
        return Repo._list(
            """SELECT tarih,
                      ortalama_kan_sekeri AS ortalama
                 FROM v_gunluk_kan_sekeri
                WHERE patient_id=%s
             ORDER BY tarih""",
            pid
        )

    @staticmethod
    def patient_archive(pid):
        """
        Ölçümler + egzersiz/diyet logları + uyarılar → tek arşiv listesi.
        """
        return Repo._list(
            """
            SELECT DATE(measurement_time) AS tarih,
                   'Ölçüm'               AS veri_tipi,
                   CONCAT(time_slot,' → ', sugar_level,' mg/dL') AS icerik
              FROM blood_sugar_measurements
             WHERE patient_id=%s
            UNION ALL
            SELECT exercise_date,
                   'Egzersiz',
                   CONCAT(exercise_type_id,' : ',status)
              FROM exercise_logs
             WHERE patient_id=%s
            UNION ALL
            SELECT diet_date,
                   'Diyet',
                   CONCAT(diet_type_id,' : ',status)
              FROM diet_logs
             WHERE patient_id=%s
            UNION ALL
            SELECT alert_date,
                   'Uyarı',
                   CONCAT(alert_type,' (',sugar_level,' mg/dL)')
              FROM alerts
             WHERE patient_id=%s
            ORDER BY tarih
            """,
            pid, pid, pid, pid
        )

    # ---------- yardımcı generic ----------
    @staticmethod
    def _single(sql, *params):
        with DB() as db:
            rows = db.query(sql, params)
            return rows[0] if rows else None

    @staticmethod
    def _list(sql, *params):
        with DB() as db:
            return db.query(sql, params)

    @staticmethod
    def _exec(sql, params=()):
        with DB() as db:
            db.query(sql, params, fetch=False)

    # ---------- measurements / alert helpers ----------
    @staticmethod
    def today_measurements(pid):
        return Repo._list("""SELECT sugar_level
                               FROM blood_sugar_measurements
                              WHERE patient_id=%s
                                AND DATE(measurement_time)=CURDATE()
                                AND sugar_level IS NOT NULL""", pid)

    @staticmethod
    def add_alert_full(pid, alert_type, level, date_obj, time_obj, message):
        with DB() as db:
            db.query("""
                INSERT INTO alerts
                    (patient_id, alert_type, sugar_level, alert_date, alert_time, alert_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pid, alert_type, level, date_obj, time_obj, message), fetch=False)
<<<<<<< HEAD


    @staticmethod
    def assign_plan(pid, diet, exercise):
        """Doktorun hastaya atadığı güncel planı kaydeder (üzerine yazar)."""
        Repo._exec("""
            INSERT INTO patient_plan (patient_id, diet_plan, exercise_plan, assigned_date)
            VALUES (%s,%s,%s,CURDATE())
            ON DUPLICATE KEY UPDATE
                diet_plan=VALUES(diet_plan),
                exercise_plan=VALUES(exercise_plan),
                assigned_date=VALUES(assigned_date)
        """, (pid, diet, exercise))


    @staticmethod
    def get_assigned_plan(pid: int):
        return Repo._single(
            "SELECT diet_plan, exercise_plan FROM assigned_plans WHERE patient_id=%s",
            pid
        )
=======
>>>>>>> ff5ba3752ee48505231700abff9bf0d5334e1272
