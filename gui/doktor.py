# =============================================================
# gui/doktor.py  —  Hasta ekleme ve “Gün İçi Değişim” düzeltildi
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import io
from utils import send_email
from repository import Repo

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
        if self._profile and self._profile['photo_blob']:
            img = Image.open(io.BytesIO(
                self._profile['photo_blob'])).resize((80, 80))
            self._photo_tk = ImageTk.PhotoImage(img)
            tk.Label(self, image=self._photo_tk, bg=BG).place(relx=0.02, rely=0.01)

        # 🔽 Profil resmi olsun olmasın mutlaka oluşturulmalı!
        cont = tk.Frame(self, bg=BG)
        cont.place(relx=0.5, rely=0.05, anchor="n")

        tk.Label(cont, text="Hastalarınız", font=("Segoe UI", 20, "bold"), bg=BG
                ).grid(row=0, column=0, padx=6, pady=4)

        self.lst = tk.Listbox(cont, height=20, width=30)
        self.lst.grid(row=1, column=0, rowspan=8, padx=6, pady=4)

        for p in Repo.list_patients(user['id']):
            self.lst.insert(tk.END, f"{p['id']} - {p['tc_kimlik_no']}")

        # Butonlar
        tk.Button(cont, text="Uyarıları Göster", command=self.uyari,
                width=25).grid(row=1, column=1, pady=4)
        tk.Button(cont, text="Günlük Ortalama", command=self.ort,
                width=25).grid(row=2, column=1, pady=4)
        tk.Button(cont, text="Egzersiz/Diyet Geçmişi",
                command=self.egz_diyet, width=25).grid(row=3, column=1, pady=4)
        tk.Button(cont, text="Kan Şekeri Tablosu", command=self.tablo,
                width=25).grid(row=4, column=1, pady=4)
        tk.Button(cont, text="Grafiksel Değişim", command=self.grafik,
                width=25).grid(row=5, column=1, pady=4)
        tk.Button(cont, text="Arşiv Verileri", command=self.arsiv,
                width=25).grid(row=6, column=1, pady=4)
        tk.Button(cont, text="Gün İçi Değişim", command=self.gun_ici,
                width=25).grid(row=7, column=1, pady=4)

        # 🆕 Hasta ekleme butonu
        tk.Button(cont, text="Hasta Ekle", command=self._hasta_ekle, width=25,
                  bg="#28B463", fg="white").grid(row=8, column=1, pady=(12, 4))

    # =====================
    # 🆕 HASTA EKLE PENCERESİ
    # =====================
    def _hasta_ekle(self):
        win = tk.Toplevel(self)
        win.title("Yeni Hasta Tanımla")
        win.configure(bg=BG)
        win.resizable(False, False)

        row = 0

        def add_label(text):
            nonlocal row
            tk.Label(win, text=text, bg=BG).grid(
                row=row, column=0, sticky="e", padx=6, pady=4)
            row += 1

        add_label("T.C. Kimlik No:")
        e_tc = tk.Entry(win, width=25)
        e_tc.grid(row=0, column=1, pady=4)

        add_label("Şifre:")
        e_pw = tk.Entry(win, width=25)
        e_pw.grid(row=1, column=1, pady=4)

        add_label("E-posta:")
        e_mail = tk.Entry(win, width=25)
        e_mail.grid(row=2, column=1, pady=4)

        add_label("Doğum Tarihi (YYYY-MM-DD):")
        e_bd = tk.Entry(win, width=25)
        e_bd.grid(row=3, column=1, pady=4)

        add_label("Cinsiyet (E/K):")
        e_gn = tk.Entry(win, width=25)
        e_gn.grid(row=4, column=1, pady=4)

        add_label("Fotoğraf (isteğe bağlı):")
        frm_photo = tk.Frame(win, bg=BG)
        frm_photo.grid(row=5, column=1, pady=4)
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

        tk.Button(frm_photo, text="Seç",
                  command=choose_file).pack(side="left", padx=6)

        def kaydet():
            tc, pw, mail = (e_tc.get().strip(),
                            e_pw.get().strip(),
                            e_mail.get().strip())
            bd_str = e_bd.get().strip()
            c = e_gn.get().strip().upper()
            gn = "Erkek" if c == "E" else "Kadın" if c == "K" else None


            if not (tc and pw and mail):
                messagebox.showerror("Hata", "TC, şifre ve e-posta zorunlu.")
                return

            try:
                bd = datetime.date.fromisoformat(bd_str) if bd_str else None
            except ValueError:
                messagebox.showerror("Hata", "Doğum tarihi YYYY-MM-DD olmalı")
                return

            try:
                Repo.create_patient(
                    tc, pw, self.user['id'], mail, bd, gn, photo_bytes["data"]
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



            # listeyi yenile
            self.lst.delete(0, tk.END)
            for p in Repo.list_patients(self.user['id']):
                self.lst.insert(tk.END, f"{p['id']} - {p['tc_kimlik_no']}")

        tk.Button(win, text="Kaydet", command=kaydet, width=18,
                  bg="#2980B9", fg="white").grid(row=6, column=0,
                   columnspan=2, pady=12)
                  

    # ---------- Yardımcı ----------
    def _selected_pid(self):
        sel = self.lst.curselection()
        return int(self.lst.get(sel[0]).split()[0]) if sel else None

    # ---------- Panel Fonksiyonları ----------
    def uyari(self):
        pid = self._selected_pid()
        if pid is None:
            return
        alerts = Repo.alerts_of_patient(pid)
        win = tk.Toplevel(self)
        win.title("Uyarılar")
        if not alerts:
            tk.Label(win, text="Güncel uyarı yok").pack(padx=20, pady=10)
            return
        for a in alerts:
            tk.Label(
                win,
                text=f"{a['tarih']} {a['saat']} → {a['alert_type']} "
                f"({a['sugar_level']} mg/dL)"
            ).pack(anchor="w")

    def ort(self):
        pid = self._selected_pid()
        if pid is None:
            return
        row = Repo.daily_summary(pid)
        msg = (
            f"Bugünkü ortalama: {row['ortalama_kan_sekeri']} mg/dL"
            if row else "Bugün ölçüm yok"
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

    def arsiv(self):
        pid = self._selected_pid()
        if pid is None:
            return
        rows = Repo.patient_archive(pid)
        win = tk.Toplevel(self)
        win.title("Arşiv Verileri")
        txt = tk.Text(win, width=80, height=25)
        txt.pack(padx=10, pady=10)
        for row in rows:
            txt.insert(
                "end", f"{row['tarih']} {row['veri_tipi']}: {row['icerik']}\n")
        txt.config(state="disabled")

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
