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
    def create_patient(tc_no: str, raw_pw: str, first_name: str, last_name: str, doctor_id: int,
                       email: str, birth_date: datetime.date, gender: str,
                       photo_bytes: bytes | None = None):
        """Doktor yeni hasta oluşturur; users + patients iki adım."""
        with DB() as db:
            # 1. users kaydı
            db.query(
                """
                INSERT INTO users
                    (tc_kimlik_no, password_hash,first_name, last_name, email, birth_date,
                     gender, profile_image, role)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'hasta')
                """,
                (tc_no, _hash(raw_pw),first_name, last_name, email, birth_date, gender, photo_bytes),
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
            parts.append("profile_image=%s")
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
            SELECT tc_kimlik_no, email, birth_date, gender, profile_image
              FROM users WHERE id=%s
            """,
            uid
        )

    @staticmethod
    def add_measurement(user_id, val, slot, date, time):
        import mysql.connector
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="gulsuf201",  # ← senin şifrense böyle kalacak
                database="diyabet_takip"
            )
            cursor = conn.cursor()

            full_dt = datetime.datetime.combine(date, time)
            query = """
                INSERT INTO blood_sugar_measurements
                    (patient_id, sugar_level, time_slot, measurement_time, zaman_dilimi)
                VALUES (%s, %s, %s, %s, %s)
            """
            enum_values = {'Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece'}
            ts_val = slot if slot in enum_values else None
            zd_val = slot if slot else "Bilinmeyen"

            cursor.execute(query, (user_id, val, ts_val, full_dt, zd_val))
            conn.commit()

        except Exception as e:
            print("❌ SQL HATASI:", e)

        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except:
                pass


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
        return Repo._list("""
            SELECT u.id, u.tc_kimlik_no, u.first_name, u.last_name
            FROM patients p
            JOIN users u ON p.id=u.id
            WHERE p.doctor_id=%s
        """, doc_id)

    @staticmethod
    def alerts_of_patient(pid, *, only_today=False):
        base = """
            SELECT tarih, saat, alert_type, sugar_level
            FROM v_uyari_listesi
            WHERE patient_id=%s
        """
        if only_today:
            base += " AND tarih=CURDATE()"
        base += " ORDER BY tarih DESC, saat DESC"
        return Repo._list(base, pid)


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
                   CONCAT(
                       alert_type,
                       IF(sugar_level IS NOT NULL,
                          CONCAT(' (', sugar_level, ' mg/dL)'), '')
                   ) AS icerik
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
            
    # ### EKLE – ölçüm okuma yardımcıları  -------------------------------
    @staticmethod
    def get_measurement_value(pid: int, date_obj: datetime.date, slot: str):
        """Verilen tarih+slot için tek ölçüm döndürür (yoksa None)."""
        row = Repo._single("""SELECT sugar_level
                                FROM blood_sugar_measurements
                            WHERE patient_id=%s
                                AND DATE(measurement_time)=%s
                                AND time_slot=%s""",
                        pid, date_obj, slot)
        return row["sugar_level"] if row else None

    @staticmethod
    def get_measurement_dates(pid: int):
        """Hastanın ölçüm yaptığı tüm günler (tarih listesi)."""
        rows = Repo._list("""SELECT DISTINCT DATE(measurement_time) AS d
                            FROM blood_sugar_measurements
                            WHERE patient_id=%s""", pid)
        return [r["d"] for r in rows]
            
    @staticmethod
    def last_sugar_level(pid: int) -> int | None:
            """Hastanın en son (en güncel) kan şekeri ölçümünü döndürür."""
            row = Repo._single("""
                SELECT sugar_level
                FROM blood_sugar_measurements
                WHERE patient_id=%s
            ORDER BY measurement_time DESC
                LIMIT 1
            """, pid)
            return row["sugar_level"] if row else None
        
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
        # Temel alanlar kontrolü
        if not (alert_type and date_obj and time_obj and message):
            print("⚠️ Eksik veri: uyarı kaydedilmedi.")
            return

        tm_str = time_obj.strftime("%H:%M:%S")

        with DB() as db:
            # Aynı uyarı zaten var mı kontrolü (level NULL ise de kontrol yapılır)
            kontrol = db.query("""
                SELECT 1 FROM alerts
                WHERE patient_id = %s
                AND alert_type = %s
                AND (sugar_level = %s OR (sugar_level IS NULL AND %s IS NULL))
                AND alert_date = %s
                AND alert_time = %s
            """, (pid, alert_type, level, level, date_obj, tm_str))

            if kontrol:
                print("⚠️ Aynı uyarı zaten kayıtlı, tekrar eklenmedi.")
                return

            # Yeni kayıt
            db.query("""
                INSERT INTO alerts
                    (patient_id, alert_type, sugar_level, alert_date, alert_time, alert_message)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pid, alert_type, level, date_obj, tm_str, message), fetch=False)
    
    @staticmethod
    def get_assigned_plan(pid: int):
        return Repo._single(
            "SELECT diet_plan, exercise_plan FROM assigned_plans WHERE patient_id=%s",
            pid,
        )

    @staticmethod
    def assign_plan(pid: int, diet: str, ex: str):
        """Hastaya egzersiz ve diyet planı atar (ekle veya güncelle)."""
        with DB() as db:
            db.query("""
                INSERT INTO assigned_plans (patient_id, diet_plan, exercise_plan)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    diet_plan = VALUES(diet_plan),
                    exercise_plan = VALUES(exercise_plan)
            """, (pid, diet, ex), fetch=False)
            
         
    # repository.py  ➜  class Repo altına ekle
    @staticmethod
    def _build_level_alert(val: int) -> tuple[str | None, str | None]:
        """
        Ölçüm değerine göre (70–110 hariç) uyarı tipini & mesajını döndürür.
        Dönüş: (alert_type, alert_message)  – ikisi de None ise uyarı yoktur.
        """
        if val < 70:
            return ("Acil Uyarı",
                    f"Kan şekeri {val} mg/dL! Hipoglisemi riski, acil müdahale gerekebilir.")
        if 111 <= val <= 150:
            return ("Takip Uyarısı",
                    f"Kan şekeri {val} mg/dL. Durum izlenmeli.")
        if 151 <= val <= 200:
            return ("İzleme Uyarısı",
                    f"Kan şekeri {val} mg/dL. Diyabet kontrolü gereklidir.")
        if val > 200:
            return ("Acil Uyarı",
                    f"Kan şekeri {val} mg/dL! Hiperglisemi, acil müdahale gerekebilir.")
        return (None, None)          # 70-110 arası – uyarı yok
                

    # ==============================
    # --- EGZERSİZ / DİYET BLOĞU ---
    # ==============================

    @staticmethod
    def toggle_daily_exercise(pid: int, ex_id: int, done: bool,
                            date_obj: datetime.date | None = None):
        """
        Egzersiz günlüğü: done=True → 'yapıldı'
                        done=False → 'yapılmadı'
        """
        date_clause = "%s" if date_obj else "CURDATE()"
        params = (pid, ex_id, date_obj, 'yapıldı' if done else 'yapılmadı') if date_obj \
                else (pid, ex_id, 'yapıldı' if done else 'yapılmadı')

        Repo._exec(
            f"""
            INSERT INTO exercise_logs (patient_id, exercise_type_id, exercise_date, status)
            VALUES (%s, %s, {date_clause}, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
            """,
            params
        )





    @staticmethod
    def toggle_daily_diet(pid: int, diet_id: int, done: bool,
                          date_obj: datetime.date | None = None):
        """
        Diyet günlüğü:  done=True  → 'uygulandı'
                        done=False → 'uygulanmadı'
        """
        date_clause = "%s" if date_obj else "CURDATE()"
        params = (pid, diet_id, date_obj, 'uygulandı' if done else 'uygulanmadı') if date_obj \
                 else (pid, diet_id, 'uygulandı' if done else 'uygulanmadı')

        Repo._exec(
            f"""
            INSERT INTO diet_logs (patient_id, diet_type_id, diet_date, status)
            VALUES (%s, %s, {date_clause}, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
            """,
            params
        )

    # -------------------------------
    # --- KURAL MOTORU -------------
    # -------------------------------
    @staticmethod
    def generate_recommendation(sugar_level: int, symptom_ids: list[int]) -> tuple[str, str]:
        """
        Kan şekeri ve belirtilere göre (diyet, egzersiz) önerisi üretir.
        Dönüş: (diyet_ismi, egzersiz_ismi)
        """
        s = set(symptom_ids)

        if sugar_level < 70:
            if s & {4, 2, 6}:         # Nöropati, Polifaji, Yorgunluk
                return ("Dengeli Beslenme", "Yok")

        elif 70 <= sugar_level <= 110:
            if s & {6, 5}:            # Yorgunluk, Kilo kaybı
                return ("Az Şekerli Diyet", "Yürüyüş")
            if s & {2, 3}:            # Polifaji, Polidipsi
                return ("Dengeli Beslenme", "Yürüyüş")

        elif 110 < sugar_level <= 180:
            if s & {8, 4}:            # Bulanık görme, Nöropati
                return ("Az Şekerli Diyet", "Klinik Egzersiz")
            if s & {1, 3}:            # Poliüri, Polidipsi
                return ("Şekersiz Diyet", "Klinik Egzersiz")
            if s & {6, 4, 8}:         # Yorgunluk, Nöropati, Bulanık görme
                return ("Az Şekerli Diyet", "Yürüyüş")

        elif sugar_level > 180:
            if s & {7, 2, 3}:         # Yaraların yavaş iyileşmesi, Polifaji, Polidipsi
                return ("Şekersiz Diyet", "Klinik Egzersiz")
            if s & {7, 5}:            # Yaraların yavaş iyileşmesi, Kilo kaybı
                return ("Şekersiz Diyet", "Yürüyüş")

        return ("-", "-")  # eşleşme yoksa


    @staticmethod
    def daily_completeness_alert(pid: int, date_obj: datetime.date):
        """
        Verilen tarih için sadece belirlenen slot içindeki ölçümler baz alınarak
        eksik/yetersiz uyarı oluşturur.
        """
        row = Repo._single("""
            SELECT COUNT(*) AS c
            FROM blood_sugar_measurements
            WHERE patient_id=%s
            AND measurement_time >= %s
            AND measurement_time < DATE_ADD(%s, INTERVAL 1 DAY)
            AND time_slot IN ('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
        """, pid, date_obj, date_obj)          # ← tek tek argüman
        
        
        cnt = row["c"] if row else 0
        if cnt == 0:
            Repo.add_alert_full(pid, "Ölçüm Eksik Uyarısı", None,
                                date_obj, datetime.time(23, 59, 0),
                                "Hasta gün boyunca belirtilen saatlerde ölçüm yapmamıştır.")
        elif cnt < 3:
            Repo.add_alert_full(pid, "Ölçüm Yetersiz Uyarısı", None,
                                date_obj, datetime.time(23, 59, 0),
                                f"Hasta sadece {cnt} uygun ölçüm yaptı (yetersiz).")


    #  --- class Repo sonunda (varsa eskisini sil) -----------------
    @staticmethod
    def check_and_alert_incomplete_days(end_date: datetime.date):
        """
        Girilen tarihe (end_date) kadar, her hasta için
        Eksik / Yetersiz ölçüm uyarılarını oluşturur.
        """
        for h in Repo._list("SELECT id FROM patients"):
            pid = h["id"]

            # Hastanın ilk ölçüm yaptığı gün (yoksa end_date kullan)
            row = Repo._single("""
                SELECT MIN(DATE(measurement_time)) AS d
                FROM blood_sugar_measurements
                WHERE patient_id=%s
            """, pid)
            first_date = row["d"] or end_date     # None ise end_date

            cur = first_date
            while cur <= end_date:
                Repo.daily_completeness_alert(pid, cur)
                cur += datetime.timedelta(days=1)
    
    
    @staticmethod
    def patients_with_symptoms(symptom_names: list[str]) -> list[int]:
        """
        Verilen belirtilerden en az birine sahip hasta ID'lerini döner.
        """
        if not symptom_names:
            return []

        q = f"""
            SELECT DISTINCT patient_id
            FROM symptom_logs sl
            JOIN symptoms s ON s.id = sl.symptom_id
            WHERE s.name IN ({','.join(['%s'] * len(symptom_names))})
        """
        rows = Repo._list(q, *symptom_names)
        return [r["patient_id"] for r in rows]


    @staticmethod
    def log_symptoms(pid: int, symptom_ids: list[int]):
        """
        Seçilen semptomları symptom_logs tablosuna kaydeder.
        Aynı hasta–semptom için günceller (ON DUPLICATE).
        """
        for sid in symptom_ids:
            Repo._exec(
                """
                INSERT INTO symptom_logs
                    (patient_id, symptom_id, symptom_date)
                VALUES (%s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE symptom_date = CURDATE()
                """,
                (pid, sid)
            )


    # ──────────────────────────────────────────────────────────────
    #  KAN ŞEKERİ × EGZERSİZ / DİYET GRAFİĞİ  (yeni)
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def sugar_diet_exercise_data(pid: int, day: datetime.date):
        """
        Verilen gün için:
            - ölçüm saatleri & kan şekeri değerleri
            - o gün egzersiz yapılmış mı?
            - o gün diyet uygulanmış mı?
        OUTPUT: [{'tm': datetime.time, 'lvl': int,
                  'ex': bool, 'di': bool}]
        """
        q = """
            SELECT CAST(measurement_time AS TIME) AS tm,
                   sugar_level                  AS lvl,
                   MAX(el.status='yapıldı')     AS ex,
                   MAX(dl.status='uygulandı')   AS di
            FROM blood_sugar_measurements m
            LEFT JOIN exercise_logs el
                   ON el.patient_id = m.patient_id
                  AND el.exercise_date = %s
            LEFT JOIN diet_logs dl
                   ON dl.patient_id = m.patient_id
                  AND dl.diet_date = %s
            WHERE m.patient_id = %s
              AND DATE(m.measurement_time) = %s
            GROUP BY tm, lvl
            ORDER BY tm
        """
        return Repo._list(q, day, day, pid, day)
