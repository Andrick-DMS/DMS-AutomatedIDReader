import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, StringVar

CONFIG_DIR = "configs"
ICON_PATH = os.path.join(os.path.dirname(sys.argv[0]), "assets", "icono.ico")

COLOR_BG = "#212121"
COLOR_TEXT = "white"
COLOR_ACCENT = "#e53935"

class CrearConfiguracionGUI:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Crear Nueva Configuración")
        self.ventana.geometry("520x500")
        self.ventana.configure(bg=COLOR_BG)

        try:
            self.ventana.iconbitmap(default=ICON_PATH)
        except Exception as e:
            print(f"⚠️ No se pudo aplicar ícono a la ventana: {e}")

        style = ttk.Style(self.ventana)
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 11))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11), padding=6, background=COLOR_ACCENT, foreground="white")
        style.map("TButton", background=[('active', '#d32f2f')])

        frame = ttk.Frame(self.ventana, padding=20, style="TFrame")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="Nombre de la configuración:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_nombre = ttk.Entry(frame, width=30)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=5)

        self.campos_vars = []
        self.tab_vars = []

        campos = ["Primer Apellido", "Segundo Apellido", "Nombre", "Cedula", "Sexo", 
                  "Fecha de Nacimiento", "Fecha de Expiracion"]

        for i, campo in enumerate(campos):
            ttk.Label(frame, text=campo + ":").grid(row=i+1, column=0, sticky="w", padx=5, pady=2)
            var = StringVar(value=campo)
            tab = StringVar(value="0")
            self.campos_vars.append(var)
            self.tab_vars.append(tab)

            ttk.Entry(frame, textvariable=var, width=20).grid(row=i+1, column=1, padx=5, pady=2)
            ttk.Entry(frame, textvariable=tab, width=5).grid(row=i+1, column=2, padx=5, pady=2)

        ttk.Button(frame, text="Guardar Configuración", command=self.guardar_config).grid(
            row=len(campos)+2, column=0, columnspan=3, pady=20
        )

        self.ventana.mainloop()

    def guardar_config(self):
        nombre = self.entry_nombre.get().strip().replace(" ", "_")
        if not nombre:
            messagebox.showerror("Error", "El nombre no puede estar vacío.")
            return

        os.makedirs(CONFIG_DIR, exist_ok=True)
        filename = nombre + ".json"
        path = os.path.join(CONFIG_DIR, filename)

        if os.path.exists(path):
            messagebox.showerror("Error", f"Ya existe una configuración llamada '{filename}'.")
            return

        campos = []
        for i in range(len(self.campos_vars)):
            dato = self.campos_vars[i].get()
            try:
                tabs = int(self.tab_vars[i].get())
            except ValueError:
                tabs = 0
            campos.append({"dato": dato, "tabuladores": tabs})

        config = {"nombre": nombre, "campos": campos}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        messagebox.showinfo("Guardado", f"Configuración '{filename}' guardada.")
        self.ventana.destroy()

if __name__ == "__main__":
    CrearConfiguracionGUI()
