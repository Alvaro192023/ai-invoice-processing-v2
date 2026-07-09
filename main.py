"""Pipeline principal: extrae facturas PDF, las estructura con IA y las carga en SQLite.

Uso:
    1. Coloca los PDFs en subcarpetas dentro de `facturas/`.
    2. Define tu clave en `.env` (ver `.env.example`).
    3. Ejecuta: `python main.py`
"""
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

import funciones

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

CARPETA_FACTURAS = Path("facturas")
BASE_DATOS = "sqlite:///facturas.db"


def procesar_facturas(carpeta: Path) -> pd.DataFrame:
    """Recorre los PDFs de `carpeta` (y subcarpetas) y devuelve un DataFrame con las facturas."""
    registros = []
    for ruta_pdf in sorted(carpeta.rglob("*.pdf")):
        logger.info("Procesando factura: %s", ruta_pdf)
        texto = funciones.extraer_texto_pdf(str(ruta_pdf))
        csv_estructurado = funciones.estructurar_texto(texto)
        if csv_estructurado.lower() == "error":
            logger.warning("No se pudo extraer datos de %s", ruta_pdf)
            continue
        registros.append(funciones.csv_a_dataframe(csv_estructurado))

    if not registros:
        return pd.DataFrame(columns=funciones.COLUMNS)
    return pd.concat(registros, ignore_index=True)


def guardar_en_sqlite(df: pd.DataFrame, conexion: str = BASE_DATOS) -> None:
    """Guarda el DataFrame en la tabla `facturas` de la base SQLite."""
    engine = create_engine(conexion)
    df.to_sql("facturas", engine, if_exists="append", index=False)
    engine.dispose()


def main() -> None:
    df = procesar_facturas(CARPETA_FACTURAS)
    logger.info("Facturas procesadas: %d", len(df))
    guardar_en_sqlite(df)
    logger.info("Datos guardados en facturas.db")


if __name__ == "__main__":
    main()
