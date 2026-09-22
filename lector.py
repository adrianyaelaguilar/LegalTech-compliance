import cv2
import pytesseract
import re
import sqlite3
from datetime import datetime
import os

LISTAS_RIESGO_ALTO = [
    "AURA030215HSRGMDA5"  # Tu CURP exacta configurada para detonar Riesgo Alto
]

def inicializar_base_de_datos():
    conexion = sqlite3.connect('expedientes.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            fecha TEXT,
            documento TEXT,
            curp TEXT,
            estatus TEXT,
            nivel_riesgo TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

def guardar_en_base_de_datos(empresa, documento, curp, estatus, nivel_riesgo):
    inicializar_base_de_datos()
    conexion = sqlite3.connect('expedientes.db')
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO clientes (empresa, fecha, documento, curp, estatus, nivel_riesgo)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (empresa, fecha_actual, documento, curp, estatus, nivel_riesgo))
    conexion.commit()
    conexion.close()

def evaluar_enfoque_basado_en_riesgos(curp):
    if curp in LISTAS_RIESGO_ALTO:
        return {
            "estatus": "ALERTA: Coincidencia en Listas de Alto Riesgo",
            "nivel_riesgo": "ALTO",
            "accion": "Revision manual obligatoria y debida diligencia reforzada."
        }
    else:
        return {
            "estatus": "APROBADO: Sin Coincidencias de Riesgo",
            "nivel_riesgo": "BAJO",
            "accion": "Expediente simplificado bajo diligencia estandar."
        }

def extraer_y_corregir_curp(ruta_imagen, empresa):
    
    # Configuración inteligente de Tesseract para Windows o Linux (Nube)
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:
        # Ruta estándar para Linux en Streamlit Cloud
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        return {"error": "No se pudo cargar la imagen. Revisa el nombre o la ruta."}
    
    texto_bruto = pytesseract.image_to_string(imagen)

    patron_etiqueta = r'CURP[\s\S]*?([A-Z0-9]{18})'
    busqueda = re.search(patron_etiqueta, texto_bruto)

    if not busqueda:
        return {"error": "No se encontró la CURP en el documento."}

    curp_sucia = busqueda.group(1)
    
    lista = list(curp_sucia)
    for i in range(4, 10):
        if lista[i] == 'S': lista[i] = '5'
        if lista[i] == 'O': lista[i] = '0'
        if lista[i] == 'I': lista[i] = '1'
        if lista[i] == 'Z': lista[i] = '2'
        
    if lista[17] == 'S': lista[17] = '5'
    if lista[17] == 'O': lista[17] = '0'
    if lista[17] == 'I': lista[17] = '1'
    
    curp_perfecta = "".join(lista)
    
    resultado_riesgo = evaluar_enfoque_basado_en_riesgos(curp_perfecta)
    
    guardar_en_base_de_datos(
        empresa, 
        "INE", 
        curp_perfecta, 
        resultado_riesgo["estatus"], 
        resultado_riesgo["nivel_riesgo"]
    )

    return {
        "documento": "INE",
        "curp": curp_perfecta,
        "estatus": resultado_riesgo["estatus"],
        "nivel_riesgo": resultado_riesgo["nivel_riesgo"],
        "accion": resultado_riesgo["accion"]
    }