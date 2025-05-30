def run_sql_script(sql_file: str):
    sql_path = Path(sql_file)
    if not sql_path.exists():
        raise FileNotFoundError(f"{sql_file} bulunamadı.")

    script = sql_path.read_text(encoding="utf-8")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="gulsuf201",
        database="diyabet_takip",
        autocommit=True
    )
    cursor = conn.cursor()

    # 🔧 Tüm komutları ";" ile böl ve tek tek çalıştır
    for command in script.split(";"):
        cmd = command.strip()
        if cmd:  # boş satır değilse çalıştır
            try:
                cursor.execute(cmd)
            except Exception as e:
                print("❌ Hata:", e)
                print("Komut:", cmd)
                break

    cursor.close()
    conn.close()
    print("✅ SQL script başarıyla çalıştırıldı.")
