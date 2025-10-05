


DROP DATABASE IF EXISTS diyabet_takip;

CREATE DATABASE diyabet_takip CHARACTER SET utf8mb4 COLLATE utf8mb4_turkish_ci;

USE diyabet_takip;


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tc_kimlik_no CHAR(11) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    birth_date DATE,
    gender ENUM('Erkek', 'Kadın') NOT NULL,
    email VARCHAR(100) NOT NULL,
    role ENUM('doktor', 'hasta') NOT NULL,
    photo_blob LONGBLOB
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE doctors (
    id INT PRIMARY KEY, -- FK->users.id
    uzmanlik VARCHAR(100),
    FOREIGN KEY (id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE patients (
    id INT PRIMARY KEY, -- FK->users.id
    doctor_id INT,
    FOREIGN KEY (id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;


CREATE TABLE exercise_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE diet_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE symptoms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE blood_sugar_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    measurement_time DATETIME NOT NULL,
    sugar_level INT NOT NULL,
    time_slot ENUM(
        'Sabah',
        'Öğle',
        'İkindi',
        'Akşam',
        'Gece'
    ) NOT NULL,
    zaman_dilimi VARCHAR(20),
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_bsm_patient_date (patient_id, measurement_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE exercise_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    exercise_type_id INT NOT NULL,
    exercise_date DATE NOT NULL,
    status ENUM('yapıldı', 'yapılmadı') NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (exercise_type_id) REFERENCES exercise_types (id),
    INDEX idx_exlog_patient_date (patient_id, exercise_date)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE diet_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    diet_type_id INT NOT NULL,
    diet_date DATE NOT NULL,
    status ENUM('uygulandı', 'uygulanmadı') NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (diet_type_id) REFERENCES diet_types (id),
    INDEX idx_dlog_patient_date (patient_id, diet_date)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE symptom_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    symptom_id INT NOT NULL,
    symptom_date DATE NOT NULL,
    UNIQUE (
        patient_id,
        symptom_id,
        symptom_date
    ),
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES symptoms (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    alert_type ENUM(
        'Ölçüm Eksik',
        'Yetersiz Ölçüm',
        'Acil Uyarı',
        'İzleme Uyarısı'
    ) NOT NULL,
    alert_message TEXT,
    sugar_level INT,
    alert_date DATE,
    alert_time TIME,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_alerts_patient_date (patient_id, alert_date)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;

CREATE TABLE insulin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    insulin_ml DECIMAL(4, 1) NOT NULL,
    log_time DATETIME NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_insulin_patient_date (patient_id, log_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_turkish_ci;


CREATE TABLE insulin_history (
    patient_id INT NOT NULL,
    date DATE NOT NULL,
    slot ENUM(
        'sabah',
        'ogle',
        'ikindi',
        'aksam',
        'gece'
    ) NOT NULL,
    sugar_level DECIMAL(5, 1) NOT NULL,
    recommended_dose_ml VARCHAR(8),
    PRIMARY KEY (patient_id, date, slot),
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE assigned_plans (
    patient_id INT PRIMARY KEY,
    diet_plan VARCHAR(100),
    exercise_plan VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE ON UPDATE CASCADE
);

DELIMITER /
/

CREATE TRIGGER trg_bsm_alert
AFTER INSERT ON blood_sugar_measurements
FOR EACH ROW
BEGIN
  IF NEW.sugar_level < 70 OR NEW.sugar_level > 200 THEN
    INSERT INTO alerts (
      patient_id,
      measurement_id,
      alert_type,
      alert_message,
      sugar_level,
      alert_date,
      alert_time
    ) VALUES (
      NEW.patient_id,
      NEW.id,
      'Acil Uyarı',
      CONCAT('Kan şekeri ', NEW.sugar_level, ' mg/dL! Acil müdahale gerekebilir.'),
      NEW.sugar_level,
      DATE(NEW.measurement_time),
      TIME(NEW.measurement_time)
    );
  END IF;
END
/
/

DELIMITER;


DROP EVENT IF EXISTS ev_gun_sonu_kontrol;

DELIMITER /
/

CREATE EVENT ev_gun_sonu_kontrol
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURDATE(),'23:59:00')
DO
BEGIN
  /* Hiç ölçüm yapmayan hastalara uyarı */
  INSERT INTO alerts (patient_id, alert_type, alert_message, alert_date)
  SELECT p.id,
         'Ölçüm Eksik',
         'Hasta gün boyunca kan şekeri ölçümü yapmadı.',
         CURDATE()
  FROM patients p
  LEFT JOIN blood_sugar_measurements m
    ON p.id = m.patient_id AND DATE(m.measurement_time)=CURDATE()
  WHERE m.id IS NULL;

  /* Yetersiz ölçüm yapan hastalara uyarı (<3) */
  INSERT INTO alerts (patient_id, alert_type, alert_message, alert_date)
  SELECT t.patient_id,
         'Yetersiz Ölçüm',
         'Günlük ölçüm sayısı yetersiz (<3).',
         CURDATE()
  FROM (
     SELECT patient_id, COUNT(*) AS c
     FROM   blood_sugar_measurements
     WHERE  DATE(measurement_time)=CURDATE()
     GROUP  BY patient_id
     HAVING c < 3 AND c > 0
  ) t;
END
/
/

DELIMITER;


CREATE OR REPLACE VIEW v_gunluk_kan_sekeri AS
SELECT
    patient_id,
    DATE(measurement_time) AS tarih,
    ROUND(AVG(sugar_level), 1) AS ortalama_kan_sekeri
FROM blood_sugar_measurements
GROUP BY
    patient_id,
    DATE(measurement_time);

CREATE OR REPLACE VIEW v_egzersiz_uygulama_orani AS
SELECT
    patient_id,
    exercise_date,
    ROUND(
        100 * SUM(status = 'yapıldı') /

COUNT(*),
        2
    ) AS egzersiz_orani
FROM exercise_logs
GROUP BY
    patient_id,
    exercise_date;

CREATE OR REPLACE VIEW v_diyet_uygulama_orani AS
SELECT
    patient_id,
    diet_date,
    ROUND(
        100 * SUM(status = 'uygulandı') /

COUNT(*),
        2
    ) AS diyet_orani
FROM diet_logs
GROUP BY
    patient_id,
    diet_date;

CREATE OR REPLACE VIEW v_insulin_ozet AS
SELECT
    patient_id,
    DATE(measurement_time) AS tarih,
    ROUND(AVG(sugar_level)) AS ortalama,
    CASE
        WHEN AVG(sugar_level) < 70 THEN ''
        WHEN AVG(sugar_level) <= 110 THEN ''
        WHEN AVG(sugar_level) <= 150 THEN '1 ml'
        WHEN AVG(sugar_level) <= 200 THEN '2 ml'
        ELSE '3 ml'
    END AS insulin_dozu
FROM blood_sugar_measurements
GROUP BY
    patient_id,
    DATE(measurement_time);

CREATE OR REPLACE VIEW v_uyari_listesi AS
SELECT
    patient_id,
    alert_type,
    alert_message,
    sugar_level,
    alert_date AS tarih,
    alert_time AS saat
FROM alerts
ORDER BY alert_date DESC, alert_time DESC;


INSERT INTO
    exercise_types (name)
VALUES ('Yürüyüş'),
    ('Bisiklet'),
    ('Klinik Egzersiz');

INSERT INTO
    diet_types (name)
VALUES ('Az Şekerli Diyet'),
    ('Şekersiz Diyet'),
    ('Dengeli Beslenme');

INSERT INTO
    symptoms (name)
VALUES ('Poliüri'),
    ('Polifaji'),
    ('Polidipsi'),
    ('Nöropati'),
    ('Kilo kaybı'),
    ('Yorgunluk'),
    ('Yaraların yavaş iyileşmesi'),
    ('Bulanık görme');

/* Doktor hesabı (şifre SHA-256 hash örneği) */
INSERT INTO
    users (
        tc_kimlik_no,
        password_hash,
        first_name,
        last_name,
        gender,
        email,
        role
    )
VALUES (
        '11111111110',
        '3e59cb27c718ba2a58ae78e92d2a27ac5a375a859e5aa57f51f86a8bbbde9fe2',
        'Aybars',
        'Demir',
        'Erkek',
        'doktor@example.com',
        'doktor'
    );

INSERT INTO
    doctors (id, uzmanlik)
VALUES (
        LAST_INSERT_ID(),
        'Endokrinoloji'
    );

-- ============================================================
--  BETİK TAMAMLANDI  ✅
-- ============================================================

ALTER TABLE blood_sugar_measurements
MODIFY COLUMN time_slot ENUM(
    'Sabah',
    'Öğle',
    'İkindi',
    'Akşam',
    'Gece'
) DEFAULT NULL;
-- NOT NULL kaldırıldı

ALTER TABLE users ADD COLUMN profile_image LONGBLOB;

ALTER TABLE users DROP COLUMN photo_blob;

ALTER TABLE alerts MODIFY alert_type VARCHAR(50);

SHOW CREATE TABLE users;

UPDATE symptoms SET name = 'Poliüri' WHERE id = 1;

UPDATE symptoms SET name = 'Polifaji' WHERE id = 2;

UPDATE symptoms SET name = 'Polidipsi' WHERE id = 3;

UPDATE symptoms SET name = 'Nöropati' WHERE id = 4;

UPDATE symptoms SET name = 'Kilo Kaybı' WHERE id = 5;

UPDATE symptoms SET name = 'Yorgunluk' WHERE id = 6;

UPDATE symptoms
SET
    name = 'Yaraların Yavaş İyileşmesi'
WHERE
    id = 7;

UPDATE symptoms SET name = 'Bulanık Görme' WHERE id = 8;

SELECT *
FROM blood_sugar_measurements
WHERE
    DATE(measurement_time) = '2025-05-18';

SELECT * FROM exercise_logs WHERE exercise_date = '2025-05-18';

SELECT * FROM diet_logs WHERE diet_date = '2025-05-18';

SELECT USER ();

ALTER TABLE alerts ADD COLUMN measurement_id INT;

ALTER TABLE alerts
ADD CONSTRAINT fk_alert_measurement FOREIGN KEY (measurement_id) REFERENCES blood_sugar_measurements (id) ON DELETE CASCADE ON UPDATE CASCADE;

CREATE OR REPLACE VIEW v_egzersiz_diyet_sugar AS
SELECT
    m.patient_id,
    DATE(m.measurement_time) AS tarih,
    m.sugar_level,
    CASE
        WHEN e.exercise_date IS NOT NULL THEN 1
        ELSE 0
    END AS egzersiz,
    CASE
        WHEN d.diet_date IS NOT NULL THEN 1
        ELSE 0
    END AS diyet
FROM
    blood_sugar_measurements m
    LEFT JOIN exercise_logs e ON m.patient_id = e.patient_id
    AND DATE(m.measurement_time) = e.exercise_date
    LEFT JOIN diet_logs d ON m.patient_id = d.patient_id
    AND DATE(m.measurement_time) = d.diet_date;

CREATE OR REPLACE VIEW v_diyet_egzersiz_4grup AS
SELECT
    m.patient_id,
    CASE
        WHEN e.exercise_date IS NOT NULL
        AND d.diet_date IS NOT NULL THEN 'Her İkisi Yapılan'
        WHEN e.exercise_date IS NOT NULL
        AND d.diet_date IS NULL THEN 'Sadece Egzersiz Yapılan'
        WHEN e.exercise_date IS NULL
        AND d.diet_date IS NOT NULL THEN 'Sadece Diyet Yapılan'
        ELSE 'Hiçbiri Yapılmayan'
    END AS kategori,
    AVG(m.sugar_level) AS ortalama
FROM
    blood_sugar_measurements m
    LEFT JOIN exercise_logs e ON m.patient_id = e.patient_id
    AND DATE(m.measurement_time) = e.exercise_date
    LEFT JOIN diet_logs d ON m.patient_id = d.patient_id
    AND DATE(m.measurement_time) = d.diet_date
GROUP BY
    m.patient_id,
    kategori;

INSERT INTO
    users (
        tc_kimlik_no,
        password_hash,
        first_name,
        last_name,
        gender,
        email,
        role
    )
VALUES (
        '22222222221',
        '3e59cb27c718ba2a58ae78e92d2a27ac5a375a859e5aa57f51f86a8bbbde9fe2',
        'Zeynep',
        'Çelik',
        'Kadın',
        'zeynep@example.com',
        'doktor'
    );

SELECT id FROM users WHERE tc_kimlik_no = '22222222221';

INSERT INTO doctors (id, uzmanlik) VALUES (2, 'Endokrinoloji');

UPDATE users SET birth_date = '1985-07-25' WHERE id = 2;
