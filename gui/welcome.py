"""
gui/app_windows.py
Tüm başlangıç akışını içeren tek dosya.
- WelcomeWin  : Hoş geldiniz + ‘Giriş’ butonu
- RoleWin     : Doktor / Hasta seçim ekranı
- LoginWin    : Kullanıcı adı / şifre giriş ekranı (yalın örnek)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# ---------- Genel ayarlar ----------
_ROOT_DIR   = os.path.dirname(os.path.dirname(__file__))    # DiyabetTakip/
_ASSETS_DIR = os.path.join(_ROOT_DIR, "assets")

BG_MAIN   = "#EAF2F8"   # açık mavi zemin
BTN_BG    = "#2980B9"   # koyu mavi buton
BTN_FG    = "#FFFFFF"

# ttk düğme stilleri (tek sefer tanımla)
_style = ttk.Style()
_style.configure("Main.TButton", font=("Segoe UI", 14, "bold"),
                 background=BTN_BG, foreground=BTN_FG)
_style.map("Main.TButton",
           background=[("active", "#1F618D")],
           foreground=[("disabled", "#CCCCCC")])


# ---------- 1️⃣  Hoş geldiniz penceresi ----------
class WelcomeWin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diyabet Takip Sistemi")
        self.state("zoomed")              # tam ekran
        self.configure(bg=BG_MAIN)

        # Arka plan görseli
        bg_path = os.path.join(_ASSETS_DIR, "welcome_screen.png")
        self._set_full_background(bg_path)

        # “GİRİŞ” butonu
        ttk.Button(self, text="GİRİŞ", style="Main.TButton",
                   command=self._open_role_win
                   ).place(relx=0.5, rely=0.85, anchor="center")

    # Ekranı kapat, RoleWin göster
    def _open_role_win(self):
        self.destroy()
        RoleWin().mainloop()

    # Tam ekran arka plan fonksiyonu
    def _set_full_background(self, img_path):
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        img  = Image.open(img_path).resize((w, h))
        self._bg_photo = ImageTk.PhotoImage(img)
        tk.Label(self, image=self._bg_photo).place(x=0, y=0, relwidth=1, relheight=1)


# ---------- 2️⃣  Rol seçimi penceresi ----------
class RoleWin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Giriş Yapın")
        self.geometry("420x680")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)

        # Arka plan görseli (üst kısım)
        bg_path = os.path.join(_ASSETS_DIR, "login_screen.png")
        self._header(bg_path)

        # Doktor / Hasta butonları
        ttk.Button(self, text="Doktor Girişi", style="Main.TButton",
                   command=lambda: self._open_login("Doktor")
                   ).pack(pady=(20, 10))
        ttk.Button(self, text="Hasta Girişi",  style="Main.TButton",
                   command=lambda: self._open_login("Hasta")
                   ).pack()

    def _header(self, img_path):
        img = Image.open(img_path).resize((380, 260))
        self._img_photo = ImageTk.PhotoImage(img)
        tk.Label(self, image=self._img_photo, bg=BG_MAIN).pack(pady=(15, 5))

    def _open_login(self, role):
        self.destroy()
        LoginWin(role).mainloop()


# ---------- 3️⃣  Basit Login ekranı ----------
class LoginWin(tk.Tk):
    def __init__(self, role_name: str):
        super().__init__()
        self.title(f"{role_name} Girişi")
        self.geometry("400x350")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)

        tk.Label(self, text=f"{role_name} Girişi",
                 font=("Segoe UI", 20, "bold"),
                 bg=BG_MAIN, fg="#154360").pack(pady=20)

        frm = tk.Frame(self, bg=BG_MAIN)
        frm.pack(pady=10)

        tk.Label(frm, text="Kullanıcı Adı:", bg=BG_MAIN).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        tk.Label(frm, text="Şifre:",        bg=BG_MAIN).grid(row=1, column=0, sticky="e", padx=5, pady=5)

        self.ent_user = tk.Entry(frm, width=25)
        self.ent_pass = tk.Entry(frm, width=25, show="•")
        self.ent_user.grid(row=0, column=1, pady=5)
        self.ent_pass.grid(row=1, column=1, pady=5)

        ttk.Button(self, text="Giriş Yap", style="Main.TButton",
                   command=self._check_login).pack(pady=25)

    def _check_login(self):
        user = self.ent_user.get().strip()
        pw   = self.ent_pass.get().strip()

        # Şimdilik sadece boş mu diye kontrol
        if not user or not pw:
            messagebox.showwarning("Uyarı", "Lütfen kullanıcı adı ve şifre girin.")
            return

        # TODO: DB doğrulaması → db.py / repository.py kullan
        messagebox.showinfo("Başarılı", "Giriş başarılı! (sahte)")
        self.destroy()


# ---------- 4️⃣  Uygulamayı başlat ----------
if __name__ == "__main__":
    WelcomeWin().mainloop()