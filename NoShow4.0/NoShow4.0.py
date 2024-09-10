import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64
import os
import configparser
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QApplication, QPlainTextEdit





def show_libraries():
    libraries = [
        'tkinter',
        'filedialog',
        'messagebox',
        'simpledialog',
        'cryptography.fernet',
        'hashlib',
        'base64',
        'os',
        'configparser',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtWidgets'
    ]
    libraries_str = "\n".join(libraries)
    messagebox.showinfo("Le librerie sono", libraries_str)

def main():
    print("Non pensavate mica che vi davo il codice! hahah                                                                                                                                                                                                        Premi Invio")
    input()  # Attende che l'utente prema Invio
    show_libraries()

if __name__ == "__main__":
    main()
