

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
    COLS = ["Tarih", "Sabah", "Öğle", "İkindi", "Akşam", "Gece"]
    IDX = {c: i for i, c in enumerate(COLS)}

    # yardımcı 
    @classmethod
    def _slot_from_time(cls, t: datetime.time) -> str | None:
        for slot, (start, end) in cls.TIME_SLOTS.items():
            if start <= t <= end:
                return slot
        return None

   
    def _place_unknown(self, row_id, val):
        for col in ("Sabah", "Öğle", "İkindi", "Akşam", "Gece"):
            if self.tv.item(row_id, "values")[self.IDX[col]] == "":
                self._cell_update(row_id, col, f"⚠ {val}")
                return
        # Hepsi doluysa en sola ekle
        old = self.tv.item(row_id, "values")[self.IDX["Sabah"]]
        self._cell_update(row_id, "Sabah", f"{old}, ⚠ {val}")

    #kurucu

    def __init__(self, user: dict | None = None):
        super().__init__()
        self.user = user or {"id": 0, "tc_kimlik_no": "Demo"}

        # profil bilgileri
        self._profile = Repo.get_profile(self.user["id"])

        self.state("zoomed")
        self.configure(bg=BG)
        self.title("Hasta Paneli")

        self._build_top_section()
        self._init_table()
        self._populate_table()

   
    def _build_top_section(self):
        top = tk.Frame(self, bg=BG)
        top.place(relx=0.5, rely=0.05, anchor="n")
        self.lbl_cnt = tk.Label(self, text="", bg=BG)
        self.lbl_cnt.place(relx=0.5, rely=0.62, anchor="center")

        self._photo_tk = None
        if self._profile and self._profile["profile_image"]:
            img = Image.open(io.BytesIO(
                self._profile["profile_image"])).resize((80, 80))
            self._photo_tk = ImageTk.PhotoImage(img)
            tk.Label(top, image=self._photo_tk, bg=BG).pack()

        tk.Label(
            top,
            text=f"Hoş geldiniz, {self.user['first_name']} {self.user['last_name']}",
            font=("Segoe UI", 20, "bold"),
            bg=BG,
        ).pack(pady=4)

       
        if self._profile:
            info = (
                f"E-posta: {self._profile['email']}  |  "
                f"Doğum: {self._profile['birth_date']}  |  "
                f"Cinsiyet: {self._profile['gender']}"
            )
            tk.Label(top, text=info, bg=BG).pack(pady=2)

      
        tk.Button(
            top, text="Profil Düzenle", command=self._edit_profile, bg="#F1C40F"
        ).pack(pady=(0, 8))

      
        frm = tk.Frame(top, bg=BG)
        frm.pack(pady=8)

        tk.Label(frm, text="Şeker (mg/dL):", bg=BG).grid(row=0, column=0)
        self.e_val = tk.Entry(frm, width=8, justify="center")
        self.e_val.grid(row=0, column=1, padx=4)

        tk.Label(frm, text="Tarih (GG.AA.YYYY):", bg=BG).grid(
            row=0, column=2, padx=(12, 0))
        self.e_date = tk.Entry(frm, width=12, justify="center")
        self.e_date.grid(row=0, column=3)

        tk.Label(frm, text="Saat (HH:MM:SS):", bg=BG).grid(
            row=0, column=4, padx=(12, 0))
        self.e_time = tk.Entry(frm, width=8, justify="center")
        self.e_time.grid(row=0, column=5)

        tk.Button(top, text="Kaydet", command=self.kaydet,
                  width=10).pack(pady=(4, 2))
        tk.Button(top, text="İnsulin Önerisi",
                  command=self.slot_bazli_insulin, width=18).pack(pady=2)
        tk.Button(top, text="Egz./Diyet Yüzdesi",
                  command=self.egz_diyet, width=18).pack(pady=2)
        tk.Button(top, text="Önerilen Plan",
                  command=self._gunluk_bildir, width=18).pack(pady=2)
        tk.Button(top, text="Şeker Grafiği",
                  command=self.grafik, width=18).pack(pady=2)
        tk.Button(top, text="İnsülin Geçmişi",
                  command=self.insulin_gecmis, width=18).pack(pady=2)


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

        tk.Label(win, text="Doğum (DD-MM-YYYY):", bg=BG).grid(row=1,
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
                        "Hata", "Doğum tarihi DD-MM-YYYY olmalı")
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

           # if not self.e_time.get().strip():
              #  messagebox.showerror(
               #     "Hata", "Lütfen saat bilgisini giriniz (HH:MM)")
                #return

        tk.Button(
            win, text="Kaydet", command=kaydet, bg="#2980B9", fg="white", width=20
        ).grid(row=4, column=0, columnspan=2, pady=12)

    # TABLO 
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
        }
        for col in self.COLS:
            self.tv.heading(col, text=header[col])
            self.tv.column(col, anchor="center", width=180, minwidth=160)

    #Yardımcılar
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

    
    def _populate_table(self):
        rows = Repo.measurement_table(self.user["id"])
        print("DEBUG ölçüm satırları:", rows)  # ← Bunu ekle
        for row in rows:
            tarih_str = row["tarih"].strftime("%d.%m.%Y")
            saat_str = row["saat"]
            try:
                # HH:MM formatı mı?
                if len(saat_str) == 5:
                    saat = datetime.datetime.strptime(saat_str, "%H:%M").time()
                else:
                    saat = datetime.datetime.strptime(saat_str, "%H:%M:%S").time()
            except Exception as ex:
                print("❌ Saat parse hatası:", saat_str, ex)
                continue
            slot = self._slot_from_time(saat)

            row_id = self._row_by_date(tarih_str)

        
            if not slot:
                self._place_unknown(row_id, row["deger"])
            else:
                self._cell_update(row_id, slot, row["deger"])

    def kaydet(self):
        # --- TEMEL BOŞLUK / FORMAT KONTROLÜ ----------------------
        if not self.e_val.get().strip() or not self.e_date.get().strip() or not self.e_time.get().strip():
            messagebox.showwarning("Eksik Giriş", "Şeker, tarih ve saat alanları boş bırakılamaz.")
            return

        if not self.e_val.get().strip().isdigit():
            messagebox.showerror("Hata", "Kan şekeri değeri sadece sayılardan oluşmalıdır.")
            return
        # ---------------------------------------------------------

        try:
            val = int(self.e_val.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz şeker değeri")
            return

        try:
            dt = datetime.datetime.strptime(self.e_date.get(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı")
            return

        try:
            tm = datetime.datetime.strptime(self.e_time.get(), "%H:%M:%S").time()
        except ValueError:
            messagebox.showerror("Hata", "Saat HH:MM biçiminde olmalı")
            return

        slot = self._slot_from_time(tm)
        print("🧪 SLOT:", slot)

        tarih_str = dt.strftime("%d.%m.%Y")
        row_id = self._row_by_date(tarih_str)

        # Ölçüm kaydet (slot olsun olmasın)
        slot_or_default = slot if slot is not None else "Bilinmeyen"
        Repo.add_measurement(self.user["id"], val, slot, dt, tm)

        # KAYDET fonksiyonunda Repo.add_measurement(...) satırından hemen SONRA
        alert_t, msg = Repo._build_level_alert(val)
        if alert_t:
            Repo.add_alert_full(self.user["id"], alert_t, val, dt, tm, msg)

        
        if val < 70 or val > 200:
            mesaj = f"Kan şekeri {val} mg/dL! Acil müdahale gerekebilir."
            Repo.add_alert_full(
                self.user["id"], "Acil Uyarı", val, dt, tm, mesaj)

       
        if not slot:
            self._place_unknown(row_id, val)
            messagebox.showwarning(
                "Eksik Ölçüm",
                "Ölçüm eksik! Ortalama alınırken bu ölçüm hesaba katılmadı."
            )
        else:
            self._cell_update(row_id, slot, val)

        self.lbl_cnt.config(
            text=f"{self.e_date.get()} için {len(self._valid_slot_values())} ölçüm var."
        )




    def slot_bazli_insulin(self):
        """Her zaman dilimine kadar ortalamayı hesaplar ve doz önerir."""
        # 1) giriş tarihi
        try:
            dt = datetime.datetime.strptime(
                self.e_date.get(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        slotlar = ["Sabah", "Öğle", "İkindi", "Akşam", "Gece"]
        biriken = []
        rapor = ""

        for slot in slotlar:
            v = Repo.get_measurement_value(self.user["id"], dt, slot)
            if v is not None:
                biriken.append(v)
                ort = sum(biriken) / len(biriken)
                doz = insulin_dose(ort) or "-"
                rapor += f"{slot:<6} → {ort:>6.1f} mg/dL → {doz} insülin\n"
            else:
                rapor += f"{slot:<6} → (ölçüm yok)\n"

        if len(biriken) < 3:
            rapor += "\n⚠ Yetersiz veri! Ortalama güvenilir değildir."

        messagebox.showinfo("Slot Bazlı İnsülin Önerisi", rapor)

    def egz_diyet(self):
        ex = Repo.exercise_percent(self.user["id"])
        diet = Repo.diet_percent(self.user["id"])

        win = tk.Toplevel(self)
        win.title("Egzersiz / Diyet Yüzdeleri")
        txt = tk.Text(win, width=50, height=15)
        txt.pack(padx=10, pady=8)

        
        plan = Repo.get_assigned_plan(self.user["id"])
        if plan:
            txt.insert("end",
                       f"Diyet Planı   : {plan.get('diet_plan', '-')}\n"
                       f"Egzersiz Planı: {plan.get('exercise_plan', '-')}\n\n"
                       )
        
        symp = Repo._list("""
            SELECT sl.symptom_date, s.name
            FROM symptom_logs sl
            JOIN symptoms s ON s.id=sl.symptom_id
            WHERE patient_id=%s
        """, self.user["id"])
        if symp:
            txt.insert("end", "Belirtiler (son girişler):\n")
            for r in symp[-5:]:
                txt.insert("end", f"  {r['symptom_date']} : {r['name']}\n")
            txt.insert("end", "\n")
        # -----------------------------------------

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        dates = {r["exercise_date"]
                 for r in ex} | {r["diet_date"] for r in diet}
        for d in sorted(dates):
            e = next((r["oran"] for r in ex if r["exercise_date"] == d), "-")
            di = next((r["oran"] for r in diet if r["diet_date"] == d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    # Günlük şeker grafiği
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
        ax.plot(x, [v if v is not None else float('nan')
                for v in y], marker="o", linestyle="-", color="blue")

     
        for i, val in enumerate(y):
            if val is not None:
                ax.annotate(f"{val}", (x[i], val), textcoords="offset points", xytext=(
                    0, 6), ha='center')

    
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(x, ha="center")

        ax.set_ylabel("mg/dL")
        ax.set_title(f"{self.e_date.get()} Kan Şekeri")
        ax.grid(True)

    
        if any(v is None for v in y):
            ax.text(0.5, 0.05, "⚠ Bazı saatlerde ölçüm eksik", transform=ax.transAxes,
                    fontsize=9, color="red", ha="center")

        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(
            fill="both", expand=True)


    def insulin_gecmis(self):
        # 1) tarih aralığını küçük diyalog kutularından al
        d1 = simpledialog.askstring("Başlangıç", "Başlangıç (DD.MM.YYYY):", parent=self)
        if d1 is None:        # iptal
            return
        d2 = simpledialog.askstring("Bitiş", "Bitiş (DD.MM.YYYY):", parent=self)
        if d2 is None:
            return

        try:
            start = datetime.datetime.strptime(d1.strip(), "%d.%m.%Y").date()
            end   = datetime.datetime.strptime(d2.strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Biçim DD.MM.YYYY olmalı.")
            return
        if start > end:
            messagebox.showwarning("Uyarı", "Başlangıç, bitişten önce olmalı.")
            return

        # 2) sonuç penceresi
        win = tk.Toplevel(self)
        win.title("İnsülin Takip (Slot Bazlı)")
        txt = tk.Text(win, width=70, height=18)
        txt.pack(padx=8, pady=8)

        # 3) yardımcı – bir günün satırlarını bas
        def _dump_day(d_date: datetime.date):
            sugar_vals = []
            for slot in self.TIME_SLOTS.keys():
                v = Repo.get_measurement_value(self.user["id"], d_date, slot)
                if v is None:
                    continue
                sugar_vals.append(v)
                ort  = sum(sugar_vals) / len(sugar_vals)
                doz  = insulin_dose(ort) or "0 ünite"
                hour = {"Sabah":"07:05", "Öğle":"12:05", "İkindi":"15:05",
                        "Akşam":"18:05", "Gece":"22:05"}[slot]
                txt.insert("end", f"{d_date:%d.%m.%Y} {hour} | {doz}\n")

        # 4) tarih aralığındaki günleri sırayla yaz
        days = sorted([d for d in Repo.get_measurement_dates(self.user["id"])
                       if start <= d <= end])
        for i, g in enumerate(days):
            _dump_day(g)
            if i != len(days)-1:                 # son gün değilse ayırıcı çiz
                txt.insert("end", "-"*40 + "\n")

        if not days:
            txt.insert("end", "Kayıt bulunamadı.\n")

        txt.config(state="disabled")

    def _gunluk_bildir(self):
        win = tk.Toplevel(self)
        win.title("Uygulama Kaydı")
        win.configure(bg=BG)
        win.resizable(False, False)

        
        tk.Label(win, text="Tarih (GG.AA.YYYY):", bg=BG
                ).grid(row=0, column=0, sticky="e", padx=6, pady=4)
        e_dt = tk.Entry(win, width=12, justify="center")
        e_dt.grid(row=0, column=1, sticky="w")
        e_dt.insert(0, self.e_date.get())        # ana ekrandaki tarihi al

        # --- Egzersiz ---------------------------------------------------
        egzs = Repo._list("SELECT id, name FROM exercise_types")
        tk.Label(win, text="Egzersiz:", bg=BG
                ).grid(row=1, column=0, sticky="e", padx=6, pady=4)
        cb_ex = ttk.Combobox(win, values=[e["name"] for e in egzs],
                            state="readonly", width=25)
        cb_ex.grid(row=1, column=1)
        cb_ex.current(0)
        var_ex = tk.BooleanVar(value=True)
        ttk.Checkbutton(win, text="Yapıldı", variable=var_ex
                        ).grid(row=1, column=2)

        # Diyet
        diets = Repo._list("SELECT id, name FROM diet_types")
        tk.Label(win, text="Diyet:", bg=BG
                ).grid(row=2, column=0, sticky="e", padx=6, pady=4)
        cb_dt = ttk.Combobox(win, values=[d["name"] for d in diets],
                            state="readonly", width=25)
        cb_dt.grid(row=2, column=1)
        cb_dt.current(0)
        var_dt = tk.BooleanVar(value=True)
        ttk.Checkbutton(win, text="Uygulandı", variable=var_dt
                        ).grid(row=2, column=2)
        # Kaydet butonundan ÖNCE, combobox'ların altına EKLE:
        plan = Repo.get_assigned_plan(self.user["id"])
        if plan:
            tk.Label(win, text=f"📌 Doktorun Önerisi:\nDiyet: {plan['diet_plan']}  |  Egzersiz: {plan['exercise_plan']}", 
                    bg=BG, fg="darkblue", font=("Segoe UI", 9, "italic"), justify="left"
            ).grid(row=3, column=0, columnspan=3, pady=(6, 10))

        # Kaydet
        def kaydet():
            try:
                d_obj = datetime.datetime.strptime(e_dt.get().strip(), "%d.%m.%Y").date()
            except ValueError:
                messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
                return

            Repo.toggle_daily_exercise(self.user["id"],
                                    egzs[cb_ex.current()]["id"],
                                    var_ex.get(), d_obj)
            Repo.toggle_daily_diet(self.user["id"],
                                diets[cb_dt.current()]["id"],
                                var_dt.get(), d_obj)
            messagebox.showinfo("Başarılı",
                                f"{d_obj:%d.%m.%Y} için kayıt güncellendi.")
            win.destroy()

        ttk.Button(win, text="Kaydet", command=kaydet, width=18
                ).grid(row=5, column=0, columnspan=3, pady=10)
