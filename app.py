import streamlit as st
import pdfplumber
import pandas as pd
import os
import re

st.title("FacturenCheckerV3")
st.write("Stap A.5 – Factuurstof koppelen aan TOPPOINT matrixen")

# ---------------------------
# Leverancier
# ---------------------------
supplier = st.selectbox("Kies leverancier", ["TOPPOINT"])

# ---------------------------
# Matrixen laden
# ---------------------------
MATRIX_DIR = "suppliers/toppoint/gordijnen"
matrices = {}

for filename in os.listdir(MATRIX_DIR):
    if filename.lower().endswith(".xlsx"):
        key = filename.lower().replace(" price matrix.xlsx", "").strip()
        matrices[key] = filename

# ---------------------------
# Stof normaliseren
# ---------------------------
def normaliseer_stof_toppoint(stof_raw: str) -> str:
    stof = stof_raw.lower()
    stof = stof.replace("inbetween", "")
    stof = "".join(c for c in stof if not c.isdigit())
    stof = stof.replace(",", " ").strip()
    woorden = stof.split()
    if len(woorden) >= 2:
        return " ".join(woorden[:2])
    elif woorden:
        return woorden[0]
    return ""

# ---------------------------
# Factuur upload
# ---------------------------
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

                # probeer stofdeel te pakken
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

    st.subheader("Factuurstof → matrix koppeling")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
