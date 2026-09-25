import cv2
import pytesseract
import re
import os
from supabase import create_client, Client

# --- TUS LLAVES DE SUPABASE ---
SUPABASE_URL = "https://sotvsjzujjmwylmnkywv.supabase.co"
SUPABASE_KEY = "sb_publishable_NKG06zGEOCh4w6YpaCDKYg_lx78L--Z"
# ----------------------------------------------------

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

LISTAS_RIESGO_ALTO = [
    "AURA030215HSRGMDA5"
]

def guardar_en_base_de_datos(empresa, documento, curp, estatus, nivel_riesgo):
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
            "accion": "Revisión manual obligatoria y debida diligencia reforzada."
        }
    else:
        return {
            "estatus": "APROBADO: Sin Coincidencias de Riesgo",
            "nivel_riesgo": "BAJO",
            "accion": "Expediente simplificado bajo diligencia estándar."
        }

def comparar_domicilios(texto_ine, texto_comprobante):
    # Extraemos palabras clave largas (nombres de calles, colonias, municipios)
    palabras_ine = set(re.findall(r'\b[A-Z]{4,}\b', texto_ine.upper()))
    palabras_comp = set(re.findall(r'\b[A-Z]{4,}\b', texto_comprobante.upper()))
    
    # Filtramos palabras genéricas que no aportan al cruce
    ignoradas = {"CALLE", "COLONIA", "ESTADO", "MEXICO", "NUMERO", "EXTERIOR", "INTERIOR", "FECHA", "NOMBRE", "DOMICILIO", "REPUBLICA", "ELECTORAL", "INSTITUTO", "NACIONAL"}
    palabras_ine = palabras_ine - ignoradas
    palabras_comp = palabras_comp - ignoradas

    # Buscamos coincidencias entre ambos documentos
    coincidencias = palabras_ine.intersection(palabras_comp)
    
    # Si hay al menos 2 palabras clave idénticas, asumimos que es el mismo domicilio
    if len(coincidencias) >= 2:
        return True, coincidencias
    return False, coincidencias

def procesar_expediente_completo(ruta_ine, ruta_comprobante, empresa):
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # 1. Lectura de la INE
    imagen_ine = cv2.imread(ruta_ine)
    if imagen_ine is None:
        return {"error": "No se pudo cargar la imagen de la INE."}
    
    texto_ine = pytesseract.image_to_string(imagen_ine)

    patron_etiqueta = r'CURP[\s\S]*?([A-Z0-9]{18})'
    busqueda = re.search(patron_etiqueta, texto_ine)

    if not busqueda:
        return {"error": "No se encontró la CURP en el documento INE."}

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
    estatus_final = resultado_riesgo["estatus"]
    nivel_riesgo_final = resultado_riesgo["nivel_riesgo"]
    accion_final = resultado_riesgo["accion"]

    # 2. Lectura del Comprobante (si se proporcionó uno)
    if ruta_comprobante:
        imagen_comp = cv2.imread(ruta_comprobante)
        if imagen_comp is not None:
            texto_comp = pytesseract.image_to_string(imagen_comp)
            coincide, coincidencias = comparar_domicilios(texto_ine, texto_comp)
            
            if coincide:
                estatus_final += " | Domicilio validado exitosamente"
            else:
                estatus_final += " | ALERTA: Domicilios no coinciden"
                if nivel_riesgo_final == "BAJO":
                    nivel_riesgo_final = "MEDIO"
                accion_final += " Solicitar Carta Declaratoria de Domicilio al cliente."
    
    guardar_en_base_de_datos(empresa, "INE + Comprobante", curp_perfecta, estatus_final, nivel_riesgo_final)

    return {
        "documento": "INE + Comprobante",
        "curp": curp_perfecta,
        "estatus": estatus_final,
        "nivel_riesgo": nivel_riesgo_final,
        "accion": accion_final
    }
