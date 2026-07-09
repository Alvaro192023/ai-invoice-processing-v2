"""Funciones de extracción y estructuración de facturas.

Extrae texto de PDFs (PyMuPDF), lo estructura con la API de OpenAI según el
prompt de `prompt.py` y lo convierte en un DataFrame de pandas.
"""
import os
from io import StringIO

import fitz  # PyMuPDF
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from prompt import prompt

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError(
        "Falta OPENAI_API_KEY. Copia .env.example a .env y define tu clave."
    )

client = OpenAI(api_key=_api_key)

COLUMNS = ["fecha_factura", "proveedor", "concepto", "importe", "moneda"]


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae todo el texto de un PDF de factura."""
    with fitz.open(ruta_pdf) as doc:
        return "\n".join(page.get_text("text") for page in doc)


def estructurar_texto(texto: str) -> str:
    """Envía el texto de la factura a OpenAI y devuelve un CSV (`;`) estructurado.

    Devuelve la palabra 'error' si el modelo no pudo extraer datos.
    """
    respuesta = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en extraccion de datos de facturas. Devuelve solo "
                    "el CSV sin explicaciones. Si no puedes extraer datos, devuelve "
                    "exactamente la palabra 'error' sin comillas."
                ),
            },
            {
                "role": "user",
                "content": f"{prompt}\nEste es el texto a parsear:\n{texto}",
            },
        ],
    )
    return respuesta.choices[0].message.content.strip()


def csv_a_dataframe(csv_texto: str) -> pd.DataFrame:
    """Convierte el CSV devuelto por el modelo en un DataFrame, con `importe` numérico."""
    df = pd.read_csv(StringIO(csv_texto), delimiter=";", dtype={c: str for c in COLUMNS})
    df["importe"] = pd.to_numeric(df["importe"].str.replace(",", "."), errors="coerce")
    return df
