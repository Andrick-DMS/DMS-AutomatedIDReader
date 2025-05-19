import os
import json
from tkinter import Tk, Label, Entry, StringVar, Button, messagebox

CONFIG_DIR = "configs"

class CrearConfiguracionGUI:
    def __init__(self):
        self.ventana = Tk()
        self.ventana.title("Crear Nueva Configuración")
        self.ventana.geometry("500x370")

        Label(self.ventana, text="Nombre de la configuración:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_nombre = Entry(self.ventana, width=30)
        self.entry_nombre.grid(row=0, column=1, padx=10, pady=5)

        self.campos_vars = []
        self.tab_vars = []

        campos = ["Primer Apellido", "Segundo Apellido", "Nombre", "Cedula", "Sexo", 
                 "Fecha de Nacimiento", "Fecha de Expiracion"]

        for i, campo in enumerate(campos):
            Label(self.ventana, text=campo).grid(row=i+1, column=0, padx=10, pady=2, sticky="w")
            var = StringVar(value=campo)
            tab = StringVar(value="0")
            self.campos_vars.append(var)
            self.tab_vars.append(tab)
            Entry(self.ventana, textvariable=var, width=20).grid(row=i+1, column=1)
            Entry(self.ventana, textvariable=tab, width=5).grid(row=i+1, column=2)

        Button(self.ventana, text="Guardar Configuración", command=self.guardar_config).grid(
            row=len(campos)+2, column=0, columnspan=3, pady=10)

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
