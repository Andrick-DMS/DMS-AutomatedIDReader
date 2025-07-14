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
        self.ventana.title("DMS - Crear Configuración")
        self.ventana.geometry("500x620")
        self.ventana.configure(bg=COLOR_BG)

        try:
            self.ventana.iconbitmap(default=ICON_PATH)
        except Exception as e:
            print(f"⚠️ No se pudo aplicar ícono a la ventana: {e}")

        style = ttk.Style(self.ventana)
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BG)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 11))
        style.configure("TEntry", fieldbackground="white", background="white", foreground="black", relief="flat", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11), padding=6, background=COLOR_ACCENT, foreground="white")
        style.map("TButton", background=[('active', '#d32f2f')])

        # Encabezado
        frame = ttk.Frame(self.ventana, padding=20, style="TFrame")
        frame.place(relx=0.5, rely=0.03, anchor="n")
        ttk.Label(frame, text="DMS", font=("Segoe UI", 20, "bold")).pack()

        # Contenedor del formulario
        formulario = ttk.Frame(self.ventana, padding=20, style="TFrame")
        formulario.place(relx=0.5, rely=0.13, anchor="n")

        ttk.Label(formulario, text="Nombre de la configuración:", style="TLabel").pack(pady=(0, 5))
        self.entry_nombre = ttk.Entry(formulario, width=35, style="TEntry")
        self.entry_nombre.pack(pady=(0, 20))

        campos = [
            "Primer Apellido", "Segundo Apellido", "Nombre", "Cedula", "Sexo",
            "Fecha de Nacimiento", "Fecha de Expiracion"
        ]

        self.campos_vars = []
        self.tab_vars = []

        for campo in campos:
            ttk.Label(formulario, text=campo + ":", style="TLabel").pack(anchor="w", padx=10)
            row_frame = ttk.Frame(formulario, style="TFrame")
            row_frame.pack(pady=5)

            var = StringVar(value=campo)
            tab = StringVar(value="0")
            self.campos_vars.append(var)
            self.tab_vars.append(tab)

            ttk.Entry(row_frame, textvariable=var, width=30, style="TEntry").pack(side="left", padx=(0, 10))
            ttk.Entry(row_frame, textvariable=tab, width=5, style="TEntry").pack(side="left")

        ttk.Button(self.ventana, text="Guardar Configuración", command=self.guardar_config).place(relx=0.5, rely=0.93, anchor="center")

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
