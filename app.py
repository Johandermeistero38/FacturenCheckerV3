import streamlit as st
import pdfplumber
import pandas as pd
import os
import re
import math

# -------------------------------------------------
# Config
# -------------------------------------------------
MATRIX_DIR = "suppliers/toppoint/gordijnen"
TOLERANTIE = 0.50  # euro

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("FacturenCheckerV3")
st.write("Stap A.6 – TOPPOINT volledige prijscontrole")

supplier = st.selectbox("Kies leverancier", ["TOPPOINT"])

# -------------------------------------------------
# Helper functies
# -------------------------------------------------
def normaliseer_stof_toppoint(stof_raw: str) -> str:
    stof = stof_raw.lower().strip()
    stof = stof.replace("inbetween", "").strip()
    parts = re.split(r"\d", stof, maxsplit=1)
    return parts[0].strip()

def afronden_mm_naar_prijs_cm(mm: int) -> int:
    cm = mm / 10
    return math.ceil(cm / 10) * 10

def status_icoon(verschil):
    if verschil is None:
        return "⚪"
    return "🟢" if abs(verschil) <= TOLERANTIE else "🔴"

# -------------------------------------------------
# Matrixen laden
# -------------------------------------------------
matrices = {}

for filename in os.listdir(MATRIX_DIR):
    if filename.lower().endswith(".xlsx"):
        key = filename.lower().replace(" price matrix.xlsx", "").strip()
        matrices[key] = os.path.join(MATRIX_DIR, filename)


# -------------------------------------------------
# Factuur upload
# -------------------------------------------------
uploaded_pdf = st.file_uploader("Upload factuur (PDF)", type=["pdf"])

LINE_REGEX = re.compile(
    r"GORDIJN Curtain\s+"
    r"(?P<breedte>\d+)\s*x\s*(?P<hoogte>\d+)\s*mm,\s*"
    r"(?P<stof>.+?)\s+"
    r"\d+\s+"
    r"(?P<prijs>\d+,\d+)"
)

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

                match = LINE_REGEX.search(line)
                if not match:
                    continue

                breedte_mm = int(match.group("breedte"))
                hoogte_mm = int(match.group("hoogte"))
                stof_raw = match.group("stof")
                factuurprijs = float(match.group("prijs").replace(",", "."))

                stof_norm = normaliseer_stof_toppoint(stof_raw)
                matrix_path = matrices.get(stof_norm)

                breedte_cm = afronden_mm_naar_prijs_cm(breedte_mm)
                hoogte_cm = afronden_mm_naar_prijs_cm(hoogte_mm)

                beste_plooi = None
                beste_matrixprijs = None
                beste_verschil = None

                if matrix_path:
                    excel = pd.ExcelFile(matrix_path)

                    for sheet in excel.sheet_names:
                        df = pd.read_excel(excel, sheet_name=sheet)
                        df = df.rename(columns={df.columns[0]: "Hoogte"}).set_index("Hoogte")

                        if hoogte_cm in df.index and breedte_cm in df.columns:
                            prijs = df.loc[hoogte_cm, breedte_cm]
                            if pd.notna(prijs):
                                matrixprijs = round(float(prijs), 2)
                                verschil = round(factuurprijs - matrixprijs, 2)

                                if (
                                    beste_verschil is None
                                    or abs(verschil) < abs(beste_verschil)
                                ):
                                    beste_plooi = sheet
                                    beste_matrixprijs = matrixprijs
                                    beste_verschil = verschil

                rows.append({
                    "Originele regel": line,
                    "Stof": stof_norm,
                    "Breedte prijs (cm)": breedte_cm,
                    "Hoogte prijs (cm)": hoogte_cm,
                    "Factuurprijs (€)": round(factuurprijs, 2),
                    "Gekozen plooi": beste_plooi,
                    "Matrixprijs (€)": beste_matrixprijs,
                    "Verschil (€)": beste_verschil,
                    "Status": status_icoon(beste_verschil),
                })

    st.subheader("TOPPOINT – prijscontrole resultaat")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
