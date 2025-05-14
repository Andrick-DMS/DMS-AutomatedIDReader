import os
import json
import sys
import ctypes
import pyautogui
import serial
import time
import threading
from datetime import datetime
from tkinter import Tk, simpledialog, ttk
from PIL import Image, ImageDraw
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
import serial.tools.list_ports

VERSION = "1.0.0"
LIC_FILE = "licencia.key"
CACHE_FILE = "licencia_activada.json"
LOG_FILE = "logs/licencias.log"

def registrar_licencia():
    os.makedirs("logs", exist_ok=True)
    root = Tk()
    root.withdraw()
    licencia = simpledialog.askstring("Activación", "Ingrese su licencia:")
    if not licencia:
        ctypes.windll.user32.MessageBoxW(0, "No se ingresó ninguna licencia.", "Licencia requerida", 0x10)
        sys.exit(1)

    with open(CACHE_FILE, "w") as cache:
        json.dump({"licencia": licencia.strip()}, cache)

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now()}] Licencia activada: {licencia.strip()}\n")
    root.destroy()

def validar_licencia():
    os.makedirs("logs", exist_ok=True)

    if os.path.exists(CACHE_FILE):
        return True
    elif os.path.exists(LIC_FILE):
        with open(LIC_FILE, "r") as f:
            licencia = f.read().strip()
        with open(CACHE_FILE, "w") as cache:
            json.dump({"licencia": licencia}, cache)
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now()}] Licencia activada: {licencia}\n")
        return True
    else:
        registrar_licencia()
        return True

def decode_cedula_data(encoded_bytes):
    xor_key = bytearray([39, 48, 4, 160, 0, 15, 147, 18, 160, 209, 51, 224, 3, 208, 0, 223, 0])
    decoded_bytes = bytearray(len(encoded_bytes))
    for i in range(len(encoded_bytes)):
        decoded_bytes[i] = encoded_bytes[i] ^ xor_key[i % len(xor_key)]

    def extract_string(data, start, length):
        return ''.join(chr(b) for b in data[start:start+length]).split('\x00')[0].strip()

    sexo_raw = extract_string(decoded_bytes, 91, 1).upper()
    sexo = "MASCULINO" if sexo_raw == "M" else "FEMENINO" if sexo_raw == "F" else "DESCONOCIDO"

    def formato_fecha(fecha):
        return f"{fecha[6:8]}/{fecha[4:6]}/{fecha[0:4]}" if len(fecha) == 8 else fecha

    return {
        "Cedula": extract_string(decoded_bytes, 0, 9),
        "Primer Apellido": extract_string(decoded_bytes, 9, 26),
        "Segundo Apellido": extract_string(decoded_bytes, 35, 26),
        "Nombre": extract_string(decoded_bytes, 61, 30),
        "Sexo": sexo,
        "Fecha de Nacimiento": formato_fecha(extract_string(decoded_bytes, 92, 8)),
        "Fecha de Expiracion": formato_fecha(extract_string(decoded_bytes, 100, 8))
    }

def guardar_log(datos):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/detalle.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {datos}\n")

def escribir_en_formulario(datos):
    time.sleep(0.3)
    pyautogui.write(datos.get("Primer Apellido", ""))
    pyautogui.press("tab")
    pyautogui.write(datos.get("Nombre", ""))
    pyautogui.press("tab")
    pyautogui.press("tab")
    pyautogui.write(datos.get("Cedula", ""))
    pyautogui.press("tab")
    for _ in range(6):
        pyautogui.press("tab")
    pyautogui.write(datos.get("Fecha de Nacimiento", ""))

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
                        data = ser.read(ser.in_waiting)
                        buffer.extend(data)
                    if len(buffer) >= 600:
                        callback_log(f"✅ {puerto} detectado como lector.")
                        return puerto
        except Exception as e:
            callback_log(f"❌ {puerto} falló: {e}")
    callback_log("🔴 No se detectó lector QR.")
    return None

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
                    escribir_en_formulario(datos)
    except Exception as e:
        print(f"Error: {e}")

def ocultar_consola():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def crear_icono_tray(callback):
    img = Image.new("RGB", (64, 64), (50, 50, 200))
    d = ImageDraw.Draw(img)
    d.ellipse((16, 16, 48, 48), fill=(255, 255, 255))
    icon = TrayIcon("QR Lector", img, menu=TrayMenu(TrayMenuItem("Salir", lambda i, j: callback(i))))
    threading.Thread(target=icon.run, daemon=True).start()

if __name__ == "__main__":
    validar_licencia()

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
            estado_root.withdraw()
            ocultar_consola()
        estado_root.destroy()

    hilo_calibracion = threading.Thread(target=calibrar)
    hilo_calibracion.start()
    estado_root.mainloop()

    if com_detectado:
        threading.Thread(target=escuchar_en_segundo_plano, args=(com_detectado[0],), daemon=True).start()

    crear_icono_tray(lambda i: os._exit(0))