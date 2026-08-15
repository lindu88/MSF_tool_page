from tkinter import filedialog
import tkinter as tk
def get_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        folder = filedialog.askdirectory(parent=root, mustexist=True)
    finally:
        root.destroy()

    return folder

def get_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        fn = filedialog.askopenfilename(parent=root)
    finally:
        root.destroy()

    return fn