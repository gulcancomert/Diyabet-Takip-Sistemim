# gui/login.py
import os, tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from gui.doktor import DoktorWin
from gui.hasta import HastaWin
from repository import Repo

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS   = os.path.join(ROOT_DIR, "assets")

def show_login():
    win = tk.Tk()
    win.title("Giriş")
    win.geometry("400x600")
    win.configure(bg="#EAF2F8")

    # Arka plan görseli
    img_path = os.path.join(ASSETS, "login_screen.png")
    img = Image.open(img_path).resize((400, 600))
    photo = ImageTk.PhotoImage(img)
    bg_lbl = tk.Label(win, image=photo)
    bg_lbl.image = photo
    bg_lbl.place(x=0, y=0)

    # Giriş kutuları
    tk.Label(win, text="TC Kimlik No:", bg="#EAF2F8", font=("Helvetica", 11, "bold")).place(relx=0.5, rely=0.55, anchor="center")
    e_tc = tk.Entry(win, width=20, justify="center")
    e_tc.place(relx=0.5, rely=0.58, anchor="center")

    tk.Label(win, text="Şifre:", bg="#EAF2F8", font=("Helvetica", 11, "bold")).place(relx=0.5, rely=0.63, anchor="center")
    e_pw = tk.Entry(win, show="*", width=20, justify="center")
    e_pw.place(relx=0.5, rely=0.66, anchor="center")

    # Giriş butonu
    btn_login = tk.Button(
        win,
        text="Giriş Yap",
        width=20,
        font=("Helvetica", 12, "bold"),
        bg="#2471A3",
        fg="white",
        command=lambda: login_fn(win, e_tc.get(), e_pw.get())
    )
    btn_login.place(relx=0.5, rely=0.72, anchor="center")

    win.mainloop()

def login_fn(win, tc, pw):
    user = Repo.login(tc.strip(), pw.strip())
    if not user:
        messagebox.showerror("Hatalı Giriş", "TC veya şifre hatalı!")
        return

    win.destroy()

    if user["role"] == "doktor":
        DoktorWin(user).mainloop()
    elif user["role"] == "hasta":
        HastaWin(user).mainloop()
    else:
        messagebox.showerror("Hata", "Rol tanımsız.")
