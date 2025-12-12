import streamlit as st
import pdfplumber
import pandas as pd
import os
import re

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("FacturenCheckerV3")
st.write("Stap A.5 – TOPPOINT stof → matrix koppeling")

# -------------------------------------------------
# Leverancier
# -------------------------------------------------
supplier = st.selectbox("Kies leverancier", ["TOPPOINT"])

# -------------------------------------------------
# Matrixen laden (TOPPOINT)
# -------------------------------------------------
MATRIX_DIR = "suppliers/toppoint/gordijnen"
matrices = {}

if supplier == "TOPPOINT":
    for filename in os.listdir(MATRIX_DIR):
        if filename.lower().endswith(".xlsx"):
            key = (
                filename
                .lower()
                .replace(" price matrix.xlsx", "")
                .strip()
            )
            matrices[key] = filename

st.subheader("Beschikbare TOPPOINT matrices")
st.write(sorted(matrices.keys()))

# -------------------------------------------------
# Stof normaliseren (JOUW REGEL)
# -------------------------------------------------
def normaliseer_stof_toppoint(stof_raw: str) -> str:
    """
    Stofnaam = alles vóór het eerste cijfer
    """
    stof = stof_raw.lower().strip()

    # verwijder 'inbetween'
    stof = stof.replace("inbetween", "").strip()

    # alles vóór eerste cijfer
    parts = re.split(r"\d", stof, maxsplit=1)
    stof_naam = parts[0].strip()

    return stof_naam

# -------------------------------------------------
# Factuur upload
# -------------------------------------------------
uploaded_pdf = st.file_uploader("Upload factuur (PDF)", type=["pdf"])

if uploaded_pdf:
    rows = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                if "GORDIJN Curtain" not in line:
                    continue

                # haal stofdeel uit regel
                match = re.search(r",\s*(.+?)\s+\d+,\d+", line)
                if not match:
                    continue

                stof_raw = match.group(1)
                stof_norm = normaliseer_stof_toppoint(stof_raw)

                rows.append({
                    "Originele regel": line,
                    "Stof (factuur)": stof_raw,
                    "Stof (genormaliseerd)": stof_norm,
                    "Matrix gevonden": stof_norm in matrices,
                    "Matrix bestand": matrices.get(stof_norm),
                })

    st.subheader("Factuurregels → matrix koppeling")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
