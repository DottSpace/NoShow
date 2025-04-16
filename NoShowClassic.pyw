import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64
import os
import configparser
import requests
import subprocess
import sys
import json
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QApplication, QPlainTextEdit

class CustomErrorDialog(tk.Toplevel):
    def __init__(self, parent, title, message, width=400, height=50):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icona.ico")
        self.iconbitmap(default=icon_path)

        label = tk.Label(self, text=message)
        label.pack(padx=20, pady=10)

        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(image_path):
            logo_image = tk.PhotoImage(file=image_path)
            logo_label = tk.Label(self, image=logo_image)
            logo_label.image = logo_image
            logo_label.pack(pady=10)

        ok_button = tk.Button(self, text="OK", command=self.destroy)
        ok_button.pack(pady=10)

class NoShowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NoShow Classic")
        self.root.geometry("600x430")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icona.ico")
        self.root.iconbitmap(default=self.icon_path)

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)

        if not self.get_config_option("General", "FirstTime", False):
            self.show_welcome_message()
            change_password = self.ask_change_password()
            if change_password:
                self.change_decryption_password()

        username = "NoShowUser"
        password = self.get_config_option("General", "DecryptionPassword", "NoShowPredPass")
        key = hashlib.pbkdf2_hmac('sha256', (username + password).encode(), b'salt', 100000)
        key = base64.urlsafe_b64encode(key)
        key = key.ljust(32, b'=')

        self.cipher_suite = Fernet(key)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Nuovo", command=self.nuovo_file)
        file_menu.add_command(label="Apri", command=self.apri_file)
        file_menu.add_command(label="Salva", command=self.salva_file)
        file_menu.add_command(label="Salva con nome", command=self.salva_con_nome)
        file_menu.add_command(label="Stampa", command=self.stampa_file)
        file_menu.add_separator()
        file_menu.add_command(label="Cambia password", command=self.change_decryption_password)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.on_close)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        self.status_bar_var = tk.BooleanVar(value=self.get_config_option("View", "StatusBar", True))
        self.wrap_text_var = tk.BooleanVar(value=self.get_config_option("View", "WrapText", True))
        self.dark_mode_var = tk.BooleanVar(value=self.get_config_option("View", "DarkMode", False))
        self.selected_font = tk.StringVar(value=self.get_config_option("Font", "SelectedFont", "Arial"))

        font_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Font", menu=font_menu)
        self.font_options = ["Arial", "Helvetica", "Times New Roman", "Courier New",
                             "Verdana", "Georgia", "Palatino", "Garamond",
                             "Bookman", "Avant Garde", "Candara", "Comic Sans MS",
                             "Impact", "Lucida Sans Unicode", "Tahoma", "Trebuchet MS",
                             "Consolas", "Monaco", "Copperplate",
                             "Liberation Serif", "Liberation Sans", "Liberation Mono",
                             "DejaVu Serif", "DejaVu Sans", "DejaVu Sans Mono"]
        for font_option in self.font_options:
            font_menu.add_radiobutton(label=font_option, variable=self.selected_font, command=self.change_font)

        view_menu.add_checkbutton(label="Barra di stato", variable=self.status_bar_var, command=self.update_status_bar)
        view_menu.add_checkbutton(label="A capo automatico", variable=self.wrap_text_var, command=self.update_wrap_mode)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Modalità scura", variable=self.dark_mode_var, command=self.toggle_dark_mode)

        self.text_area = tk.Text(self.root, wrap="word", bg="white", fg="black", insertbackground="black")
        self.text_area.pack(expand=True, fill="both")
        self.text_area.bind('<Key>', self.on_key_press)
        self.text_area.bind('<Configure>', self.update_wrap_mode)

        self.status_bar = tk.Label(self.root, text="", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.current_file = None

        self.update_status_bar()

        # Controlla gli aggiornamenti all'avvio dell'app
        self.check_for_updates()
        self.toggle_dark_mode()

    def show_welcome_message(self):
        messagebox.showinfo("Benvenuto", "Ciao! Benvenuto in NoShow, l'app di testo più sicura: crea, apri e condividi file NoShow e rimani al sicuro!")
        self.save_config_option("General", "FirstTime", True)

    def ask_change_password(self):
        return messagebox.askyesno("Modifica Password", "Vuoi modificare la password di decriptazione?\nSe scegli 'No', verrà utilizzata la password preimpostata.")

    def change_decryption_password(self):
        dialog = ChangePasswordDialog(self.root)
        self.root.wait_window(dialog)
        new_password = dialog.result
        if new_password:
            self.update_decryption_key(new_password)

    def nuovo_file(self):
         self.text_area.delete("1.0", "end")
         self.current_file = None
         self.update_status_bar()
         self.text_area.config(state=tk.NORMAL)  # Abilita il widget di testo
  
  
    def salva_file(self):
        if self.current_file:
            testo = self.text_area.get("1.0", "end-1c")
            font_utilizzato = self.selected_font.get()  # Ottieni il font attuale
            contenuto = json.dumps({"text": testo, "font": font_utilizzato})  # Serializza testo e font in JSON
            with open(self.current_file, "wb") as file:
                encrypted_text = self.cipher_suite.encrypt(contenuto.encode())  # Cripta il contenuto
                file.write(encrypted_text)
        else:
            self.salva_con_nome()




    def salva_con_nome(self):
        testo = self.text_area.get("1.0", "end-1c")
        font_utilizzato = self.selected_font.get()  # Ottieni il font attuale
        contenuto = json.dumps({"text": testo, "font": font_utilizzato})  # Serializza testo e font in JSON
        file_path = filedialog.asksaveasfilename(defaultextension=".NoShow", filetypes=[("NoShow files", "*.NoShow")])
        if file_path:
            with open(file_path, "wb") as file:
                encrypted_text = self.cipher_suite.encrypt(contenuto.encode())  # Cripta il contenuto
                file.write(encrypted_text)
            self.current_file = file_path
        self.update_status_bar()

    def apri_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("NoShow files", "*.NoShow")])
        if file_path:
            decrypted_content = self.decifra_file(file_path)
            if decrypted_content:
                contenuto = json.loads(decrypted_content)  # Decodifica il contenuto JSON
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", contenuto["text"])  # Inserisce il testo
                self.selected_font.set(contenuto.get("font", "Arial"))  # Imposta il font, default "Arial"
                self.change_font()  # Applica il font all'area di testo
                self.current_file = file_path
            self.update_status_bar()


    def decifra_file(self, file_path):
        try:
            with open(file_path, "rb") as file:
                encrypted_text = file.read()
                decrypted_text = self.cipher_suite.decrypt(encrypted_text).decode()
                return decrypted_text
        except (InvalidToken, FileNotFoundError):
            error_message = "Errore: Il file non può essere decifrato. Potrebbe essere danneggiato o utilizza una chiave diversa."
            CustomErrorDialog(self.root, "Errore", error_message, width=590, height=50)
            return None


    def update_status_bar(self, event=None):
        status_text = "Nuovo" if self.current_file is None else os.path.basename(self.current_file)
        self.status_bar.config(text=status_text)

    def on_key_press(self, event):
        self.update_status_bar()

    def update_wrap_mode(self, event=None):
        wrap_mode = "none" if not self.wrap_text_var.get() else "word"
        self.text_area.config(wrap=wrap_mode)

    def change_font(self):
        selected_font = self.selected_font.get()
        self.text_area.config(font=(selected_font, 12))
    def toggle_dark_mode(self):
        if self.dark_mode_var.get():
            self.root.config(bg="black")
            self.text_area.config(bg="#383838", fg="white", insertbackground="white")
            self.status_bar.config(bg="#383838", fg="white")
        else:
            self.root.config(bg="white")
            self.text_area.config(bg="white", fg="black", insertbackground="black")
            self.status_bar.config(bg="white", fg="black")
        self.save_config_option("View", "DarkMode", self.dark_mode_var.get())

    def stampa_file(self):
        testo_da_stampare = self.text_area.get("1.0", tk.END)

        app = QApplication([])

        text_edit = QPlainTextEdit()
        text_edit.setPlainText(testo_da_stampare)

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer)
        if dialog.exec_() == QPrintDialog.Accepted:
            text_edit.print_(printer)


    def get_config_option(self, section, option, default):
        if self.config.has_section(section) and self.config.has_option(section, option):
            return self.config.getboolean(section, option) if isinstance(default, bool) else self.config.get(section, option)
        return default
    
    def save_config_option(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))
        with open(self.config_file_path, 'w') as configfile:
            self.config.write(configfile)

    def save_config(self):
        with open(self.config_file_path, "w") as configfile:
            self.config.write(configfile)

    def update_decryption_key(self, new_password):
        username = "NoShowUser"
        key = hashlib.pbkdf2_hmac('sha256', (username + new_password).encode(), b'salt', 100000)
        key = base64.urlsafe_b64encode(key)
        key = key.ljust(32, b'=')
        self.cipher_suite = Fernet(key)
        self.save_config_option("General", "DecryptionPassword", new_password)

    def on_close(self):
        self.root.destroy()

    def check_for_updates(self):
        try:
            response = requests.get("https://api.github.com/repos/DottSpace/NoShowUpdates/releases/latest")
            response.raise_for_status()
            latest_release = response.json()

            latest_version = latest_release["tag_name"]
            download_url = latest_release["assets"][0]["browser_download_url"]

            current_version = "NoShow5.0"  # Aggiorna questa versione con quella attuale del tuo software

            if latest_version > current_version:
                response = messagebox.askyesno("Aggiornamento Disponibile", f"Abbiamo trovato la versione {latest_version}. Vuoi scaricarla e installarla?")
                if response:
                    self.download_and_install_update(download_url, latest_version)
            else:
                messagebox.showinfo("Aggiornamento", "Sei già aggiornato all'ultima versione.")

        except requests.RequestException as e:
            messagebox.showerror("Errore", f"Errore durante il controllo degli aggiornamenti: {e}")

    def download_and_install_update(self, download_url, version):
        try:
            # Percorso dove verrà salvato il nuovo file
            update_path = os.path.join(os.path.dirname(sys.argv[0]), "update.exe")

            # Scarica il file .exe della nuova versione
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            with open(update_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            messagebox.showinfo("Aggiornamento", f"Download completato. L'aggiornamento alla versione {version} verrà installato ora.")

            # Avvia il nuovo file .exe
            subprocess.Popen([update_path], shell=True)

            # Esegui il file di disinstallazione del vecchio programma
            uninstall_path = os.path.join(os.path.dirname(sys.argv[0]), "Uninstall.exe")
            if os.path.exists(uninstall_path):
                subprocess.Popen([uninstall_path], shell=True)

            # Termina il programma corrente
            sys.exit()

        except requests.RequestException as e:
            messagebox.showerror("Errore", f"Errore durante il download dell'aggiornamento: {e}")

class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cambia Password")
        self.geometry("300x150")
        self.result = None

        label = tk.Label(self, text="Nuova password:")
        label.pack(pady=10)

        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=10)

        change_button = tk.Button(self, text="Cambia", command=self.change_password)
        change_button.pack(pady=10)

    def change_password(self):
        self.result = self.password_entry.get()
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NoShowApp(root)
    root.mainloop()


