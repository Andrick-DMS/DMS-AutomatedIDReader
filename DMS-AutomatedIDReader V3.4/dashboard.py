import os
import uuid
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import subprocess
import threading
import openpyxl
import time

CLIENTES_LOG = "clientes/log_clientes.json"
TEMPLATE_DIR = "template"
MAIN_SCRIPT = os.path.join(TEMPLATE_DIR, "main.py")
CONFIGURADOR_SCRIPT = os.path.join(TEMPLATE_DIR, "crear_configuracion.py")
CONFIGS_SRC = os.path.join(TEMPLATE_DIR, "configs")
ICON_PATH = os.path.join(TEMPLATE_DIR, "DMS_icono_circulo_i.ico")

def calcular_expiracion(valor, unidad):
    ahora = datetime.now()
    if unidad == "Horas":
        return ahora + timedelta(hours=int(valor))
    elif unidad == "Días":
        return ahora + timedelta(days=int(valor))
    elif unidad == "Meses":
        return ahora + timedelta(days=int(valor) * 30)
    elif unidad == "Años":
        return ahora + timedelta(days=int(valor) * 365)
    return ahora

def generar_licencia(valor, unidad):
    lic = f"LIC-{uuid.uuid4().hex[:8].upper()}"
    expira = calcular_expiracion(valor, unidad)
    return {
        "licencia": lic,
        "expira": expira.isoformat()
    }

def guardar_registro(cliente, lic_data, zip_path):
    os.makedirs("clientes", exist_ok=True)
    if os.path.exists(CLIENTES_LOG):
        with open(CLIENTES_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({
        "cliente": cliente,
        "licencia": lic_data["licencia"],
        "expira": lic_data["expira"],
        "zip": zip_path,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(CLIENTES_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def ver_clientes():
    if os.path.exists(CLIENTES_LOG):
        with open(CLIENTES_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        return "\n".join([f"{d['fecha']} - {d['cliente']} - {d['licencia']} - expira: {d['expira']}" for d in data])
    return "No hay registros."

def crear_plantilla_vetados(ruta):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hoja1"
    ws.append(["Cedula"])
    wb.save(ruta)

def generar_instalador(cliente, tiempo, unidad):
    lic_data = generar_licencia(tiempo, unidad)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"{cliente.replace(' ', '_')}_{ts}"
    cliente_dir = os.path.join("clientes", nombre_base)
    os.makedirs(cliente_dir, exist_ok=True)

    shutil.copy(MAIN_SCRIPT, os.path.join(cliente_dir, "main.py"))
    shutil.copy(CONFIGURADOR_SCRIPT, os.path.join(cliente_dir, "crear_configuracion.py"))

    plantilla_path = os.path.join(cliente_dir, "vetados.xlsx")
    crear_plantilla_vetados(plantilla_path)

    icon_subfolder = os.path.join(cliente_dir, "assets")
    os.makedirs(icon_subfolder, exist_ok=True)
    icon_dest = os.path.join(icon_subfolder, "icono.ico")
    shutil.copy(ICON_PATH, icon_dest)

    config_dest = os.path.join(cliente_dir, "configs")
    if os.path.exists(CONFIGS_SRC):
        shutil.copytree(CONFIGS_SRC, config_dest)
    else:
        os.makedirs(config_dest)

    with open(os.path.join(cliente_dir, "licencia.key"), "w", encoding="utf-8") as f:
        json.dump(lic_data, f, indent=2)

    exe_name = f"lector_qr_{uuid.uuid4().hex[:6]}"
    try:
        subprocess.run([
            "pyinstaller", "--onefile", "--noconsole",
            "--icon", "assets/icono.ico",
            "--name", exe_name, "main.py"
        ], cwd=cliente_dir, check=True)

        subprocess.run([
            "pyinstaller", "--onefile", "--noconsole",
            "--icon", "assets/icono.ico",
            "--name", "crear_configuracion", "crear_configuracion.py"
        ], cwd=cliente_dir, check=True)

    except Exception as e:
        return None, f"❌ Error compilando ejecutable: {e}"

    zip_output = f"{cliente_dir}.zip"
    zip_dir = os.path.join(cliente_dir, "zip_output")
    os.makedirs(zip_dir, exist_ok=True)

    time.sleep(3)  # Espera para asegurar que los .exe estén libres

    shutil.copy(os.path.join(cliente_dir, "dist", f"{exe_name}.exe"), os.path.join(zip_dir, f"{exe_name}.exe"))
    shutil.copy(os.path.join(cliente_dir, "dist", "crear_configuracion.exe"), os.path.join(zip_dir, "crear_configuracion.exe"))
    shutil.copy(os.path.join(cliente_dir, "licencia.key"), os.path.join(zip_dir, "licencia.key"))
    shutil.copy(plantilla_path, os.path.join(zip_dir, "vetados.xlsx"))

    if os.path.exists(config_dest):
        shutil.copytree(config_dest, os.path.join(zip_dir, "configs"))
    shutil.copytree(icon_subfolder, os.path.join(zip_dir, "assets"))

    shutil.make_archive(zip_output.replace(".zip", ""), 'zip', zip_dir)

    guardar_registro(cliente, lic_data, zip_output)

    shutil.rmtree(os.path.join(cliente_dir, "build"), ignore_errors=True)
    shutil.rmtree(os.path.join(cliente_dir, "dist"), ignore_errors=True)
    shutil.rmtree(zip_dir, ignore_errors=True)
    for file in ["main.py", "crear_configuracion.py", f"{exe_name}.spec", "crear_configuracion.spec"]:
        path = os.path.join(cliente_dir, file)
        if os.path.exists(path):
            os.remove(path)

    return zip_output, "✅ Instalador generado correctamente."

def abrir_dashboard():
    root = tk.Tk()
    root.title("DMS - Generador de Instaladores")
    root.geometry("480x420")
    root.configure(bg="#212121")

    root.update_idletasks()
    w, h = 480, 420
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Estilo.TFrame", background="#212121")
    style.configure("TLabel", background="#212121", foreground="white", font=("Segoe UI", 12))
    style.configure("Estilo.TEntry", font=("Segoe UI", 11), relief="flat", padding=5)
    style.configure("Estilo.TButton", background="#e53935", foreground="white", font=("Segoe UI", 11),
                    borderwidth=0, focusthickness=0, padding=6)
    style.configure("Estilo.TCombobox", fieldbackground="white", background="white", foreground="black")

    style.map("Estilo.TButton",
              background=[('active', '#d32f2f')],
              foreground=[('!disabled', 'white')])

    frame = ttk.Frame(root, padding=20, style="Estilo.TFrame")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    ttk.Label(frame, text="DMS", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))

    ttk.Label(frame, text="Nombre del Cliente:").pack(anchor="center")
    cliente_entry = ttk.Entry(frame, width=40, style="Estilo.TEntry")
    cliente_entry.pack(pady=(0, 15))

    ttk.Label(frame, text="Duración de la licencia:").pack(anchor="center")
    duracion_frame = ttk.Frame(frame, style="Estilo.TFrame")
    duracion_frame.pack(pady=(5, 20))

    duracion_entry = ttk.Entry(duracion_frame, width=10, style="Estilo.TEntry")
    duracion_entry.insert(0, "1")
    duracion_entry.pack(side="left", padx=(0, 10))

    unidad_var = tk.StringVar(value="Días")
    unidad_menu = ttk.Combobox(duracion_frame, textvariable=unidad_var,
                               values=["Horas", "Días", "Meses", "Años"],
                               width=10, state="readonly", style="Estilo.TCombobox")
    unidad_menu.pack(side="left")

    result_label = ttk.Label(frame, text="", foreground="#e53935", background="#212121")
    result_label.pack()

    def generar():
        cliente = cliente_entry.get().strip()
        tiempo = duracion_entry.get().strip()
        unidad = unidad_var.get().strip()
        if not cliente or not tiempo.isdigit():
            messagebox.showwarning("Campos vacíos", "Por favor ingrese todos los campos correctamente.")
            return

        carga = tk.Toplevel(root)
        carga.title("Procesando")
        carga.configure(bg="#212121")
        ttk.Label(carga, text="Generando instalador, por favor espere...",
                  background="#212121", foreground="white").pack(padx=20, pady=20)
        carga.resizable(False, False)
        carga.grab_set()
        root.update()

        def crear_y_cerrar():
            path, msg = generar_instalador(cliente, int(tiempo), unidad)
            carga.destroy()
            result_label.config(text=msg)
            messagebox.showinfo("Proceso finalizado", msg)
            if path and os.path.exists(os.path.dirname(path)):
                os.startfile(os.path.dirname(path))

        threading.Thread(target=crear_y_cerrar).start()

    def mostrar_log():
        log_text = ver_clientes()
        messagebox.showinfo("Clientes registrados", log_text)

    ttk.Button(frame, text="Generar Instalador", command=generar, style="Estilo.TButton").pack(pady=(10, 5))
    ttk.Button(frame, text="Ver Clientes", command=mostrar_log, style="Estilo.TButton").pack()

    root.mainloop()

if __name__ == "__main__":
    abrir_dashboard()