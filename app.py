import streamlit as st
import pandas as pd
import re
import unicodedata

# ----------------- Funciones auxiliares ------------------

def normalizar(s: str) -> str:
    """Convierte texto a minúsculas y elimina acentos/tildes."""
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()

def construir_patron(frase: str) -> re.Pattern:
    """
    Crea una expresión regular que:
    - tolere saltos de línea entre palabras
    - busque palabras completas (evita coincidencias parciales)
    """
    expr = re.escape(frase.strip())
    expr = expr.replace(r'\ ', r'\s+')
    return re.compile(rf'\b{expr}\b', re.IGNORECASE | re.MULTILINE)

def tiene_coincidencia(texto: str, patrones: dict) -> list[str]:
    """Devuelve la lista de frases que aparecen en el texto normalizado."""
    return [frase for frase, patron in patrones.items() if patron.search(texto)]

# ----------------- Streamlit App -------------------------

st.set_page_config(page_title="Buscador ICC Adenda 1 DMH", layout="wide")
st.title("🔍 Buscador de Palabras Clave ICC Adenda DMH")

# Ruta al archivo CSV
archivo = r'C:\Users\GabrielRaggio\OneDrive - SLR Consulting\Documentos\Automatización PAC\DMH\excels obs\observaciones_adenda_plataforma.csv'

# Inputs y estados
if 'buscar' not in st.session_state:
    st.session_state['buscar'] = False
if 'resultados_df' not in st.session_state:
    st.session_state['resultados_df'] = pd.DataFrame()

# Entrada de palabras clave
palabras_input = st.text_area(
    "Escribe las palabras o frases clave separadas por coma",
    "arsenico, plomo, metales"
)
palabras_clave = [p.strip() for p in palabras_input.split(",") if p.strip()]
palabras_norm = [normalizar(p) for p in palabras_clave]
patrones = {p: construir_patron(normalizar(p)) for p in palabras_clave}

# Acción de búsqueda
if st.button("Buscar"):
    st.session_state['buscar'] = True

    df = pd.read_csv(archivo)
    df["texto_norm"] = df["texto_observacion"].astype(str).apply(normalizar)

    # Detectar coincidencias
    df["coincidencias"] = df["texto_norm"].apply(lambda txt: tiene_coincidencia(txt, patrones))
    df_filtrado = df[df["coincidencias"].str.len() > 0].copy()

    # Crear campo combinaciones únicas para filtrar
    df_filtrado["Palabras Clave (combinadas)"] = df_filtrado["coincidencias"].apply(
        lambda l: ", ".join(sorted(set(l)))
    )

    st.session_state['resultados_df'] = df_filtrado

# Mostrar resultados
if st.session_state['buscar']:
    df_filtrado = st.session_state['resultados_df']

    if df_filtrado.empty:
        st.warning("No se encontraron coincidencias.")
    else:
        combinaciones_unicas = sorted(df_filtrado["Palabras Clave (combinadas)"].unique())
        seleccion = st.selectbox("Filtrar por combinación de palabras clave", ["Todas"] + combinaciones_unicas)

        if seleccion != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Palabras Clave (combinadas)"] == seleccion]

        # Explota por coincidencia individual para mostrar
        df_resultados = (
            df_filtrado
            .explode("coincidencias")
            .rename(columns={
                "coincidencias": "Palabra Clave",
                "nombre_archivo": "observacion_id"
            })
            [["Palabras Clave (combinadas)", "observacion_id"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        st.success(f"Se encontraron {len(df_resultados)} coincidencias.")
        st.dataframe(df_resultados)
