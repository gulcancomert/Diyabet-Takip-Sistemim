# =============================================================
# gui/doktor.py  —  Hasta ekleme ve “Gün İçi Değişim” düzeltildi
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import ttk, messagebox, filedialog, simpledialog   # ➊ EK
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import io
from utils import send_email
from repository import Repo
import numpy as np
BG = "#EAF2F8"


class DoktorWin(tk.Tk):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.state("zoomed")
        self.configure(bg=BG)
        self.title("Doktor Paneli")

        # Profil bilgisi
        self._profile = Repo.get_profile(self.user['id'])

        # Profil resmi (varsa)
        self._photo_tk = None
        if self._profile and self._profile['profile_image']:
            img = Image.open(io.BytesIO(
                self._profile['profile_image'])).resize((80, 80))
            self._photo_tk = ImageTk.PhotoImage(img)
            tk.Label(self, image=self._photo_tk, bg=BG).place(
                relx=0.02, rely=0.01)
            

        # 🔽 Profil resmi olsun olmasın mutlaka oluşturulmalı!
        cont = tk.Frame(self, bg=BG)
        cont.place(relx=0.5, rely=0.05, anchor="n")

        tk.Label(
            self,
            text=f"Hoş geldiniz Dr. {self.user['first_name']} {self.user['last_name']}",
            font=("Segoe UI", 18, "bold"),
            bg=BG
        ).place(relx=0.02, rely=0.12)

        tk.Label(cont, text="Hastalarınız", font=("Segoe UI", 20, "bold"), bg=BG
                 ).grid(row=0, column=0, padx=6, pady=4)

        self.lst = tk.Listbox(cont, height=20, width=45)
        self.lst.grid(row=1, column=0, rowspan=8, padx=6, pady=4)

        self._all_patients = Repo.list_patients(self.user["id"])
        # YENİ:
        for p in self._all_patients:
            self.lst.insert(tk.END, f"{p['id']} - {p['first_name']} {p['last_name']} ({p['tc_kimlik_no']})")


        # Butonlar
        tk.Button(cont, text="Uyarıları Göster", command=self.uyari,
                width=25, bg="#5DADE2", fg="white").grid(row=1, column=1, pady=4)

        tk.Button(cont, text="Günlük Ortalama", command=self.ort,
                width=25, bg="#5DADE2", fg="white").grid(row=2, column=1, pady=4)

        tk.Button(cont, text="Egzersiz/Diyet Geçmişi", command=self._show_ex_diet,
                width=25, bg="#5DADE2", fg="white").grid(row=3, column=1, pady=4)

        tk.Button(cont, text="Egz./Diyet Grafik", command=self._egz_diyet_grafik,
                width=25, bg="#5DADE2", fg="white").grid(row=4, column=1, pady=4)

        tk.Button(cont, text="Kan Şekeri Tablosu", command=self.tablo,
                width=25, bg="#5DADE2", fg="white").grid(row=5, column=1, pady=4)

        tk.Button(cont, text="Grafiksel Değişim", command=self.grafik,
                width=25, bg="#5DADE2", fg="white").grid(row=6, column=1, pady=4)

        tk.Button(cont, text="Arşiv Verileri", command=self.arsiv,
                width=25, bg="#5DADE2", fg="white").grid(row=7, column=1, pady=4)

        tk.Button(cont, text="Gün İçi Değişim", command=self.gun_ici,
                width=25, bg="#5DADE2", fg="white").grid(row=8, column=1, pady=4)

        tk.Button(cont, text="Hasta Ekle", command=self._hasta_ekle,
                width=25, bg="#5DADE2", fg="white").grid(row=9, column=1, pady=(12, 4))

        tk.Button(cont, text="Belirti - Öneri", command=self._open_symptom_form,
                width=25, bg="#5DADE2", fg="white").grid(row=10, column=1, pady=(4, 12))

        tk.Button(cont, text="Profil Düzenle", command=self._edit_profile,
                width=25, bg="#5DADE2", fg="white").grid(row=11, column=1, pady=(0, 12))

        tk.Button(cont, text="Gün Sonu Al", command=self._gun_sonu_al,
                width=25, bg="#5DADE2", fg="white").grid(row=12, column=1, pady=(0, 12))
            
        # --- Yeni: Hasta Filtrele butonu ---------------------------
        tk.Button(cont, text="Şekere Göre Filtrele", command=self._filter_patients,
                  width=25, bg="#5DADE2", fg="white").grid(row=13, column=1, pady=(0, 12))
            
        # Yeni: Belirtiye Göre Filtrele → Hemen altına ekle!
        tk.Button(cont, text="Belirtiye Göre Filtrele", command=self._filter_by_symptoms,
                width=25, bg="#5DADE2", fg="white").grid(row=14, column=1, pady=(0, 12))            
     
        tk.Button(cont,
                text="Şeker × Egz/Diyet Grafiği",
                command=self._sugar_diet_ex_graph,
                width=25, bg="#5DADE2", fg="white"
        ).grid(row=15, column=1, pady=(0, 12))
     
     # Checkbox örneği (uyari() fonksiyonuna yakın bir yere)
        self.only_today = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Sadece bugünkü uyarılar",
                       variable=self.only_today, bg=BG).place(relx=0.02, rely=0.25)
    # =====================
    # 🆕 HASTA EKLE PENCERESİ
    # =====================

    def _hasta_ekle(self):
        win = tk.Toplevel(self)
        win.title("Yeni Hasta Tanımla")
        win.configure(bg=BG)
        win.resizable(False, False)

        # --- Label/Entry yardımcı ---
        def add_label(text, row):
            tk.Label(win, text=text, bg=BG).grid(
                row=row, column=0, sticky="e", padx=6, pady=4)
            
        # --- Satırları sırayla oluştur ---
        add_label("Ad:", 0)
        e_first = tk.Entry(win, width=25)
        e_first.grid(row=0, column=1, pady=4)

        add_label("Soyad:", 1)
        e_last = tk.Entry(win, width=25)
        e_last.grid(row=1, column=1, pady=4)

        add_label("T.C. Kimlik No:", 2)
        e_tc = tk.Entry(win, width=25)
        e_tc.grid(row=2, column=1, pady=4)

        add_label("Şifre:", 3)
        e_pw = tk.Entry(win, width=25)
        e_pw.grid(row=3, column=1, pady=4)

        add_label("E-posta:", 4)
        e_mail = tk.Entry(win, width=25)
        e_mail.grid(row=4, column=1, pady=4)

        add_label("Doğum Tarihi (GG-AA-YYYY):", 5)
        e_bd = tk.Entry(win, width=25)
        e_bd.grid(row=5, column=1, pady=4)

        add_label("Cinsiyet (E/K):", 6)
        e_gn = tk.Entry(win, width=25)
        e_gn.grid(row=6, column=1, pady=4)

        # --- Fotoğraf seçici ---
        add_label("Fotoğraf (isteğe bağlı):", 7)
        frm_photo = tk.Frame(win, bg=BG)
        frm_photo.grid(row=7, column=1, pady=4)
        lbl_file = tk.Label(frm_photo, text="(seçilmedi)", bg=BG)
        lbl_file.pack(side="left")
        photo_bytes = {"data": None}

        def choose_file():
            path = filedialog.askopenfilename(
                title="Görsel seç",
                filetypes=[("Resim", "*.png;*.jpg;*.jpeg")]
            )
            if path:
                lbl_file.config(text=os.path.basename(path))
                with open(path, "rb") as f:
                    photo_bytes["data"] = f.read()

        # 📌 Pencereyi tekrar öne getir
                win.lift()
                win.focus_force()
        tk.Button(frm_photo, text="Seç", command=choose_file).pack(side="left", padx=6)

        # --- KAYDET butonu ---
        def kaydet():
            tc, pw, mail = (e_tc.get().strip(), e_pw.get().strip(), e_mail.get().strip())
            fname, lname = (e_first.get().strip(), e_last.get().strip())
            bd_str = e_bd.get().strip()
            c = e_gn.get().strip().upper()
            gn = "Erkek" if c == "E" else "Kadın" if c == "K" else None

            if not (tc and pw and mail and fname and lname):
                messagebox.showerror("Hata", "TC, şifre, e-posta ve ad-soyad zorunlu.")
                return

            #  T.C. Kimlik kontrolü
            if not tc.isdigit() or len(tc) != 11:
                messagebox.showerror("Hata", "T.C. Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır.")
                return
            
            try:
                bd = datetime.date.fromisoformat(bd_str) if bd_str else None
            except ValueError:
                messagebox.showerror("Hata", "Doğum tarihi GG-AA-YYYY olmalı")
                return

            try:
                Repo.create_patient(
                    tc, pw, fname, lname, self.user['id'], mail, bd, gn, photo_bytes["data"]
                )

                send_email(
                    mail,
                    subject="Diyabet Takip Giriş Bilgileri",
                    content=f"""
    Merhaba,

    Diyabet Takip Sistemine giriş bilgileriniz aşağıdadır:

    T.C. Kimlik No: {tc}
    Şifre: {pw}

    Sağlıklı günler dileriz.
                    """
                )
            except Exception as ex:
                messagebox.showerror("Hata", str(ex))
                return

            messagebox.showinfo("Başarılı", "Hasta eklendi!")
            win.destroy()

            # Listeyi güncelle
            self._all_patients = Repo.list_patients(self.user['id'])
            self.lst.delete(0, tk.END)
            for p in self._all_patients:
                self.lst.insert(tk.END, f"{p['id']} - {p['tc_kimlik_no']}")

        # Kaydet butonu → en alta ekle
        tk.Button(win, text="Kaydet", command=kaydet, width=18,
                bg="#2980B9", fg="white").grid(row=8, column=0, columnspan=2, pady=12)

    # ---------- Yardımcı ----------

    def _selected_pid(self):
        sel = self.lst.curselection()
        return int(self.lst.get(sel[0]).split()[0]) if sel else None

    # ---------- Panel Fonksiyonları ----------

    def uyari(self):
        pid = self._selected_pid()
        if pid is None:
            return

        tarih_obj = None
        if self.only_today.get():
            t = simpledialog.askstring(
                "Tarih",
                "GG.AA.YYYY biçiminde tarihi girin\n"
                "(boş bırak → sadece BUGÜN):"
            )
            if t is None:
                return
            if t.strip() == "":
                tarih_obj = datetime.date.today()
            else:
                try:
                    tarih_obj = datetime.datetime.strptime(
                        t.strip(), "%d.%m.%Y").date()
                except ValueError:
                    messagebox.showerror(
                        "Hata", "Tarih GG.AA.YYYY biçiminde olmalı")
                    return

        alerts = Repo.alerts_of_patient(pid)
        if tarih_obj:
            alerts = [a for a in alerts if a['tarih'] == tarih_obj]

        win = tk.Toplevel(self)
        win.title("Uyarılar")

        if not alerts:
            tk.Label(win, text="Uyarı bulunamadı").pack(padx=20, pady=10)
            return

        for a in alerts:
            tarih = a["tarih"].strftime("%d.%m.%Y") if isinstance(
                a["tarih"], (datetime.date, datetime.datetime)) else str(a["tarih"])
            saat = a["saat"].strftime("%H:%M:%S") if isinstance(
                a["saat"], datetime.time) else (a["saat"] if a["saat"] else "--:--")
            seviye = f"{a['sugar_level']} mg/dL" if a["sugar_level"] is not None else "-"
            alert_type = a["alert_type"] or "Uyarı"

            tk.Label(
                win,
                text=f"{tarih} {saat} → {alert_type} ({seviye})"
            ).pack(anchor="w", padx=8)

    def ort(self):
        pid = self._selected_pid()
        if pid is None:
            return

        tarih_str = simpledialog.askstring(
            "Tarih",
            "Lütfen tarihi GG.AA.YYYY biçiminde girin:",
            parent=self
        )
        if not tarih_str:
            return

        try:
            tarih_obj = datetime.datetime.strptime(tarih_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        row = Repo._single("""
            SELECT ortalama_kan_sekeri
            FROM v_gunluk_kan_sekeri
            WHERE patient_id=%s AND tarih=%s
        """, pid, tarih_obj)

        msg = (
            f"{tarih_str} için ortalama: {row['ortalama_kan_sekeri']} mg/dL"
            if row else f"{tarih_str} tarihinde ölçüm yapılmamış."
        )
        messagebox.showinfo("Günlük Ortalama", msg)


    def egz_diyet(self):
        pid = self._selected_pid()
        if pid is None:
            return
        ex = Repo.exercise_percent(pid)
        diet = Repo.diet_percent(pid)

        win = tk.Toplevel(self)
        win.title("Egzersiz / Diyet Geçmişi")
        txt = tk.Text(win, width=60, height=20)
        txt.pack(padx=10, pady=8)

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        dates = {r['exercise_date']
                 for r in ex} | {r['diet_date'] for r in diet}
        for d in sorted(dates):
            e = next((r['oran'] for r in ex if r['exercise_date'] == d), "-")
            di = next((r['oran'] for r in diet if r['diet_date'] == d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    def tablo(self):
        pid = self._selected_pid()
        if pid is None:
            return
        rows = Repo.measurement_table(pid)
        win = tk.Toplevel(self)
        win.title("Kan Şekeri Tablosu")

        tree = ttk.Treeview(
            win, columns=("tarih", "saat", "deger"), show="headings")
        tree.heading("tarih", text="Tarih")
        tree.heading("saat", text="Saat")
        tree.heading("deger", text="Kan Şekeri (mg/dL)")
        tree.pack(fill="both", expand=True, padx=10, pady=8)

        for row in rows:
            tree.insert("", "end",
                        values=(row['tarih'], row['saat'], row['deger']))

    def grafik(self):
        pid = self._selected_pid()
        if pid is None:
            return
        rows = Repo.daily_graph_data(pid)
        if not rows:
            messagebox.showwarning(
                "Veri Yok", "Günlük grafik oluşturulacak veri yok")
            return

        tarih = [r['tarih'] for r in rows]
        ort = [r['ortalama'] for r in rows]

        win = tk.Toplevel(self)
        win.title("Zaman Bazlı Kan Şekeri Değişimi")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(tarih, ort, marker="o")
        ax.set_title("Günlük Kan Şekeri Ortalamaları")
        ax.set_ylabel("mg/dL")
        ax.set_xlabel("Tarih")
        ax.grid(True)

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()

        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(
            fill="both", expand=True)

    # -----------------------------------------------------------------
    #  YENİ  arsiv  (doktor.py)
    # -----------------------------------------------------------------
    def arsiv(self):
        """Seçili hastanın bütün kayıtlarını (ölçüm-egz-diyet-uyarı) gösterir."""
        pid = self._selected_pid()
        if pid is None:
            return

        rows = Repo.patient_archive(pid)        # tarih-sıralı birleşik liste
        if not rows:
            messagebox.showinfo("Bilgi", "Kayıt bulunamadı.")
            return

        win = tk.Toplevel(self)
        win.title("Arşiv Verileri")
        txt = tk.Text(win, width=70, height=22)
        txt.pack(padx=8, pady=8)

        last_date = None
        for r in rows:
            d = r["tarih"].strftime("%Y-%m-%d")      # aynı formatta yazalım
            if last_date and d != last_date:
                txt.insert("end", "-"*40 + "\n")      # 🔹 tarih değişti → ayırıcı
            last_date = d

            line = f"{d} {r['veri_tipi']}: {r['icerik']}\n"
            txt.insert("end", line)

        txt.config(state="disabled")

        # =======================================================
    #  🆕  Doktorun belirtileri girip “Öneri Oluştur”duğu form
    # =======================================================
    def _open_symptom_form(self):
        pid = self._selected_pid()
        if pid is None:
            messagebox.showwarning(
                "Uyarı", "Lütfen önce listeden bir hasta seçin.")
            return

        win = tk.Toplevel(self)
        win.title("Belirti Girişi ve Öneri Oluştur")
        win.configure(bg=BG)
        win.resizable(False, False)

        # --- ilk kan şekeri --------------------------------
        tk.Label(win, text="İlk Kan Şekeri (mg/dL):", bg=BG
                 ).grid(row=0, column=0, sticky="e", padx=6, pady=4)
        e_sugar = tk.Entry(win, width=10, justify="center")
        e_sugar.grid(row=0, column=1, pady=4)

        # --- belirtiler ------------------------------------
        symptoms = [
            "Poliüri", "Polifaji", "Polidipsi", "Nöropati",
            "Kilo Kaybı", "Yorgunluk", "Yaraların Yavaş İyileşmesi", "Bulanık Görme"
        ]
        vars_ = {}
        tk.Label(win, text="Belirtiler:", bg=BG
                 ).grid(row=1, column=0, sticky="ne", padx=6, pady=4)
        frm_sym = tk.Frame(win, bg=BG)
        frm_sym.grid(row=1, column=1, sticky="w")
        for i, s in enumerate(symptoms):
            v = tk.IntVar(value=0)
            vars_[s] = v
            tk.Checkbutton(frm_sym, text=s, variable=v, bg=BG
                           ).grid(row=i//2, column=i % 2, sticky="w")

        # --- öneri kutuları --------------------------------
        tk.Label(win, text="Diyet Önerisi:", bg=BG
                 ).grid(row=5, column=0, sticky="e", padx=6, pady=(10, 4))
        e_diet = tk.Entry(win, width=25)
        e_diet.grid(row=5, column=1, pady=(10, 4))

        tk.Label(win, text="Egzersiz Önerisi:", bg=BG
                 ).grid(row=6, column=0, sticky="e", padx=6, pady=4)
        e_ex = tk.Entry(win, width=25)
        e_ex.grid(row=6, column=1, pady=4)

    # --- ÖNERİ OLUŞTUR düğmesi --------------------------
        def _generate():
            try:
                sugar = float(e_sugar.get())
            except ValueError:
                messagebox.showerror("Hata", "Şeker değeri sayı olmalı.")
                return
            sel_sym = [k for k, v in vars_.items() if v.get()]
            diet, ex = self._calc_reco(sugar, sel_sym)

            e_diet.delete(0, tk.END)
            e_ex.delete(0, tk.END)
            e_diet.insert(0, diet)
            e_ex.insert(0, ex)

        tk.Button(win, text="Öneri Oluştur", command=_generate,
                  bg="#2980B9", fg="white", width=18).grid(
            row=7, column=0, pady=(12, 4))

        def _save():
            diet_plan = e_diet.get().strip()
            ex_plan = e_ex.get().strip()
            if not (diet_plan and ex_plan):
                messagebox.showwarning("Uyarı", "Önce öneri oluşturun veya girin.")
                return

            # 🔹 SEÇİLEN BELİRTİLERİ TOPLA
            selected = [k for k, v in vars_.items() if v.get()]
            all_symptoms = [
                "Poliüri", "Polifaji", "Polidipsi", "Nöropati",
                "Kilo Kaybı", "Yorgunluk", "Yaraların Yavaş İyileşmesi", "Bulanık Görme"
            ]
            symptom_id_map = {name: idx+1 for idx, name in enumerate(all_symptoms)}  # ID'ler 1'den başlıyor
            selected_ids = [symptom_id_map[name] for name in selected]

            # 🔧 EKLE: BELİRTİLERİ VERİTABANINA KAYDET
            Repo.log_symptoms(pid, selected_ids)

            # 🔧 EKLE: PLAN VERİTABANINA KAYDET
            Repo.assign_plan(pid, diet_plan, ex_plan)

            # ✔️ Ekrana sabit başarı mesajı ekle
            lbl_success = tk.Label(win, text="✔️ Öneri ve belirtiler kaydedildi",
                                fg="green", bg=BG, font=("Segoe UI", 10, "bold"))
            lbl_success.grid(row=8, column=0, columnspan=2, pady=(10, 4))

        tk.Button(win, text="Kaydet", command=_save,
                  bg="#27AE60", fg="white", width=18).grid(
            row=7, column=1, pady=(12, 4))

    def gun_ici(self):
        pid = self._selected_pid()
        if pid is None:
            return

        tarih_str = tk.simpledialog.askstring(
            "Tarih", "GG.AA.YYYY biçiminde tarih girin:")
        if not tarih_str:
            return
        try:
            tarih_obj = datetime.datetime.strptime(
                tarih_str, "%d.%m.%Y").date()
        except ValueError:
            tk.messagebox.showerror(
                "Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        rows = Repo.slot_measurements_on(pid, tarih_obj)
        if not rows:
            tk.messagebox.showwarning("Veri Yok",
                                      "Bu tarihe ait veri yok.")
            return

        slotlar = ["Sabah", "Öğle", "İkindi", "Akşam", "Gece"]
        veriler = {row['time_slot']: row['sugar_level'] for row in rows}
        x = slotlar
        y = [veriler.get(slot, None) for slot in slotlar]

        if all(v is None for v in y):
            tk.messagebox.showinfo(
                "Veri Yok", "Bu tarihte hiçbir ölçüm yapılmamış.")
            return

        win = tk.Toplevel(self)
        win.title(f"{tarih_str} Kan Şekeri Gün İçi Değişimi")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(x, y, marker="o")
        ax.set_ylabel("mg/dL")
        ax.set_title(f"{tarih_str} Gün İçi Değişim")
        ax.grid(True)
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(
            fill="both", expand=True)

    def uyari(self):
        pid = self._selected_pid()
        if pid is None:
            return

        alerts = Repo.alerts_of_patient(pid, only_today=self.only_today.get())

        win = tk.Toplevel(self)
        win.title("Uyarılar")

        if not alerts:
            tk.Label(win, text="Uyarı bulunamadı").pack(padx=20, pady=10)
            return

        for a in alerts:
            tarih = a["tarih"] if isinstance(a["tarih"], str) else a["tarih"].strftime("%d.%m.%Y")

            # Saat varsa ve 23:59 ise gizle
            if isinstance(a["saat"], datetime.time) and a["saat"] == datetime.time(23, 59):
                saat_str = "--:--"
            else:
                saat_str = a["saat"].strftime("%H:%M:%S") if isinstance(a["saat"], datetime.time) else (a["saat"] or "--:--")

            # Şeker seviyesi varsa parantezli göster
            if a["sugar_level"] is not None:
                metin = f"{tarih} {saat_str} → {a['alert_type']} ({a['sugar_level']} mg/dL)"
            else:
                metin = f"{tarih} {saat_str} → {a['alert_type']}"

            tk.Label(win, text=metin).pack(anchor="w")


    def _calc_reco(self, sugar: float, sy_list: list[str]) -> tuple[str, str]:
        """PDF’teki kural tablosuna %100 uyumlu öneri döner."""
        s = set(sy_list)

        # --- < 70 mg/dL ------------------------------------
        if sugar < 70 and s & {"Nöropati", "Polifaji", "Yorgunluk"}:
            return "Dengeli Beslenme", "Yok"

        # --- 70-110 mg/dL ----------------------------------
        if 70 <= sugar <= 110:
            if {"Yorgunluk", "Kilo Kaybı"}.issubset(s):
                return "Az Şekerli Diyet", "Yürüyüş"
            if {"Polifaji", "Polidipsi"}.issubset(s):
                return "Dengeli Beslenme", "Yürüyüş"

        # --- 110-180 mg/dL ---------------------------------
        if 110 <= sugar <= 180:
            if {"Bulanık Görme", "Nöropati"}.issubset(s):
                return "Az Şekerli Diyet", "Klinik Egzersiz"
            if {"Poliüri", "Polidipsi"}.issubset(s):
                return "Şekersiz Diyet", "Klinik Egzersiz"
            if {"Yorgunluk", "Nöropati", "Bulanık Görme"}.issubset(s):
                return "Az Şekerli Diyet", "Yürüyüş"

        # --- ≥ 180 mg/dL -----------------------------------
        if sugar >= 180:
            if {"Yaraların Yavaş İyileşmesi", "Polifaji", "Polidipsi"}.issubset(s):
                return "Şekersiz Diyet", "Klinik Egzersiz"
            if {"Yaraların Yavaş İyileşmesi", "Kilo Kaybı"}.issubset(s):
                return "Şekersiz Diyet", "Yürüyüş"

        # eşleşme yoksa
        return "", ""
    
    
    # ➌ --- PROFİL DÜZENLE PENCERESİ ------------------------------
    def _edit_profile(self):
        prof = Repo.get_profile(self.user["id"])
        win  = tk.Toplevel(self)
        win.title("Profil Düzenle")
        win.configure(bg=BG)
        win.resizable(False, False)

        # Alanlar
        tk.Label(win, text="E-posta:", bg=BG).grid(row=0, column=0, sticky="e", padx=6, pady=4)
        e_mail = tk.Entry(win, width=30)
        e_mail.grid(row=0, column=1, pady=4)
        e_mail.insert(0, prof["email"] or "")

        tk.Label(win, text="Doğum (GG-AA-YYYY):", bg=BG).grid(row=1, column=0, sticky="e", padx=6, pady=4)
        e_bd = tk.Entry(win, width=30)
        e_bd.grid(row=1, column=1, pady=4)
        e_bd.insert(0, str(prof["birth_date"]) if prof["birth_date"] else "")

        tk.Label(win, text="Cinsiyet (E/K):", bg=BG).grid(row=2, column=0, sticky="e", padx=6, pady=4)
        e_gn = tk.Entry(win, width=30)
        e_gn.grid(row=2, column=1, pady=4)
        e_gn.insert(0, prof["gender"] or "")

        # Fotoğraf seçici
        tk.Label(win, text="Yeni Fotoğraf:", bg=BG).grid(row=3, column=0, sticky="e", padx=6, pady=4)
        lbl_file = tk.Label(win, text="(seçilmedi)", bg=BG)
        lbl_file.grid(row=3, column=1, sticky="w")

        photo_bytes = {"data": None}

        def choose():
            path = filedialog.askopenfilename(
                title="Fotoğraf seç",
                filetypes=[("Resim", "*.png;*.jpg;*.jpeg")]
            )
            if path:
                lbl_file.config(text=os.path.basename(path))
                with open(path, "rb") as f:
                    photo_bytes["data"] = f.read()
# 📌 Pencereyi tekrar öne getir
                win.lift()
                win.focus_force()
        tk.Button(win, text="Seç", command=choose).grid(row=3, column=1, sticky="e", padx=6)

        # Kaydet
        def _save():
            mail = e_mail.get().strip()
            bd = None
            bd_str = e_bd.get().strip()
            if bd_str:
                try:
                    bd = datetime.date.fromisoformat(bd_str)
                except ValueError:
                    messagebox.showerror("Hata", "Doğum tarihi GG-AA-YYYY olmalı")
                    return

            Repo.update_profile(
                self.user["id"],
                email=mail or None,
                birth_date=bd,
                gender=e_gn.get().strip().upper() or None,
                photo_bytes=photo_bytes["data"]
            )
            messagebox.showinfo("Başarılı", "Profil güncellendi!")
            win.destroy()
            self.destroy()
            DoktorWin(self.user).mainloop()

        tk.Button(
            win, text="Kaydet", command=_save,
            bg="#2980B9", fg="white", width=20
        ).grid(row=4, column=0, columnspan=2, pady=12)



    def _show_ex_diet(self):
        pid = self._selected_pid()
        if pid is None:
            return

        win = tk.Toplevel(self)
        win.title("Egzersiz / Diyet Geçmişi")
        cols = ("Tarih", "Egzersiz %", "Diyet %")
        tv = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, anchor="center")
        tv.pack(fill="both", expand=True)

        ex = Repo.exercise_percent(pid)
        di = Repo.diet_percent(pid)
        dates = {r["exercise_date"] for r in ex} | {r["diet_date"] for r in di}
        for d in sorted(dates):
            e = next((r["oran"] for r in ex if r["exercise_date"] == d), "-")
            dd = next((r["oran"] for r in di if r["diet_date"] == d), "-")
            tv.insert("", "end", values=(d, e, dd))


    def _kural_oner(self):
        pid = self._selected_pid()
        if pid is None:
            return

        sugar = Repo._single("""
            SELECT sugar_level FROM blood_sugar_measurements
            WHERE patient_id=%s ORDER BY measurement_time DESC LIMIT 1
        """, pid)
        if not sugar:
            messagebox.showwarning("Veri Yok", "Bu hastaya ait şeker ölçüm verisi bulunamadı.")
            return

        today_symp = [r["symptom_id"] for r in Repo._list("""
            SELECT symptom_id FROM symptom_logs
            WHERE patient_id=%s AND symptom_date=CURDATE()
        """, pid)]

    # doktor.py içinde:
        diet, ex = Repo.generate_recommendation(sugar["sugar_level"], today_symp)


        if not diet and not ex:
            messagebox.showinfo("Bilgi", "Uygun öneri bulunamadı.")
            return

        if messagebox.askyesno("Öneri", f"Diyet: {diet}\nEgzersiz: {ex}\n\nPlanı hastaya atamak ister misiniz?"):
            Repo.assign_plan(pid, diet, ex)
            messagebox.showinfo("Başarılı", "Plan hastaya başarıyla kaydedildi.")

    def _gun_sonu_al(self):
        tarih_str = simpledialog.askstring(
            "Gün Sonu", "Tarih girin (GG.AA.YYYY):", parent=self
        )
        if not tarih_str:
            return

        try:
            tarih_obj = datetime.datetime.strptime(tarih_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        # 🔑  Tek satırda kontrol + uyarı üret
        Repo.check_and_alert_incomplete_days(tarih_obj)

        messagebox.showinfo(
            "Tamamlandı",
            f"{tarih_obj.strftime('%d.%m.%Y')} ve öncesi günler için kontrol bitti."
        )


    # ---------------------------------------------------------------
    #  YENİ  _egz_diyet_grafik  (doktor.py)
    # ---------------------------------------------------------------
    def _egz_diyet_grafik(self):
        """Seçili hasta için günlük egzersiz / diyet yüzdelerini çubuk grafikte gösterir."""
        pid = self._selected_pid()
        if pid is None:
            return

        ex   = Repo.exercise_percent(pid)   # [{'exercise_date': date, 'oran': 100.0}, ...]
        diet = Repo.diet_percent(pid)       # [{'diet_date': date,    'oran':  80.0}, ...]

        if not ex and not diet:
            messagebox.showinfo("Bilgi", "Bu hasta için veri yok.")
            return

        # ---------- verileri hizala ----------
        all_dates = sorted({r['exercise_date'] for r in ex} |
                           {r['diet_date']     for r in diet})
        if not all_dates:                    # veri yine yoksa
            messagebox.showinfo("Bilgi", "Bu hasta için veri yok.")
            return

        x_lbl     = [d.strftime("%d.%m") for d in all_dates]
        ex_vals   = [next((r['oran'] for r in ex   if r['exercise_date']==d),  0) for d in all_dates]
        diet_vals = [next((r['oran'] for r in diet if r['diet_date']==d), 0) for d in all_dates]

        # ---------- pencere & çubuk grafik ----------
        win = tk.Toplevel(self)
        win.title("Egzersiz / Diyet Yüzdesi (Çubuk)")

        fig, ax = plt.subplots(figsize=(7, 4))

        import numpy as np
        ind   = np.arange(len(all_dates))
        width = 0.35                              # çubuk genişliği

        bars1 = ax.bar(ind - width/2, ex_vals,   width, label="Egzersiz")
        bars2 = ax.bar(ind + width/2, diet_vals, width, label="Diyet")

        # Ekseni/başlığı ayarla
        ax.set_xticks(ind)
        ax.set_xticklabels(x_lbl, rotation=45, ha="right")
        ax.set_ylim(0, 100)
        ax.set_ylabel("%")
        ax.set_title("Günlük Uygulama Yüzdeleri")
        ax.legend()
        ax.grid(axis="y", linestyle="--", linewidth=0.4)

        # Çubukların üstüne değer etiketi
        for bar in list(bars1) + list(bars2):
            h = bar.get_height()
            ax.annotate(f"{h:.0f}",
                        xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(fill="both", expand=True)

    def _filter_patients(self):
        """
        Hastaları, tüm ölçüm değerlerinin ORTALAMASINA göre
        en düşükten en yükseğe sıralayıp yeni bir pencerede gösterir.
        Ölçüm yoksa "ölçüm yok" olarak en sonda listelenir.
        """
        # 1) Her hasta için ortalama kan şekeri değerini al
        enriched = []  # list of (hasta_kaydı, ortalama | None)
        for p in self._all_patients:
            row = Repo._single(
                "SELECT ROUND(AVG(sugar_level),1) AS ort FROM blood_sugar_measurements WHERE patient_id=%s",
                p["id"]
            )
            ort = row["ort"] if row and row["ort"] is not None else None
            enriched.append((p, ort))

        # 2) Sırala: None (ölçüm yok) en sona
        enriched.sort(key=lambda t: (t[1] is None, t[1] or 0))

        # 3) Yeni pencere oluştur
        win = tk.Toplevel(self)
        win.title("Hasta Ortalamalarına Göre Sıralama")
        cols = ("Hasta", "Tc Kimlik", "Ortalama (mg/dL)")
        tv = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, anchor="center")
            tv.grid(row=0, column=0, columnspan=2, padx=8, pady=8)
        # 4) Veriyi Treeview'a ekle
        for p, ort in enriched:
            ort_str = f"{ort}" if ort is not None else "ölçüm yok"
            tv.insert("", "end",
                      values=(p["id"], p["tc_kimlik_no"], ort_str))

        # 5) Eğer hiç ölçüm yoksa kullanıcıyı bilgilendir
        if all(ort is None for _, ort in enriched):
            messagebox.showinfo(
                "Bilgi",
                "Hiç ölçüm yapılmamış; ortalama sıralama için veri yok."
            )


        def _uygula():
            secim = cb.get()
            yeni_liste = []
            for p in self._all_patients:
                lvl = Repo.last_sugar_level(p["id"])

                # --- ①  YENİ KOŞUL ---------------------------------
                if lvl is None:
                    if secim == "Tümü":          # ‘Tümü’ ise listeye AL
                        yeni_liste.append(p)
                    continue                      # diğer aralıklarda yine atla
                # ----------------------------------------------------

                keep = (
                    secim == "Tümü" or
                    (secim == "< 70"   and lvl < 70) or
                    (secim == "70-110" and 70  <= lvl <= 110) or
                    (secim == "111-150" and 111 <= lvl <= 150) or
                    (secim == "151-200" and 151 <= lvl <= 200) or
                    (secim == "> 200"  and lvl > 200)
                )
                if keep:
                    yeni_liste.append(p)

        def _sifirla():
            self._all_patients = Repo.list_patients(self.user["id"])   # ← EKLENDİ
            self.lst.delete(0, "end")
            for p in self._all_patients:
                self.lst.insert("end", f"{p['id']} - {p['tc_kimlik_no']}")
            win.destroy()


        tk.Button(win, text="Uygula", command=_uygula, width=10).grid(row=1, column=0, pady=10)
        tk.Button(win, text="Tümünü Göster", command=_sifirla, width=12).grid(row=1, column=1, pady=10)


        # ---------------------------------------------------------------
    #  BELİRTİYE GÖRE FİLTRELE – YENİ PENCEREDE SONUÇ
    # ---------------------------------------------------------------
    def _filter_by_symptoms(self):
        """
        Seçilen belirtilere sahip hastaları AYRI bir pencerede listeler.
        Ana “Hastalarınız” listbox’una dokunmaz.
        """
        # 1) Hasta listesini hazırla (önceden alınmamışsa)
        if not hasattr(self, "_all_patients"):
            self._all_patients = Repo.list_patients(self.user["id"])

        # 2) Belirti seçme penceresi ------------------------------------------------
        sel_win = tk.Toplevel(self)
        sel_win.title("Belirti Seç")
        sel_win.configure(bg=BG)
        sel_win.resizable(False, False)

        symptom_names = [
            "Poliüri", "Polifaji", "Polidipsi", "Nöropati",
            "Kilo Kaybı", "Yorgunluk", "Yaraların Yavaş İyileşmesi",
            "Bulanık Görme"
        ]
        vars_ = {}
        for i, s in enumerate(symptom_names):
            v = tk.IntVar(value=0)
            vars_[s] = v
            tk.Checkbutton(sel_win, text=s, variable=v, bg=BG).grid(
                row=i, column=0, sticky="w", padx=8, pady=2
            )

        # 3) Filtrele → sonuçları YENİ pencereye bas -------------------------------
        def _filtrele():
            secilen = [k for k, v in vars_.items() if v.get()]
            if not secilen:
                messagebox.showwarning("Uyarı", "En az bir belirti seçmelisiniz.",
                                       parent=sel_win)
                return

            matched_ids = Repo.patients_with_symptoms(secilen)
            if not matched_ids:
                messagebox.showinfo("Bilgi",
                                    "Seçilen belirtilere sahip hasta bulunamadı.",
                                    parent=sel_win)
                return

            # --- SONUÇ PENCERESİ --------------------------------------------------
            res_win = tk.Toplevel(self)
            title_symp = ", ".join(secilen)
            res_win.title(f"{title_symp} Belirtisine Sahip Hastalar")
            res_win.configure(bg=BG)
            res_win.geometry("+300+200")  # ekrana orta-yakın aç

            cols = ("Hasta ID", "TC Kimlik No")
            tv = ttk.Treeview(res_win, columns=cols, show="headings", height=10)
            for c in cols:
                tv.heading(c, text=c)
                tv.column(c, anchor="center")
            tv.pack(fill="both", expand=True, padx=10, pady=10)

            for p in self._all_patients:
                if p["id"] in matched_ids:
                    tv.insert("", "end", values=(p["id"], p["tc_kimlik_no"]))

            # Bilgi etiketi (kaç hasta bulundu)
            lbl = tk.Label(res_win,
                           text=f"Toplam {len(tv.get_children())} hasta bulundu.",
                           bg=BG, font=("Segoe UI", 10, "italic"))
            lbl.pack(pady=(0, 8))

            sel_win.destroy()  # seçim penceresini kapat

        # 4) İptal / Sıfırla -------------------------------------------------------
        def _iptal():
            sel_win.destroy()

        btn_frm = tk.Frame(sel_win, bg=BG)
        btn_frm.grid(row=len(symptom_names), column=0, pady=10)
        tk.Button(btn_frm, text="Filtrele", command=_filtrele,
                  bg="#2980B9", fg="white", width=12).pack(side="left", padx=6)
        tk.Button(btn_frm, text="İptal", command=_iptal,
                  bg="#A6ACAF", fg="white", width=12).pack(side="left", padx=6)



    # ──────────────────────────────────────────────────────────
    #  ŞEKER × EGZERSİZ / DİYET GRAFİĞİ
    # ──────────────────────────────────────────────────────────
    def _sugar_diet_ex_graph(self):
        pid = self._selected_pid()
        if pid is None:
            return

        # 1) tarih iste
        t_str = simpledialog.askstring(
            "Tarih", "GG.AA.YYYY biçiminde tarih girin:", parent=self)
        if not t_str:
            return
        try:
            day = datetime.datetime.strptime(t_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih biçimi GG.AA.YYYY olmalı.")
            return

        rows = Repo.sugar_diet_exercise_data(pid, day)
        if not rows:
            messagebox.showinfo("Bilgi", "Seçilen güne ait veri yok.")
            return

        # 2) verileri ayıkla
        saat = [
            (datetime.datetime.min + r['tm']).strftime("%H:%M:%S")
            if isinstance(r['tm'], datetime.timedelta)
            else r['tm'].strftime("%H:%M:%S")
            for r in rows
        ]        
        seviye = [r['lvl'] for r in rows]
        egz_ok = any(r['ex'] for r in rows)
        diy_ok = any(r['di'] for r in rows)

        # 3) pencere & grafik
        win = tk.Toplevel(self)
        win.title(f"{t_str}  |  Şeker × Egzersiz / Diyet")

        fig, ax1 = plt.subplots(figsize=(7, 3.5))
        ax1.plot(saat, seviye, marker="o", label="Kan Şekeri")
        ax1.set_ylabel("mg/dL")
        ax1.set_xlabel("Saat")
        ax1.set_title("Kan Şekeri Seviyesi")

        # – Egzersiz/Diyet bilgisi (ikincil eksen, 0 = hayır, 1 = var) –
        ax2 = ax1.twinx()
        ax2.set_ylim(0, 1.2)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(["YOK", "VAR"])
        ax2.grid(False)

        if egz_ok:
            ax2.step(saat, [r['ex'] for r in rows],
                     where='mid', linestyle="--", label="Egzersiz")
        if diy_ok:
            ax2.step(saat, [r['di'] for r in rows],
                     where='mid', linestyle=":", label="Diyet")

        # – açıklama kutusu –
        lines1, labs1 = ax1.get_legend_handles_labels()
        lines2, labs2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1+lines2, labs1+labs2, loc="upper right")

        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(
            fill="both", expand=True) 