import os
import sys
import json
import ctypes
import serial
import time
import threading
import pyautogui
import serial.tools.list_ports
from datetime import datetime, timedelta
from tkinter import Tk, Toplevel, simpledialog, messagebox
from tkinter import ttk
from PIL import Image, ImageDraw
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem

VERSION = "1.0.1"
LIC_FILE = "licencia.key"
CACHE_FILE = "licencia_activada.json"
LOG_FILE = "logs/licencias.log"
CONFIG_DIR = "configs"
CONFIG_ACTUAL = os.path.join(CONFIG_DIR, "config_actual.json")
CONFIG_DEFECTO = os.path.join(CONFIG_DIR, "formulario_visitantes.json")

class SelectorConfiguracionGUI:
    def __init__(self, root=None):
        self.ventana = Toplevel(root) if root else Tk()
        self.ventana.title("Seleccionar Configuración")
        self.ventana.geometry("420x250")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg="#f5f5f5")

        self.ventana.update_idletasks()
        w = self.ventana.winfo_width()
        h = self.ventana.winfo_height()
        x = (self.ventana.winfo_screenwidth() // 2) - (w // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (h // 2)
        self.ventana.geometry(f"+{x}+{y}")

        style = ttk.Style(self.ventana)
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 12), background="#f5f5f5")
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("TCombobox", font=("Segoe UI", 11))

        frame = ttk.Frame(self.ventana, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Seleccione la configuración que desea activar:").pack(pady=(10, 10))

        disponibles = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json') and f != 'config_actual.json']
        if not disponibles:
            messagebox.showerror("Sin configuraciones", "No hay configuraciones disponibles.")
            self.ventana.destroy()
            return

        self.combo = ttk.Combobox(frame, values=disponibles, state='readonly', width=40)
        self.combo.pack(pady=(0, 20))
        self.combo.set(disponibles[0])

        ttk.Button(frame, text="Activar", command=self.guardar_seleccion).pack()

        self.ventana.grab_set()
        self.ventana.focus_force()
        self.ventana.wait_window()

    def guardar_seleccion(self):
        seleccion = self.combo.get()
        if seleccion:
            try:
                with open(CONFIG_ACTUAL, 'w', encoding='utf-8') as f:
                    json.dump({"activa": seleccion}, f, indent=2)
                self.ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")


def inicializar_configuracion():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_DEFECTO):
        config = {
            "nombre": "Formulario Visitantes",
            "campos": [
                {"dato": "Primer Apellido", "tabuladores": 0},
                {"dato": "Nombre", "tabuladores": 1},
                {"dato": "Cedula", "tabuladores": 2},
                {"dato": "Fecha de Nacimiento", "tabuladores": 3}
            ]
        }
        with open(CONFIG_DEFECTO, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    if not os.path.exists(CONFIG_ACTUAL):
        with open(CONFIG_ACTUAL, "w", encoding="utf-8") as f:
            json.dump({"activa": "formulario_visitantes.json"}, f, indent=2)


def cargar_configuracion_activa():
    try:
        with open(CONFIG_ACTUAL, "r", encoding="utf-8") as f:
            activa = json.load(f)["activa"]
        with open(os.path.join(CONFIG_DIR, activa), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar la configuración activa: {e}")
        return None


def parse_duracion(txt):
    txt = txt.lower()
    if "a" in txt:
        return timedelta(days=int(txt.replace("a", "")) * 365)
    elif "m" in txt and not "min" in txt:
        return timedelta(days=int(txt.replace("m", "")) * 30)
    elif "d" in txt:
        return timedelta(days=int(txt.replace("d", "")))
    elif "h" in txt:
        return timedelta(hours=int(txt.replace("h", "")))
    return timedelta(days=1)


def registrar_licencia():
    os.makedirs("logs", exist_ok=True)
    root = Tk()
    root.withdraw()
    licencia = simpledialog.askstring("Activación", "Ingrese su licencia:")
    if not licencia:
        ctypes.windll.user32.MessageBoxW(0, "No se ingresó ninguna licencia.", "Licencia requerida", 0x10)
        sys.exit(1)
    duracion = simpledialog.askstring("Duración", "¿Cuánto dura? (ej: 1d, 5h, 2m, 1a):")
    now = datetime.now()
    delta = parse_duracion(duracion)
    expira = now + delta
    lic_data = {"licencia": licencia.strip(), "expira": expira.isoformat()}
    with open(CACHE_FILE, "w") as cache:
        json.dump(lic_data, cache)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{now}] Licencia activada manual: {licencia.strip()}\n")
    root.destroy()


def validar_licencia():
    os.makedirs("logs", exist_ok=True)
    lic_data = None
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            lic_data = json.load(f)
    elif os.path.exists(LIC_FILE):
        with open(LIC_FILE, "r", encoding="utf-8") as f:
            lic_data = json.load(f)
        with open(CACHE_FILE, "w", encoding="utf-8") as cache:
            json.dump(lic_data, cache)
    if lic_data:
        try:
            expira = datetime.fromisoformat(lic_data["expira"])
            if datetime.now() > expira:
                os.remove(CACHE_FILE)
                if os.path.exists(LIC_FILE):
                    os.remove(LIC_FILE)
                ctypes.windll.user32.MessageBoxW(0, "La licencia ha expirado.", "Licencia Inválida", 0x10)
                sys.exit(1)
            return True
        except Exception as e:
            print(f"Error al verificar licencia: {e}")
            return False
    else:
        registrar_licencia()
        return True


def decode_cedula_data(encoded_bytes):
    xor_key = bytearray([39, 48, 4, 160, 0, 15, 147, 18, 160, 209, 51, 224, 3, 208, 0, 223, 0])
    decoded_bytes = bytearray(len(encoded_bytes))
    for i in range(len(encoded_bytes)):
        decoded_bytes[i] = encoded_bytes[i] ^ xor_key[i % len(xor_key)]

    def extract(data, start, length):
        return ''.join(chr(b) for b in data[start:start+length]).split('\x00')[0].strip()

    sexo_raw = extract(decoded_bytes, 91, 1).upper()
    sexo = "MASCULINO" if sexo_raw == "M" else "FEMENINO" if sexo_raw == "F" else "DESCONOCIDO"

    def formato_fecha(fecha):
        return f"{fecha[6:8]}/{fecha[4:6]}/{fecha[0:4]}" if len(fecha) == 8 else fecha

    return {
        "Cedula": extract(decoded_bytes, 0, 9),
        "Primer Apellido": extract(decoded_bytes, 9, 26),
        "Segundo Apellido": extract(decoded_bytes, 35, 26),
        "Nombre": extract(decoded_bytes, 61, 30),
        "Sexo": sexo,
        "Fecha de Nacimiento": formato_fecha(extract(decoded_bytes, 92, 8)),
        "Fecha de Expiracion": formato_fecha(extract(decoded_bytes, 100, 8))
    }


def escribir_con_configuracion(datos, config):
    for campo in config.get("campos", []):
        for _ in range(campo.get("tabuladores", 0)):
            pyautogui.press("tab")
        valor = datos.get(campo.get("dato"), "")
        pyautogui.write(valor)
        pyautogui.press("tab")


def guardar_log(datos):
    os.makedirs("logs", exist_ok=True)
    with open("logs/detalle.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {datos}\n")


def escuchar_en_segundo_plano(puerto):
    try:
        with serial.Serial(puerto, baudrate=9600, timeout=1) as ser:
            while True:
                buffer = bytearray()
                start_time = time.time()
                while time.time() - start_time < 5:
                    if ser.in_waiting:
                        buffer.extend(ser.read(ser.in_waiting))
                        if len(buffer) >= 600:
                            break
                if len(buffer) >= 600:
                    datos = decode_cedula_data(buffer)
                    guardar_log(datos)
                    config = cargar_configuracion_activa()
                    if config:
                        escribir_con_configuracion(datos, config)
    except Exception as e:
        print(f"Error: {e}")


def ocultar_consola():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


def encontrar_lector_qr_por_actividad(callback_log):
    for p in serial.tools.list_ports.comports():
        puerto = p.device
        callback_log(f"🧪 Escuchando {puerto}... Pasa la cédula para calibrar")
        try:
            with serial.Serial(puerto, baudrate=9600, timeout=1) as ser:
                buffer = bytearray()
                start_time = time.time()
                while time.time() - start_time < 5:
                    if ser.in_waiting:
                        buffer.extend(ser.read(ser.in_waiting))
                    if len(buffer) >= 600:
                        callback_log(f"✅ {puerto} detectado como lector.")
                        return puerto
        except Exception as e:
            callback_log(f"❌ {puerto} falló: {e}")
    callback_log("🔴 No se detectó lector QR.")
    return None


if __name__ == "__main__":
    validar_licencia()
    inicializar_configuracion()

    estado_root = Tk()
    estado_root.title(f"Calibrando lector QR - v{VERSION}")
    label_estado = ttk.Label(estado_root, text="Inicializando...", font=("Arial", 12))
    label_estado.pack(padx=30, pady=30)

    def actualizar_estado(msg):
        label_estado.config(text=msg)
        estado_root.update()

    com_detectado = []

    def calibrar():
        com = encontrar_lector_qr_por_actividad(actualizar_estado)
        if com:
            com_detectado.append(com)
        estado_root.destroy()

    threading.Thread(target=calibrar).start()
    estado_root.mainloop()

    if com_detectado:
        root_global = Tk()
        root_global.withdraw()
        SelectorConfiguracionGUI(root_global)
        root_global.destroy()

        ocultar_consola()
        threading.Thread(target=escuchar_en_segundo_plano, args=(com_detectado[0],), daemon=True).start()

        def salir(icon):
            icon.stop()
            os._exit(0)

        img = Image.new("RGB", (64, 64), (50, 50, 200))
        d = ImageDraw.Draw(img)
        d.ellipse((16, 16, 48, 48), fill=(255, 255, 255))

        icon = TrayIcon("QR Lector", img, menu=TrayMenu(
            TrayMenuItem("Salir", salir)
        ))

        icon.run()