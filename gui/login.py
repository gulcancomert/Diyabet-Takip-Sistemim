# gui/login.py
import os, tkinter as tk
from PIL import Image, ImageTk
from gui.doktor import open_doktor_panel
from gui.hasta  import open_hasta_panel

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS   = os.path.join(ROOT_DIR, "assets")

def show_login():
    win = tk.Tk()
    win.title("Giriş")
    win.geometry("400x600")
    win.configure(bg="#EAF2F8")           # Daha açık mavi

    # Login ekranı görseli
    img_path = os.path.join(ASSETS, "login_screen.png")
    img      = Image.open(img_path).resize((400, 600))
    photo    = ImageTk.PhotoImage(img)
    bg_lbl   = tk.Label(win, image=photo)
    bg_lbl.image = photo
    bg_lbl.place(x=0, y=0)

    # Doktor / Hasta butonları (arka plandaki tasarımın üstüne şeffaf yerleşir)
    btn_doc = tk.Button(win, text="Doktor Paneli", width=20,
                        font=("Helvetica", 12, "bold"),
                        bg="#2471A3", fg="white",
                        command=lambda: launch_panel(win, open_doktor_panel))
    btn_doc.place(relx=0.5, rely=0.60, anchor="center")

    btn_pat = tk.Button(win, text="Hasta Paneli", width=20,
                        font=("Helvetica", 12, "bold"),
                        bg="#2471A3", fg="white",
                        command=lambda: launch_panel(win, open_hasta_panel))
    btn_pat.place(relx=0.5, rely=0.70, anchor="center")

    win.mainloop()

def launch_panel(win, panel_fn):
    win.destroy()
    panel_fn()