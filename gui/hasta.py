# =============================================================
# gui/hasta.py  —  Profil görüntüleme + düzenleme entegre
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import datetime
import io
import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from repository import Repo

BG = "#EAF2F8"

# ---------- mevcut fonksiyon ----------


def insulin_dose(avg: float) -> str:
    if avg < 70:
        return ""
    elif avg <= 110:
        return ""
    elif avg <= 150:
        return "1 ml"
    elif avg <= 200:
        return "2 ml"
    else:
        return "3 ml"


class HastaWin(tk.Tk):
    SUNUM_MODU = True

    TIME_SLOTS = {
        "Sabah":  (datetime.time(7, 0),  datetime.time(8, 0)),
        "Öğle":   (datetime.time(12, 0), datetime.time(13, 0)),
        "İkindi": (datetime.time(15, 0), datetime.time(16, 0)),
        "Akşam":  (datetime.time(18, 0), datetime.time(19, 0)),
        "Gece":   (datetime.time(22, 0), datetime.time(23, 59)),
    }
    COLS = ["Tarih", "Sabah", "Öğle", "İkindi", "Akşam", "Gece", "İnsülin"]
    IDX = {c: i for i, c in enumerate(COLS)}

    # ---------- yardımcı ----------
    @classmethod
    def _slot_from_time(cls, t: datetime.time) -> str | None:
        for slot, (start, end) in cls.TIME_SLOTS.items():
            if start <= t <= end:
                return slot
        return None

    # 🔹 Boş ilk sütuna ⚠ değer yerleştirici
    def _place_unknown(self, row_id, val):
        for col in ("Sabah", "Öğle", "İkindi", "Akşam", "Gece"):
            if self.tv.item(row_id, "values")[self.IDX[col]] == "":
                self._cell_update(row_id, col, f"⚠ {val}")
                return
        # Hepsi doluysa en sola ekle
        old = self.tv.item(row_id, "values")[self.IDX["Sabah"]]
        self._cell_update(row_id, "Sabah", f"{old}, ⚠ {val}")

    # ---------- kurucu ----------

    def __init__(self, user: dict | None = None):
        super().__init__()
        self.user = user or {"id": 0, "tc_kimlik_no": "Demo"}

        # 🆕 profil bilgilerini çek
        self._profile = Repo.get_profile(self.user["id"])

        self.state("zoomed")
        self.configure(bg=BG)
        self.title("Hasta Paneli")

        self._build_top_section()
        self._init_table()
        self._populate_table()

    # ---------- ÜST KISIM + PROFİL ----------
    def _build_top_section(self):
        top = tk.Frame(self, bg=BG)
        top.place(relx=0.5, rely=0.05, anchor="n")

        # 🖼️ Fotoğraf (varsa)
        self._photo_tk = None
        if self._profile and self._profile["photo_blob"]:
            img = Image.open(io.BytesIO(
                self._profile["photo_blob"])).resize((80, 80))
            self._photo_tk = ImageTk.PhotoImage(img)
            tk.Label(top, image=self._photo_tk, bg=BG).pack()

        tk.Label(
            top,
            text=f"Hoş geldiniz, {self.user['tc_kimlik_no']}",
            font=("Segoe UI", 20, "bold"),
            bg=BG,
        ).pack(pady=4)

        # 🆕 profil metni
        if self._profile:
            info = (
                f"E-posta: {self._profile['email']}  |  "
                f"Doğum: {self._profile['birth_date']}  |  "
                f"Cinsiyet: {self._profile['gender']}"
            )
            tk.Label(top, text=info, bg=BG).pack(pady=2)

        # 🆕 Profil Düzenle butonu
        tk.Button(
            top, text="Profil Düzenle", command=self._edit_profile, bg="#F1C40F"
        ).pack(pady=(0, 8))

        # ------------- ölçüm giriş alanları -------------
        frm = tk.Frame(top, bg=BG)
        frm.pack(pady=8)

        tk.Label(frm, text="Şeker (mg/dL):", bg=BG).grid(row=0, column=0)
        self.e_val = tk.Entry(frm, width=8, justify="center")
        self.e_val.grid(row=0, column=1, padx=4)

        tk.Label(frm, text="Tarih (GG.AA.YYYY):", bg=BG).grid(
            row=0, column=2, padx=(12, 0))
        self.e_date = tk.Entry(frm, width=12, justify="center")
        self.e_date.grid(row=0, column=3)

        tk.Label(frm, text="Saat (HH:MM):", bg=BG).grid(
            row=0, column=4, padx=(12, 0))
        self.e_time = tk.Entry(frm, width=8, justify="center")
        self.e_time.grid(row=0, column=5)

        tk.Button(top, text="Kaydet", command=self.kaydet,
                  width=10).pack(pady=(4, 2))
        tk.Button(top, text="Özet", command=self.ozet, width=10).pack(pady=2)
        tk.Button(top, text="İnsülin Önerisi",
                  command=self.insulin, width=14).pack(pady=2)
        self.lbl_cnt = tk.Label(top, fg="blue", bg=BG)
        self.lbl_cnt.pack(pady=2)

        tk.Button(top, text="Egz./Diyet Yüzdesi",
                  command=self.egz_diyet, width=18).pack(pady=2)
        tk.Button(top, text="Şeker Grafiği",
                  command=self.grafik, width=18).pack(pady=2)
        tk.Button(top, text="İnsülin Geçmişi",
                  command=self.insulin_gecmis, width=18).pack(pady=2)

    # ---------- 🆕 PROFİL DÜZENLE ----------
    def _edit_profile(self):
        prof = Repo.get_profile(self.user["id"])

        win = tk.Toplevel(self)
        win.title("Profil Düzenle")
        win.configure(bg=BG)
        win.resizable(False, False)

        tk.Label(win, text="E-posta:", bg=BG).grid(row=0,
                                                   column=0, sticky="e", padx=6, pady=4)
        e_mail = tk.Entry(win, width=30)
        e_mail.grid(row=0, column=1, pady=4)
        e_mail.insert(0, prof["email"] if prof else "")

        tk.Label(win, text="Doğum (YYYY-MM-DD):", bg=BG).grid(row=1,
                                                              column=0, sticky="e", padx=6, pady=4)
        e_bd = tk.Entry(win, width=30)
        e_bd.grid(row=1, column=1, pady=4)
        e_bd.insert(0, (prof["birth_date"] or "") if prof else "")

        tk.Label(win, text="Cinsiyet (E/K):", bg=BG).grid(row=2,
                                                          column=0, sticky="e", padx=6, pady=4)
        e_gn = tk.Entry(win, width=30)
        e_gn.grid(row=2, column=1, pady=4)
        e_gn.insert(0, prof["gender"] if prof else "")

        tk.Label(win, text="Yeni Fotoğraf:", bg=BG).grid(
            row=3, column=0, sticky="e", padx=6, pady=4)
        lbl_file = tk.Label(win, text="(seçilmedi)", bg=BG)
        lbl_file.grid(row=3, column=1, sticky="w")

        photo_bytes = {"data": None}

        def choose():
            path = filedialog.askopenfilename(
                title="Fotoğraf seç",
                filetypes=[("Resim", "*.png;*.jpg;*.jpeg")],
            )
            if path:
                lbl_file.config(text=os.path.basename(path))
                with open(path, "rb") as f:
                    photo_bytes["data"] = f.read()

        tk.Button(win, text="Seç", command=choose).grid(
            row=3, column=1, sticky="e", padx=6)

        def kaydet():
            mail = e_mail.get().strip()
            bd_str = e_bd.get().strip()
            gn = e_gn.get().strip().upper()

            bd = None
            if bd_str:
                try:
                    bd = datetime.date.fromisoformat(bd_str)
                except ValueError:
                    messagebox.showerror(
                        "Hata", "Doğum tarihi YYYY-MM-DD olmalı")
                    return

            try:
                Repo.update_profile(
                    self.user["id"],
                    email=mail or None,
                    birth_date=bd,
                    gender=gn or None,
                    photo_bytes=photo_bytes["data"],
                )
            except Exception as ex:
                messagebox.showerror("Hata", str(ex))
                return

            messagebox.showinfo("Başarılı", "Profil güncellendi!")
            win.destroy()
            # pencereyi tazele
            self.destroy()
            HastaWin(self.user).mainloop()

        tk.Button(
            win, text="Kaydet", command=kaydet, bg="#2980B9", fg="white", width=20
        ).grid(row=4, column=0, columnspan=2, pady=12)

    # ---------- TABLO ----------
    def _init_table(self):
        style = ttk.Style()
        style.configure(
            "Grid.Treeview",
            highlightthickness=1,
            bd=1,
            relief="solid",
            font=("Segoe UI", 11),
            rowheight=28,
            bordercolor="#B0BEC5",
            fieldbackground="#FFFFFF",
        )
        style.layout("Grid.Treeview", [
                     ("Treeview.treearea", {"sticky": "nswe"})])

        tf = tk.Frame(self, bg=BG)
        tf.place(relx=0.5, rely=0.65, relwidth=0.9, relheight=0.45, anchor="n")

        self.tv = ttk.Treeview(
            tf,
            columns=self.COLS,
            show="headings",
            style="Grid.Treeview",
            selectmode="none",
        )
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscroll=vsb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        header = {
            "Tarih": "Tarih",
            "Sabah": "Sabah (07-08)",
            "Öğle": "Öğle (12-13)",
            "İkindi": "İkindi (15-16)",
            "Akşam": "Akşam (18-19)",
            "Gece": "Gece (22-23)",
            "İnsülin": "İnsülin (ml)",
        }
        for col in self.COLS:
            self.tv.heading(col, text=header[col])
            self.tv.column(col, anchor="center", width=180, minwidth=160)

    # ---------- Yardımcılar ----------
    def _row_by_date(self, dt_str: str):
        for iid in self.tv.get_children():
            if self.tv.item(iid, "values")[0] == dt_str:
                return iid
        return self.tv.insert("", "end", values=[dt_str] + [""] * 6)

    def _cell_update(self, row_id, col, val):
        vals = list(self.tv.item(row_id, "values"))
        vals[self.IDX[col]] = str(val)
        self.tv.item(row_id, values=vals)

    def _valid_slot_values(self):
        row = self._row_by_date(self.e_date.get())
        vals = self.tv.item(row, "values")
        return [int(v) for v in vals[1:6] if str(v).isdigit()]

    # ---------- TABLOYU DOLDUR ----------
    def _populate_table(self):
        rows = Repo.measurement_table(self.user["id"])
        print("DEBUG ölçüm satırları:", rows)  # ← Bunu ekle
        for row in rows:
            tarih_str = row["tarih"].strftime("%d.%m.%Y")
            saat = datetime.datetime.strptime(row["saat"], "%H:%M").time()
            slot = self._slot_from_time(saat)

            row_id = self._row_by_date(tarih_str)

            # Slot belirlenemiyorsa ⚠ işareti ile göster
            if not slot:
                self._place_unknown(row_id, row["deger"])
            else:
                self._cell_update(row_id, slot, row["deger"])

    # ---------- KAYDET ----------

    def kaydet(self):
        try:
            val = int(self.e_val.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz şeker değeri")
            return

        try:
            dt = datetime.datetime.strptime(
                self.e_date.get(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı")
            return

        try:
            tm = datetime.datetime.strptime(self.e_time.get(), "%H:%M").time()
        except ValueError:
            messagebox.showerror("Hata", "Saat HH:MM biçiminde olmalı")
            return

        slot = self._slot_from_time(tm)
        print("🧪 SLOT:", slot)

        # --- slot YOKSA: kaydet + tabloya ⚠ ekle + ortalamaya dahil etme ---
        if slot is None:
            messagebox.showwarning(
                "Uyarı",
                "Girilen saat belirtilen zaman dilimlerine uymuyor!\n"
                "Bu ölçüm kaydedildi ancak ortalamaya dahil edilmeyecek.",
            )
            print("💡 SLOT YOK — Bilinmeyen olarak kaydedilecek.")

            Repo.add_measurement(self.user["id"], val, "Bilinmeyen", dt, tm)

            tarih_str = dt.strftime("%d.%m.%Y")
            row_id = self._row_by_date(tarih_str)
            self._place_unknown(row_id, val)
            return

        # --- slot VARSA: normal işlem ---
        Repo.add_measurement(self.user["id"], val, slot, dt, tm)

        row = self._row_by_date(self.e_date.get())
        self._cell_update(row, slot, val)

        self.lbl_cnt.config(
            text=f"{self.e_date.get()} için {len(self._valid_slot_values())} ölçüm var."
        )


        if val < 70 or val > 200:
            kritik_tip = "Acil Uyarı"
            mesaj = f"{val} mg/dL → {'Hipoglisemi' if val < 70 else 'Hiperglisemi'}"
            Repo.add_alert_full(self.user["id"], kritik_tip, val, dt, tm, mesaj)



    # ---------- ÖZET ----------
    def ozet(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showwarning("Veri Yok", "Bu tarihte geçerli ölçüm yok")
            return

        avg = sum(vals) / len(vals)

        if len(vals) < 3:
            messagebox.showwarning(
                "Yetersiz Veri", "3'ten az ölçüm var, ortalama güvenilir değil."
            )
        else:
            row = self._row_by_date(self.e_date.get())
            self._cell_update(row, "İnsülin", insulin_dose(avg))

        messagebox.showinfo(
            "Ortalama", f"{self.e_date.get()} ortalama: {avg:.1f} mg/dL")

    # ---------- İNSÜLİN ÖNERİSİ ----------
    def insulin(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showerror("Veri Yok", "Bu tarihte geçerli ölçüm yok")
            return
        avg = sum(vals) / len(vals)
        doz = insulin_dose(avg) or "İnsülin gerekmiyor"
        messagebox.showinfo(
            "İnsülin", f"{self.e_date.get()} doz önerisi: {doz}")

    # ---------- Egzersiz & Diyet ----------
    def egz_diyet(self):
        ex = Repo.exercise_percent(self.user["id"])
        diet = Repo.diet_percent(self.user["id"])

        win = tk.Toplevel(self)
        win.title("Egzersiz / Diyet Yüzdeleri")
        txt = tk.Text(win, width=50, height=15)
        txt.pack(padx=10, pady=8)

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        dates = {r["exercise_date"]
                 for r in ex} | {r["diet_date"] for r in diet}
        for d in sorted(dates):
            e = next((r["oran"] for r in ex if r["exercise_date"] == d), "-")
            di = next((r["oran"] for r in diet if r["diet_date"] == d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    # ---------- Günlük şeker grafiği ----------
    def grafik(self):
        row = self._row_by_date(self.e_date.get())
        vals = [self.tv.item(row, "values")[self.IDX[s]]
                for s in self.TIME_SLOTS.keys()]
        x = list(self.TIME_SLOTS.keys())
        y = [int(v) if str(v).isdigit() else None for v in vals]

        if all(v is None for v in y):
            messagebox.showwarning("Veri Yok", "Bu tarihte ölçüm yok")
            return

        win = tk.Toplevel(self)
        win.title("Günlük Kan Şekeri Grafiği")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(x, y, marker="o")
        ax.set_ylabel("mg/dL")
        ax.set_title(f"{self.e_date.get()} Kan Şekeri")
        ax.grid(True)
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(
            fill="both", expand=True)

    # ---------- İnsülin geçmişi ----------
    def insulin_gecmis(self):
        d1 = simpledialog.askstring(
            "Tarih Başlangıcı", "Başlangıç (GG.AA.YYYY):")
        if not d1:
            return
        d2 = simpledialog.askstring("Tarih Bitişi", "Bitiş (GG.AA.YYYY):")
        if not d2:
            return
        try:
            start = datetime.datetime.strptime(d1, "%d.%m.%Y").date()
            end = datetime.datetime.strptime(d2, "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Biçim GG.AA.YYYY olmalı.")
            return
        if start > end:
            messagebox.showerror("Hata", "Başlangıç, bitişten önce olmalı.")
            return

        win = tk.Toplevel(self)
        win.title("İnsülin Geçmişi")
        cols = (
            "Tarih",
            "Sabah",
            "Öğle",
            "İkindi",
            "Akşam",
            "Gece",
            "Ortalama",
            "İnsülin (ml)",
        )
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True)

        for raw in Repo.get_measurement_dates(self.user["id"]):
            # ham değeri datetime.date'e çevir
            if isinstance(raw, datetime.date):
                d_date = raw if not isinstance(
                    raw, datetime.datetime) else raw.date()
            else:
                s = str(raw).split(" ")[0]
                try:
                    d_date = datetime.date.fromisoformat(s)
                except ValueError:
                    try:
                        d_date = datetime.datetime.strptime(
                            s, "%d.%m.%Y").date()
                    except ValueError:
                        continue

            if not (start <= d_date <= end):
                continue

            row_vals, slot_vals = [d_date.strftime("%d.%m.%Y")], []
            for slot in self.TIME_SLOTS.keys():
                v = Repo.get_measurement_value(self.user["id"], d_date, slot)
                row_vals.append(v if v is not None else "-")
                if v is not None:
                    slot_vals.append(v)

            if len(slot_vals) >= 3:
                avg = sum(slot_vals) / len(slot_vals)
                row_vals += [f"{avg:.1f}", insulin_dose(avg) or "-"]
            else:
                row_vals += ["-", "Yetersiz veri"]

            tree.insert("", "end", values=row_vals)
