import os
import uuid
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import subprocess
import threading

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

def generar_instalador(cliente, tiempo, unidad):
    lic_data = generar_licencia(tiempo, unidad)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"{cliente.replace(' ', '_')}_{ts}"
    cliente_dir = os.path.join("clientes", nombre_base)
    os.makedirs(cliente_dir, exist_ok=True)

    shutil.copy(MAIN_SCRIPT, os.path.join(cliente_dir, "main.py"))
    shutil.copy(CONFIGURADOR_SCRIPT, os.path.join(cliente_dir, "crear_configuracion.py"))

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
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--icon", "assets/icono.ico",
            "--name", exe_name,
            "main.py"
        ], cwd=cliente_dir, check=True)

        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--icon", "assets/icono.ico",
            "--name", "crear_configuracion",
            "crear_configuracion.py"
        ], cwd=cliente_dir, check=True)

    except Exception as e:
        return None, f"❌ Error compilando ejecutable: {e}"

    exe_path = os.path.join(cliente_dir, "dist", f"{exe_name}.exe")
    if not os.path.exists(exe_path):
        return None, "❌ El ejecutable no se generó correctamente."

    zip_output = f"{cliente_dir}.zip"
    zip_dir = os.path.join(cliente_dir, "zip_output")
    os.makedirs(zip_dir, exist_ok=True)

    shutil.copy(exe_path, os.path.join(zip_dir, f"{exe_name}.exe"))
    shutil.copy(os.path.join(cliente_dir, "dist", "crear_configuracion.exe"), os.path.join(zip_dir, "crear_configuracion.exe"))
    shutil.copy(os.path.join(cliente_dir, "licencia.key"), os.path.join(zip_dir, "licencia.key"))
    if os.path.exists(config_dest):
        shutil.copytree(config_dest, os.path.join(zip_dir, "configs"))
    shutil.copytree(icon_subfolder, os.path.join(zip_dir, "assets"))

    subprocess.run([
        "powershell", "Compress-Archive",
        "-Path", os.path.join(zip_dir, "*"),
        "-DestinationPath", zip_output
    ])

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
    root.title("Generador de Instaladores - Dashboard")

    ttk.Label(root, text="Nombre del Cliente:").grid(row=0, column=0, padx=10, pady=10)
    cliente_entry = ttk.Entry(root, width=40)
    cliente_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(root, text="Duración de la licencia:").grid(row=1, column=0, padx=10, pady=10)
    duracion_entry = ttk.Entry(root, width=10)
    duracion_entry.insert(0, "1")
    duracion_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=10)

    unidad_var = tk.StringVar(value="Días")
    unidad_menu = ttk.Combobox(root, textvariable=unidad_var, values=["Horas", "Días", "Meses", "Años"], width=10, state="readonly")
    unidad_menu.grid(row=1, column=1, sticky="e", padx=(0, 10), pady=10)

    result_label = ttk.Label(root, text="", foreground="green")
    result_label.grid(row=3, column=0, columnspan=2)

    def generar():
        cliente = cliente_entry.get().strip()
        tiempo = duracion_entry.get().strip()
        unidad = unidad_var.get().strip()
        if not cliente or not tiempo.isdigit():
            messagebox.showwarning("Campos vacíos", "Por favor ingrese todos los campos correctamente.")
            return

        carga = tk.Toplevel(root)
        carga.title("Procesando")
        ttk.Label(carga, text="Generando instalador, por favor espere...").pack(padx=20, pady=20)
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

    ttk.Button(root, text="Generar Instalador", command=generar).grid(row=2, column=0, padx=10, pady=10)
    ttk.Button(root, text="Ver Clientes", command=mostrar_log).grid(row=2, column=1, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    abrir_dashboard()
