import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from repository import Repo

BG = "#EAF2F8"

class DoktorWin(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.state("zoomed")
        self.configure(bg=BG)
        self.title("Doktor Paneli")
        self.user = user

        cont = tk.Frame(self, bg=BG)
        cont.place(relx=0.5, rely=0.05, anchor="n")

        tk.Label(cont, text="Hastalarınız", font=("Segoe UI", 20, "bold"), bg=BG).grid(row=0, column=0, padx=6, pady=4)

        self.lst = tk.Listbox(cont, height=20, width=30)
        self.lst.grid(row=1, column=0, rowspan=6, padx=6, pady=4)

        for p in Repo.list_patients(user['id']):
            self.lst.insert(tk.END, f"{p['id']} - {p['tc_kimlik_no']}")

        # Mevcut butonlar (bozulmadan korundu)
        tk.Button(cont, text="Uyarıları Göster", command=self.uyari, width=25).grid(row=1, column=1, pady=4)
        tk.Button(cont, text="Günlük Ortalama", command=self.ort, width=25).grid(row=2, column=1, pady=4)

        # Yeni özellikler
        tk.Button(cont, text="Egzersiz/Diyet Geçmişi", command=self.egz_diyet, width=25).grid(row=3, column=1, pady=4)
        tk.Button(cont, text="Kan Şekeri Tablosu", command=self.tablo, width=25).grid(row=4, column=1, pady=4)
        tk.Button(cont, text="Grafiksel Değişim", command=self.grafik, width=25).grid(row=5, column=1, pady=4)
        tk.Button(cont, text="Arşiv Verileri", command=self.arsiv, width=25).grid(row=6, column=1, pady=4)
        
        tk.Button(cont, text="Gün İçi Değişim", command=self.gun_ici, width=25).grid(row=7, column=1, pady=4)


    def _selected_pid(self):
        sel = self.lst.curselection()
        return int(self.lst.get(sel[0]).split()[0]) if sel else None

    def uyari(self):
        pid = self._selected_pid()
        if pid is None: return
        alerts = Repo.alerts_of_patient(pid)
        win = tk.Toplevel(self); win.title("Uyarılar")
        if not alerts:
            tk.Label(win, text="Güncel uyarı yok").pack(padx=20, pady=10)
            return
        for a in alerts:
            tk.Label(win, text=f"{a['tarih']} {a['saat']} → {a['alert_type']} ({a['sugar_level']} mg/dL)").pack(anchor="w")

    def ort(self):
        pid = self._selected_pid()
        if pid is None: return
        row = Repo.daily_summary(pid)
        msg = f"Bugünkü ortalama: {row['ortalama_kan_sekeri']} mg/dL" if row else "Bugün ölçüm yok"
        messagebox.showinfo("Günlük Ortalama", msg)

    def egz_diyet(self):
        pid = self._selected_pid()
        if pid is None: return
        ex = Repo.exercise_percent(pid)
        diet = Repo.diet_percent(pid)

        win = tk.Toplevel(self); win.title("Egzersiz / Diyet Geçmişi")
        txt = tk.Text(win, width=60, height=20); txt.pack(padx=10, pady=8)

        txt.insert("end", "Tarih      Egzersiz %   Diyet %\n")
        txt.insert("end", "--------------------------------\n")
        dates = {r['exercise_date'] for r in ex} | {r['diet_date'] for r in diet}
        for d in sorted(dates):
            e  = next((r['oran'] for r in ex   if r['exercise_date']==d), "-")
            di = next((r['oran'] for r in diet if r['diet_date']==d), "-")
            txt.insert("end", f"{d}   {e}        {di}\n")
        txt.config(state="disabled")

    def tablo(self):
        pid = self._selected_pid()
        if pid is None: return
        rows = Repo.measurement_table(pid)
        win = tk.Toplevel(self); win.title("Kan Şekeri Tablosu")

        tree = ttk.Treeview(win, columns=("tarih", "saat", "deger"), show="headings")
        tree.heading("tarih", text="Tarih")
        tree.heading("saat", text="Saat")
        tree.heading("deger", text="Kan Şekeri (mg/dL)")
        tree.pack(fill="both", expand=True, padx=10, pady=8)

        for row in rows:
            tree.insert("", "end", values=(row['tarih'], row['saat'], row['deger']))

    def grafik(self):
        pid = self._selected_pid()
        if pid is None: return
        rows = Repo.daily_graph_data(pid)
        if not rows:
            messagebox.showwarning("Veri Yok", "Günlük grafik oluşturulacak veri yok"); return

        tarih = [r['tarih'] for r in rows]
        ort = [r['ortalama'] for r in rows]

        win = tk.Toplevel(self); win.title("Zaman Bazlı Kan Şekeri Değişimi")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(tarih, ort, marker="o")
        ax.set_title("Günlük Kan Şekeri Ortalamaları")
        ax.set_ylabel("mg/dL")
        ax.set_xlabel("Tarih")
        ax.grid(True)

        #🔽 X etiketlerini eğik yaz (daha okunur hale getirir)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()

        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(fill="both", expand=True)

    def arsiv(self):
        pid = self._selected_pid()
        if pid is None: return
        rows = Repo.patient_archive(pid)
        win = tk.Toplevel(self); win.title("Arşiv Verileri")
        txt = tk.Text(win, width=80, height=25)
        txt.pack(padx=10, pady=10)
        for row in rows:
            txt.insert("end", f"{row['tarih']} {row['veri_tipi']}: {row['icerik']}\n")
        txt.config(state="disabled")
        
        
        def gun_ici(self):
         import datetime
        pid = self._selected_pid()
        if pid is None: return

        tarih_str = tk.simpledialog.askstring("Tarih", "GG.AA.YYYY biçiminde tarih girin:")
        if not tarih_str: return
        try:
            tarih_obj = datetime.datetime.strptime(tarih_str, "%d.%m.%Y").date()
        except ValueError:
            tk.messagebox.showerror("Hata", "Tarih GG.AA.YYYY biçiminde olmalı.")
            return

        rows = Repo.slot_measurements_on(pid, tarih_obj)
        if not rows:
            tk.messagebox.showwarning("Veri Yok", "Bu tarihe ait veri yok.")
            return

        slotlar = ["Sabah", "Öğle", "İkindi", "Akşam", "Gece"]
        veriler = {row['time_slot']: row['sugar_level'] for row in rows}
        x = slotlar
        y = [veriler.get(slot, None) for slot in slotlar]

        if all(v is None for v in y):
            tk.messagebox.showinfo("Veri Yok", "Bu tarihte hiçbir ölçüm yapılmamış.")
            return

        win = tk.Toplevel(self); win.title(f"{tarih_str} Kan Şekeri Gün İçi Değişimi")
        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(x, y, marker="o")
        ax.set_ylabel("mg/dL")
        ax.set_title(f"{tarih_str} Gün İçi Değişim")
        ax.grid(True)
        FigureCanvasTkAgg(fig, master=win).get_tk_widget().pack(fill="both", expand=True)

