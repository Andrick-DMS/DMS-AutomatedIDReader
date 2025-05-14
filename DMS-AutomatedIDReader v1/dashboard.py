import os
import uuid
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import subprocess
import threading

CLIENTES_LOG = "clientes/log_clientes.json"

def generar_licencia():
    return f"LIC-{uuid.uuid4().hex[:8].upper()}"

def guardar_registro(cliente, licencia, zip_path):
    os.makedirs("clientes", exist_ok=True)
    if os.path.exists(CLIENTES_LOG):
        with open(CLIENTES_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({
        "cliente": cliente,
        "licencia": licencia,
        "zip": zip_path,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(CLIENTES_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def ver_clientes():
    if os.path.exists(CLIENTES_LOG):
        with open(CLIENTES_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        return "\n".join([f"{d['fecha']} - {d['cliente']} - {d['licencia']}" for d in data])
    return "No hay registros."

def generar_instalador(cliente):
    licencia = generar_licencia()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"{cliente.replace(' ', '_')}_{ts}"
    cliente_dir = f"clientes/{nombre_base}"
    os.makedirs(cliente_dir, exist_ok=True)

    shutil.copy("template/main.py", f"{cliente_dir}/main.py")
    with open(f"{cliente_dir}/licencia.key", "w") as f:
        f.write(licencia)

    exe_name = f"lector_qr_{uuid.uuid4().hex[:6]}"
    try:
        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--name", exe_name,
            "main.py"
        ], cwd=cliente_dir, check=True)
    except Exception as e:
        return None, f"❌ Error compilando ejecutable: {e}"

    exe_path = os.path.join(cliente_dir, "dist", f"{exe_name}.exe")
    if not os.path.exists(exe_path):
        return None, "❌ El ejecutable no se generó correctamente."

    zip_output = f"{cliente_dir}.zip"
    os.makedirs(f"{cliente_dir}/zip_output", exist_ok=True)
    shutil.copy(exe_path, f"{cliente_dir}/zip_output/{exe_name}.exe")
    shutil.copy(f"{cliente_dir}/licencia.key", f"{cliente_dir}/zip_output/licencia.key")

    subprocess.run([
        "powershell",
        "Compress-Archive",
        "-Path", f"{cliente_dir}/zip_output/*",
        "-DestinationPath", zip_output
    ])

    guardar_registro(cliente, licencia, zip_output)

    shutil.rmtree(os.path.join(cliente_dir, "build"), ignore_errors=True)
    shutil.rmtree(os.path.join(cliente_dir, "dist"), ignore_errors=True)
    shutil.rmtree(os.path.join(cliente_dir, "zip_output"), ignore_errors=True)

    spec_path = os.path.join(cliente_dir, f"{exe_name}.spec")
    if os.path.exists(spec_path):
        os.remove(spec_path)

    os.remove(os.path.join(cliente_dir, "main.py"))

    return zip_output, "✅ Instalador generado correctamente."

def abrir_dashboard():
    root = tk.Tk()
    root.title("Generador de Instaladores - Dashboard")

    ttk.Label(root, text="Nombre del Cliente:").grid(row=0, column=0, padx=10, pady=10)
    cliente_entry = ttk.Entry(root, width=40)
    cliente_entry.grid(row=0, column=1, padx=10, pady=10)

    result_label = ttk.Label(root, text="", foreground="green")
    result_label.grid(row=2, column=0, columnspan=2)

    def generar():
        cliente = cliente_entry.get().strip()
        if not cliente:
            messagebox.showwarning("Campos vacíos", "Por favor ingrese el nombre del cliente.")
            return

        carga = tk.Toplevel(root)
        carga.title("Procesando")
        ttk.Label(carga, text="Generando instalador, por favor espere...").pack(padx=20, pady=20)
        carga.resizable(False, False)
        carga.grab_set()
        root.update()

        def crear_y_cerrar():
            path, msg = generar_instalador(cliente)
            carga.destroy()
            result_label.config(text=msg)
            messagebox.showinfo("Proceso finalizado", msg)
            if path and os.path.exists(os.path.dirname(path)):
                os.startfile(os.path.dirname(path))

        threading.Thread(target=crear_y_cerrar).start()

    def mostrar_log():
        log_text = ver_clientes()
        messagebox.showinfo("Clientes registrados", log_text)

    ttk.Button(root, text="Generar Instalador", command=generar).grid(row=1, column=0, padx=10, pady=10)
    ttk.Button(root, text="Ver Clientes", command=mostrar_log).grid(row=1, column=1, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    abrir_dashboard()