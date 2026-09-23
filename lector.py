import cv2
import pytesseract
import re
from datetime import datetime
import os
from supabase import create_client, Client

# --- PEGA TUS LLAVES AQUÍ ADENTRO DE LAS COMILLAS ---
SUPABASE_URL = "https://sotvsjzujjmwylmnkywv.supabase.co"
SUPABASE_KEY = "sb_publishable_NKG06zGEOCh4w6YpaCDKYg_lx78L--Z"
# ----------------------------------------------------

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

LISTAS_RIESGO_ALTO = [
    "AURA030215HSRGMDA5"
]

def guardar_en_base_de_datos(empresa, documento, curp, estatus, nivel_riesgo):
    # Guardado directo en la base de datos corporativa en la nube
    supabase.table('clientes').insert({
        "empresa": empresa,
        "documento": documento,
        "curp": curp,
        "estatus": estatus,
        "nivel_riesgo": nivel_riesgo
    }).execute()

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
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
