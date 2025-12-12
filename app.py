import streamlit as st
import pdfplumber
import re
import math
import pandas as pd

st.title("FacturenCheckerV3")

st.write("Stap 7: Cosa prijsmatrix matchen")

# Uploads
uploaded_pdf = st.file_uploader("Upload een factuur (PDF)", type=["pdf"])
uploaded_matrix = st.file_uploader("Upload Cosa prijsmatrix (Excel)", type=["xlsx"])

LINE_REGEX = re.compile(
    r"GORDIJN Curtain\s+"
    r"(?P<breedte>\d+)\s*x\s*(?P<hoogte>\d+)\s*mm,\s*"
    r"(?P<stof>Cosa\s+\d+\s+\w+)\s+"
    r"\d+\s+"
    r"(?P<prijs>\d+,\d+)"
)

def prijs_cm_van_mm(mm: int) -> int:
    cm = mm / 10
    cm_naar_boven = math.ceil(cm)
    return math.ceil(cm_naar_boven / 10) * 10

def normaliseer_stof(stof_raw: str) -> str:
    return "Cosa" if stof_raw.lower().startswith("cosa") else stof_raw

if uploaded_pdf and uploaded_matrix:
    st.success("PDF en matrix succesvol geüpload")

    # Matrix inlezen
    sheet_name = st.selectbox(
        "Kies Cosa matrix sheet",
        options=pd.ExcelFile(uploaded_matrix).sheet_names
    )

    matrix_df = pd.read_excel(uploaded_matrix, sheet_name=sheet_name)

    # Eerste kolom = hoogte
    matrix_df = matrix_df.rename(columns={matrix_df.columns[0]: "Hoogte"}).set_index("Hoogte")

    rows = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                if "GORDIJN Curtain" in line and "Cosa" in line:
                    match = LINE_REGEX.search(line)
                    if match:
                        breedte_mm = int(match.group("breedte"))
                        hoogte_mm = int(match.group("hoogte"))

                        breedte_cm = prijs_cm_van_mm(breedte_mm)
                        hoogte_cm = prijs_cm_van_mm(hoogte_mm)

                        matrix_prijs = None
                        if hoogte_cm in matrix_df.index and breedte_cm in matrix_df.columns:
                            matrix_prijs = matrix_df.loc[hoogte_cm, breedte_cm]

                        rows.append({
                            "Originele regel": line,
                            "Breedte prijs (cm)": breedte_cm,
                            "Hoogte prijs (cm)": hoogte_cm,
                            "Factuurprijs": float(match.group("prijs").replace(",", ".")),
                            "Matrixprijs": matrix_prijs
                        })

    st.subheader("Cosa-gordijnen met matrixprijs")
    st.table(rows)
