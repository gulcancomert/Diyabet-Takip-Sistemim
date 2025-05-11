import tkinter as tk
from repository import Repo

BG = "#EAF2F8"          # aynı tema rengi

class DoktorWin(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.state("zoomed")            # ← TAM EKRAN
        self.configure(bg=BG)
        self.title("Doktor Paneli")
        self.user = user

        # ── içeriği ortalamak için tek çerçeve ──
        cont = tk.Frame(self, bg=BG)
        cont.place(relx=0.5, rely=0.05, anchor="n")

        tk.Label(cont, text="Hastalarınız", font=("Segoe UI", 20, "bold"),
                 bg=BG).grid(row=0, column=0, padx=6, pady=4)

        self.lst = tk.Listbox(cont, height=20, width=30)
        self.lst.grid(row=1, column=0, rowspan=3, padx=6, pady=4)

        for p in Repo.list_patients(user['id']):
            self.lst.insert(tk.END, f"{p['id']} - {p['tc_kimlik_no']}")

        tk.Button(cont, text="Uyarıları Göster", command=self.uyari,
                  width=20).grid(row=1, column=1, sticky="we", pady=6)
        tk.Button(cont, text="Günlük Ortalama", command=self.ort,
                  width=20).grid(row=2, column=1, sticky="we", pady=6)

    # ---------- yardımcı ----------
    def _selected_pid(self):
        sel = self.lst.curselection()
        return int(self.lst.get(sel[0]).split()[0]) if sel else None

    # ---------- komutlar ----------
    def uyari(self):
        pid = self._selected_pid()
        if pid is None: return
        alerts = Repo.alerts_of_patient(pid)
        win = tk.Toplevel(self); win.title("Uyarılar")
        if not alerts:
            tk.Label(win, text="Güncel uyarı yok").pack(padx=20, pady=10)
            return
        for a in alerts:
            tk.Label(win,
                     text=f"{a['tarih']} {a['saat']} → {a['alert_type']} "
                          f"({a['sugar_level']} mg/dL)").pack(anchor="w")

    def ort(self):
        pid = self._selected_pid()
        if pid is None: return
        row = Repo.daily_summary(pid)
        msg = (f"Bugünkü ortalama: {row['ortalama_kan_sekeri']} mg/dL"
               if row else "Bugün ölçüm yok")
        tk.messagebox.showinfo("Günlük Ortalama", msg)
