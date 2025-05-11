# gui/hasta.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
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
        "Sabah":  (datetime.time(7, 0), datetime.time(8, 0)),
        "Öğle":   (datetime.time(12, 0), datetime.time(13, 0)),
        "İkindi": (datetime.time(15, 0), datetime.time(16, 0)),
        "Akşam":  (datetime.time(18, 0), datetime.time(19, 0)),
        "Gece":   (datetime.time(22, 0), datetime.time(23, 59)),
    }
    COLS = ["Tarih", "Sabah", "Öğle", "İkindi",
            "Akşam", "Gece", "İnsülin"]
    IDX = {c: i for i, c in enumerate(COLS)}

    @classmethod
    def _slot_from_time(cls, t: datetime.time) -> str | None:
        for slot, (start, end) in cls.TIME_SLOTS.items():
            if start <= t <= end:
                return slot
        return None

        # ──────────────────────────────────────────────────────────────
    # 🔵 BUTON DİZAYNI ⇣  (yalnızca bu fonksiyon güncel)
    # ──────────────────────────────────────────────────────────────
    def _build_top_section(self) -> None:
        top = tk.Frame(self, bg=BG)
        # genel blok: pencerenin tam ortasına, üstten %4 boşluk bırakarak yerleştir
        top.place(relx=0.5, rely=0.04, anchor="n")

        # — Başlık —
        tk.Label(
            top,
            text=f"Hoş geldiniz, {self.user['tc_kimlik_no']}",
            font=("Segoe UI", 20, "bold"),
            bg=BG,
        ).pack()

        # — Giriş alanları —
        frm = tk.Frame(top, bg=BG)
        frm.pack(pady=6)

        tk.Label(frm, text="Şeker (mg/dL):", bg=BG).grid(row=0, column=0, padx=2)
        self.e_val = tk.Entry(frm, width=8, justify="center")
        self.e_val.grid(row=0, column=1, padx=4)

        tk.Label(frm, text="Tarih (GG.AA.YYYY):", bg=BG).grid(
            row=0, column=2, padx=(12, 2)
        )
        self.e_date = tk.Entry(frm, width=12, justify="center")
        self.e_date.grid(row=0, column=3, padx=4)

        tk.Label(frm, text="Saat (HH:MM):", bg=BG).grid(row=0, column=4, padx=(12, 2))
        self.e_time = tk.Entry(frm, width=8, justify="center")
        self.e_time.grid(row=0, column=5, padx=4)

        # — Dikey (üst) buton grubu —
        col_btns = tk.Frame(top, bg=BG)
        col_btns.pack(pady=(2, 6))              # dikey aralık ⇡

        for txt, cmd, w in [
            ("Kaydet",          self.kaydet,           12),
            ("Özet",            self.ozet,             12),
            ("İnsülin Önerisi", self.insulin,          14),
        ]:
            tk.Button(col_btns, text=txt, command=cmd, width=w).pack(pady=2)

        self.lbl_cnt = tk.Label(col_btns, fg="blue", bg=BG)
        self.lbl_cnt.pack(pady=(2, 4))

        # — Yatay (alt) buton grubu —
        row_btns = tk.Frame(top, bg=BG)
        row_btns.pack()                          # hemen altına

        btn_info = [
            ("Egz./Diyet Yüzdesi", self.egz_diyet),
            ("Şeker Grafiği",      self.grafik),
            ("İnsülin Geçmişi",    self.insulin_gecmis),
        ]
        for i, (txt, cmd) in enumerate(btn_info):
            tk.Button(
                row_btns, text=txt, command=cmd,
                width=18
            ).grid(row=0, column=i, padx=6, pady=0)


    # ---------- tablo ----------
    def _init_table(self):
        s = ttk.Style()
        s.configure("Grid.Treeview", highlightthickness=1, bd=1, relief="solid",
                    font=("Segoe UI", 11), rowheight=28,
                    bordercolor="#B0BEC5", fieldbackground="#FFFFFF")
        s.layout("Grid.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        tf = tk.Frame(self, bg=BG)
        tf.place(relx=0.5, rely=0.45, relwidth=0.9, relheight=0.5, anchor="n")

        self.tv = ttk.Treeview(tf, columns=self.COLS, show="headings",
                               style="Grid.Treeview", selectmode="none")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscroll=vsb.set)
        self.tv.pack(side="left", fill="both", expand=True); vsb.pack(side="right", fill="y")

        header = {
            "Tarih":  "Tarih",
            "Sabah":  "Sabah(07:00–08:00)",
            "Öğle":   "Öğle(12:00–13:00)",
            "İkindi": "İkindi(15:00–16:00)",
            "Akşam":  "Akşam(18:00–19:00)",
            "Gece":   "Gece(22:00–23:00)",
            "İnsülin": "İnsülin(ml)"
        }
        for col in self.COLS:
            self.tv.heading(col, text=header[col])
            self.tv.column(col, anchor="center", width=200, minwidth=180)

        self._today_row()           # <<< döngü DIŞINDA, yalnızca 1 kez

    # ---------- satır/hücre ----------
    def _row_by_date(self, dt_str: str):
     """Girilen tarihe göre tablo satırı bulur/yoksa ekler"""
     for iid in self.tv.get_children():
        if self.tv.item(iid, "values")[0] == dt_str:
            return iid
     return self.tv.insert("", "end", values=[dt_str, "", "", "", "", "", ""])


    def _cell_update(self, row_id, col, val):
        vals = list(self.tv.item(row_id, "values"))
        vals[self.IDX[col]] = str(val)          # ← str() eklendi
        self.tv.item(row_id, values=vals)

    def _valid_slot_values(self):
     date_str = self.e_date.get()
     row = self._row_by_date(date_str)
     vals = self.tv.item(row, "values")
     return [int(v) for v in vals[1:6] if str(v).isdigit()]


    # ---------- kaydet ----------
    def kaydet(self):
        try: val = int(self.e_val.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz şeker değeri"); return
        try:
            now = datetime.datetime.strptime(self.e_time.get(), "%H:%M").time()
        except ValueError:
            messagebox.showerror("Hata", "Saat HH:MM formatında olmalı"); return

        try:
          date_obj = datetime.datetime.strptime(self.e_date.get(), "%d.%m.%Y").date()
        except ValueError:
         messagebox.showerror("Hata", "Tarih GG.AA.YYYY formatında olmalı"); return
         
        slot = self._slot_from_time(now)
        if slot is None:
            messagebox.showwarning("Zaman Dilimi Yok",
                                   "Girilen saat hiçbir zaman dilimine uymuyor!"); return

       # 🟡 Repo tarafında tarih de gönderilecek
        Repo.add_measurement(self.user['id'], val, slot, now, date_obj)
    
        row = self._row_by_date(self.e_date.get())
        self._cell_update(row, slot, val)

        vals = self._valid_slot_values()
        self.lbl_cnt.config(text=f"{self.e_date.get()} için {len(vals)} ölçüm var.")

        if val < 70 or val > 200:
            Repo.add_alert(self.user['id'],
                           "Hipoglisemi" if val < 70 else "Hiperglisemi", val)

        if vals:
            avg = sum(vals)/len(vals)
            self._cell_update(row, "İnsülin", insulin_dose(avg))
            messagebox.showinfo("Kaydedildi", f"Ölçüm ({slot}) kaydedildi")

    # ---------- özet / insülin ----------
    def ozet(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showwarning("Ölçüm Eksik", "Bugün geçerli ölçüm yok!"); return
        avg = sum(vals)/len(vals)
        msg = ("Yetersiz veri! Ortalama güvenilir değildir."
               if len(vals) < 3 else f"Bugünkü ortalama: {avg:.1f} mg/dL")
        messagebox.showinfo("Bugünkü Ortalama", msg)

    def insulin(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showerror("Hata", "Bugün geçerli ölçüm yok."); return
        avg = sum(vals)/len(vals)
        doz = insulin_dose(avg) or "İnsülin gerekmiyor"
        messagebox.showinfo("İnsülin Önerisi", f"Önerilen doz: {doz}")



# 🟢 1. Egzersiz & Diyet yüzdesi ---------------------------------
    def egz_diyet(self):
        ex  = Repo.exercise_percent(self.user['id'])
        diet = Repo.diet_percent(self.user['id'])

        win = tk.Toplevel(self); win.title("Egzersiz / Diyet Yüzdeleri")
        txt = tk.Text(win, width=50, height=15); txt.pack(padx=10, pady=8)

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        # Tarih bazlı iki listeyi birleştir
        dates = {row['exercise_date'] for row in ex} | {row['diet_date'] for row in diet}
        for d in sorted(dates):
            e = next((r['oran'] for r in ex if r['exercise_date']==d), "-")
            di = next((r['oran'] for r in diet if r['diet_date']==d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    # 🟢 2. Günlük şeker grafiği -------------------------------------
    def grafik(self):
        # slot sırasıyla değerler
        row = self._today_row()
        vals = [self.tv.item(row,"values")[self.IDX[s]] for s in
                ["Sabah","Öğle","İkindi","Akşam","Gece"]]
        x = ["Sabah","Öğle","İkindi","Akşam","Gece"]
        y = [int(v) if str(v).isdigit() else None for v in vals]

        if all(v is None for v in y):
            messagebox.showwarning("Veri Yok","Bugün ölçüm yok veya eksik."); return

        win = tk.Toplevel(self); win.title("Günlük Kan Şekeri Grafiği")

        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(x, y, marker="o")
        ax.set_ylabel("mg/dL"); ax.set_title("Bugünkü Kan Şekeri"); ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    # 🟢 3. İnsülin geçmişi ------------------------------------------
    def insulin_gecmis(self):
        date_ = tk.simpledialog.askstring("Tarih", "YYYY-MM-DD biçiminde tarih girin:")
        if not date_: return
        row = Repo.insulin_advice_on(self.user['id'], date_)
        doz = row['insulin_dozu'] if row else "Veri yok"
        messagebox.showinfo("İnsülin Geçmişi",
                            f"{date_} için önerilen doz: {doz}")# gui/hasta.py   ✅ DÜZELTİLMİŞ
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from repository import Repo

BG = "#EAF2F8"

def insulin_dose(avg: float) -> str:
    if   avg <  70: return ""
    elif avg <= 110: return ""
    elif avg <= 150: return "1 ml"
    elif avg <= 200: return "2 ml"
    else:            return "3 ml"

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
    IDX  = {c: i for i, c in enumerate(COLS)}

    @classmethod
    def _slot_from_time(cls, t: datetime.time) -> str|None:
        for slot, (start, end) in cls.TIME_SLOTS.items():
            if start <= t <= end:
                return slot
        return None

    def __init__(self, user: dict):
        super().__init__()
        self.state("zoomed"); self.configure(bg=BG)
        self.user = user; self.title("Hasta Paneli")
        self._build_top_section(); self._init_table()

    # ---------- ÜST KISIM ----------
    def _build_top_section(self):
        top = tk.Frame(self, bg=BG); top.place(relx=0.5, rely=0.05, anchor="n")

        tk.Label(top, text=f"Hoş geldiniz, {self.user['tc_kimlik_no']}",
                 font=("Segoe UI", 20, "bold"), bg=BG).pack()

        frm = tk.Frame(top, bg=BG); frm.pack(pady=8)

        # Şeker
        tk.Label(frm, text="Şeker (mg/dL):", bg=BG).grid(row=0, column=0)
        self.e_val = tk.Entry(frm, width=8, justify="center")
        self.e_val.grid(row=0, column=1, padx=4)

        # Tarih
        tk.Label(frm, text="Tarih (GG.AA.YYYY):", bg=BG)\
            .grid(row=0, column=2, padx=(12,0))
        self.e_date = tk.Entry(frm, width=12, justify="center")
        self.e_date.grid(row=0, column=3)

        # Saat
        tk.Label(frm, text="Saat (HH:MM):", bg=BG).grid(row=0, column=4, padx=(12,0))
        self.e_time = tk.Entry(frm, width=8, justify="center")
        self.e_time.grid(row=0, column=5)

        # Butonlar
        tk.Button(top, text="Kaydet", command=self.kaydet, width=10).pack(pady=(4,2))
        tk.Button(top, text="Özet", command=self.ozet, width=10).pack(pady=2)
        tk.Button(top, text="İnsülin Önerisi", command=self.insulin, width=14).pack(pady=2)
        self.lbl_cnt = tk.Label(top, fg="blue", bg=BG); self.lbl_cnt.pack(pady=2)

        # Ek butonlar
        tk.Button(top, text="Egz./Diyet Yüzdesi", command=self.egz_diyet,
                  width=18).pack(pady=2)
        tk.Button(top, text="Şeker Grafiği", command=self.grafik,
                  width=18).pack(pady=2)
        tk.Button(top, text="İnsülin Geçmişi", command=self.insulin_gecmis,
                  width=18).pack(pady=2)
        
        tk.Button(top, text="İnsülin Geçmişi", 
                  command=self.insulin_gecmis, width=18).pack(pady=2)



    # ---------- TABLO ----------
    def _init_table(self):
        style = ttk.Style()
        style.configure("Grid.Treeview", highlightthickness=1, bd=1, relief="solid",
                        font=("Segoe UI", 11), rowheight=28,
                        bordercolor="#B0BEC5", fieldbackground="#FFFFFF")
        style.layout("Grid.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        tf = tk.Frame(self, bg=BG)
        tf.place(relx=0.5, rely=0.45, relwidth=0.9, relheight=0.5, anchor="n")


        self.tv = ttk.Treeview(tf, columns=self.COLS, show="headings",
                               style="Grid.Treeview", selectmode="none")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscroll=vsb.set)
        self.tv.pack(side="left", fill="both", expand=True); vsb.pack(side="right", fill="y")

        header = {
            "Tarih": "Tarih", "Sabah":"Sabah(07-08)", "Öğle":"Öğle(12-13)",
            "İkindi":"İkindi(15-16)", "Akşam":"Akşam(18-19)", "Gece":"Gece(22-23)",
            "İnsülin":"İnsülin(ml)"
        }
        for col in self.COLS:
            self.tv.heading(col, text=header[col])
            self.tv.column(col, anchor="center", width=180, minwidth=160)

    # ---------- Yardımcılar ----------
    def _row_by_date(self, dt_str: str):
        """Girilen tarihe göre tablo satırı bulur, yoksa ekler"""
        for iid in self.tv.get_children():
            if self.tv.item(iid, "values")[0] == dt_str:
                return iid
        return self.tv.insert("", "end", values=[dt_str, "", "", "", "", "", ""])

    def _cell_update(self, row_id, col, val):
        vals = list(self.tv.item(row_id, "values"))
        vals[self.IDX[col]] = str(val)
        self.tv.item(row_id, values=vals)

    def _valid_slot_values(self):
        row = self._row_by_date(self.e_date.get())
        vals = self.tv.item(row, "values")
        return [int(v) for v in vals[1:6] if str(v).isdigit()]

    # ---------- KAYDET ----------
    def kaydet(self):
        # Değer
        try:
            val = int(self.e_val.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz şeker değeri"); return

        # Tarih
        try:
            dt = datetime.datetime.strptime(self.e_date.get(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı"); return

        # Saat
        try:
            tm = datetime.datetime.strptime(self.e_time.get(), "%H:%M").time()
        except ValueError:
            messagebox.showerror("Hata", "Saat HH:MM biçiminde olmalı"); return

        # Slot
        slot = self._slot_from_time(tm)
        if slot is None:
            messagebox.showwarning("Zaman Dilimi Yok",
                                   "Girilen saat bir zaman dilimine uymuyor!"); return

        # DB kaydı
        Repo.add_measurement(self.user['id'], val, slot, dt, tm)

        # Tablo güncelle
        row = self._row_by_date(self.e_date.get())
        self._cell_update(row, slot, val)
        self.lbl_cnt.config(text=f"{self.e_date.get()} için {len(self._valid_slot_values())} ölçüm var.")

        # Alert
        if val < 70 or val > 200:
            Repo.add_alert(self.user['id'],
                           "Hipoglisemi" if val < 70 else "Hiperglisemi", val)

        # Ortalama & insülin hücresi
        vals = self._valid_slot_values()
        if vals:
            avg = sum(vals)/len(vals)
            self._cell_update(row, "İnsülin", insulin_dose(avg))
        messagebox.showinfo("Kaydedildi", f"{slot} ölçümü kaydedildi")

    # ---------- ÖZET / İNSÜLİN ----------
    def ozet(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showwarning("Veri Yok", "Bu tarihte geçerli ölçüm yok"); return
        avg = sum(vals)/len(vals)
        if len(vals) < 3:
            messagebox.showwarning("Yetersiz Veri",
                                   "3'ten az ölçüm var, ortalama güvenilir değil.")
        messagebox.showinfo("Ortalama", f"{self.e_date.get()} ortalama: {avg:.1f} mg/dL")

    def insulin(self):
        vals = self._valid_slot_values()
        if not vals:
            messagebox.showerror("Veri Yok", "Bu tarihte geçerli ölçüm yok"); return
        avg = sum(vals)/len(vals)
        doz = insulin_dose(avg) or "İnsülin gerekmiyor"
        messagebox.showinfo("İnsülin", f"{self.e_date.get()} doz önerisi: {doz}")

    # ---------- Egzersiz & Diyet ----------
    def egz_diyet(self):
        ex   = Repo.exercise_percent(self.user['id'])
        diet = Repo.diet_percent(self.user['id'])

        win = tk.Toplevel(self); win.title("Egzersiz / Diyet Yüzdeleri")
        txt = tk.Text(win, width=50, height=15); txt.pack(padx=10, pady=8)

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        dates = {r['exercise_date'] for r in ex} | {r['diet_date'] for r in diet}
        for d in sorted(dates):
            e  = next((r['oran'] for r in ex   if r['exercise_date']==d), "-")
            di = next((r['oran'] for r in diet if r['diet_date']==d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    # ---------- Günlük şeker grafiği ----------
    def grafik(self):
        row = self._row_by_date(self.e_date.get())
        vals = [self.tv.item(row, "values")[self.IDX[s]] for s in
                ["Sabah","Öğle","İkindi","Akşam","Gece"]]
        x = ["Sabah","Öğle","İkindi","Akşam","Gece"]
        y = [int(v) if str(v).isdigit() else None for v in vals]

        if all(v is None for v in y):
            messagebox.showwarning("Veri Yok","Bu tarihte ölçüm yok"); return

        win = tk.Toplevel(self); win.title("Günlük Kan Şekeri Grafiği")
        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(x, y, marker="o")
        ax.set_ylabel("mg/dL"); ax.set_title(f"{self.e_date.get()} Kan Şekeri"); ax.grid(True)
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(fill="both", expand=True)

    # ---------- İnsülin geçmişi ----------
    def insulin_gecmis(self):
        date_ = simpledialog.askstring("Tarih", "YYYY-MM-DD biçiminde tarih girin:")
        if not date_:
            return
        row = Repo.insulin_advice_on(self.user['id'], date_)
        doz = row['insulin_dozu'] if row else "Veri yok"
        messagebox.showinfo("İnsülin Geçmişi", f"{date_} için önerilen doz: {doz}")


    def insulin_gecmis(self):
        date_ = tk.simpledialog.askstring("Tarih", "GG.AA.YYYY biçiminde tarih girin:")
        if not date_: return
        try:
            date_obj = datetime.datetime.strptime(date_, "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        row = Repo.insulin_advice_on(self.user['id'], date_obj.strftime("%Y-%m-%d"))
        doz = row['insulin_dozu'] if row else "Veri yok"
        messagebox.showinfo("İnsülin Geçmişi", f"{date_} için önerilen doz: {doz}")
