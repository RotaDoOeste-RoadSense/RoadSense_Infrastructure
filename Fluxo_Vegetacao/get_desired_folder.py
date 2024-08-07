import tkinter as tk
from tkinter import filedialog

def selecionar_pasta():
    root = tk.Tk()
    root.withdraw()
    pasta_selecionada = filedialog.askdirectory()
    return pasta_selecionada

pasta = selecionar_pasta()