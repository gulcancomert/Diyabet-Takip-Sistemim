# gui/app_windows.py
import os, tkinter as tk
from tkinter import messagebox


# panel sınıfları
from gui.doktor import DoktorWin        # Doktor paneli
from gui.hasta  import HastaWin         # Hasta  paneli
from repository import Repo        

_ROOT   = os.path.dirname(os.path.dirname(__file__))
_ASSETS = os.path.join(_ROOT, "assets")

BG = "#EAF2F8"
BTN_BG, BTN_HOVER, BTN_FG = "#2980B9", "#1F618D", "#FFFFFF"


class WelcomeWin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diyabet Takip Sistemi")
        self.state("zoomed")
        self.configure(bg=BG)
        self.update()

        self._navigation_bar(is_root=True)
        self._welcome_content()

    def _navigation_bar(self, is_root=False):
        nav = tk.Frame(self, bg=BG)
        nav.place(relx=0.01, rely=0.02)
        tk.Button(nav, text="‹", font=("Segoe UI", 20), width=2,
                  relief="flat", bg=BG,
                  state="disabled" if is_root else "normal"
                 ).grid(row=0, column=0)
        tk.Button(nav, text="›", font=("Segoe UI", 20), width=2,
                  relief="flat", bg=BG, state="disabled"
                 ).grid(row=0, column=1, padx=(4, 0))

    def _welcome_content(self):
        f = tk.Frame(self, bg=BG)
        f.place(relx=0.5, rely=0.35, anchor="center")

        tk.Label(f, text="HOŞ GELDİNİZ",
                 font=("Segoe UI", 36, "bold"),
                 bg=BG, fg="#154360").pack(pady=(0, 40))

        self._mk_button(f, "Doktor Girişi",
                        lambda: self._open_login("Doktor")).pack(pady=12)
        self._mk_button(f, "Hasta Girişi",
                        lambda: self._open_login("Hasta")).pack(pady=12)

    def _mk_button(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         font=("Segoe UI", 18, "bold"),
                         width=16, height=1,
                         bg=BTN_BG, fg=BTN_FG,
                         activebackground=BTN_HOVER,
                         relief="flat", bd=0, cursor="hand2")

    def _open_login(self, role):
        self.destroy()
        LoginWin(role).mainloop()


# ──────────────────────────────────────────
class LoginWin(tk.Tk):
    def __init__(self, role):
        super().__init__()
        self.role = role                    # ← EKLENDİ
        self.title(f"{role} Girişi")
        self.state("zoomed")
        self.configure(bg=BG)
        self.update()

        self._navigation_bar()
        self._login_form(role)

    def _navigation_bar(self):
        nav = tk.Frame(self, bg=BG)
        nav.place(relx=0.01, rely=0.02)
        tk.Button(nav, text="‹", font=("Segoe UI", 20), width=2,
                  relief="flat", bg=BG, command=self._go_back
                 ).grid(row=0, column=0)
        tk.Button(nav, text="›", font=("Segoe UI", 20), width=2,
                  relief="flat", bg=BG, state="disabled"
                 ).grid(row=0, column=1, padx=(4, 0))

    def _login_form(self, role):
        cont = tk.Frame(self, bg=BG)
        cont.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(cont, text=f"{role} Girişi",
                 font=("Segoe UI", 32, "bold"),
                 bg=BG, fg="#154360").pack(pady=(0, 25))

        form = tk.Frame(cont, bg=BG, width=360)
        form.pack(anchor="center")

        tk.Label(form, text="Kullanıcı Adı:", bg=BG
                 ).grid(row=0, column=0, sticky="e", padx=8, pady=6)
        tk.Label(form, text="Şifre:", bg=BG
                 ).grid(row=1, column=0, sticky="e", padx=8, pady=6)

        self.e_user = tk.Entry(form, width=32, justify="center")
        self.e_pass = tk.Entry(form, width=32, show="•", justify="center")
        self.e_user.grid(row=0, column=1, pady=6)
        self.e_pass.grid(row=1, column=1, pady=6)

        tk.Button(cont, text="Giriş Yap", command=self._login,
                  font=("Segoe UI", 16, "bold"),
                  width=12, height=1,
                  bg=BTN_BG, fg=BTN_FG,
                  activebackground=BTN_HOVER,
                  relief="flat", bd=0, cursor="hand2"
                 ).pack(pady=24)

    def _go_back(self):
        self.destroy()
        WelcomeWin().mainloop()

 
    def _login(self):
        tc = self.e_user.get().strip()
        pw = self.e_pass.get().strip()

        if not tc or not pw:
            messagebox.showwarning("Uyarı", "Boş alan bırakmayın.")
            return

        user = Repo.get_user(tc, pw)
        if user is None:
            messagebox.showerror("Hata", "T.C. kimlik no veya şifre hatalı.")
            return

        messagebox.showinfo("Başarılı", "Giriş başarılı!")
        self.destroy()

        if self.role.lower().startswith("doktor"):
            DoktorWin(user).mainloop()
        else:
            HastaWin(user).mainloop()
   
if __name__ == "__main__":
    WelcomeWin().mainloop()
