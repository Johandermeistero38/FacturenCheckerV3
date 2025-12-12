import streamlit as st
import pdfplumber
import re
import math
import pandas as pd

st.title("FacturenCheckerV3")

st.write("Stap 7: Cosa prijsmatrix matchen (alle plooien)")

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

if uploaded_pdf and uploaded_matrix:
    st.success("PDF en matrix succesvol geüpload")

    excel = pd.ExcelFile(uploaded_matrix)
    sheets = excel.sheet_names  # alle plooien

    # Alle matrices inladen
    matrices = {}
    for sheet in sheets:
        df = pd.read_excel(uploaded_matrix, sheet_name=sheet)
        df = df.rename(columns={df.columns[0]: "Hoogte"}).set_index("Hoogte")
        matrices[sheet] = df

    rows = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                if "GORDIJN Curtain" in line and "Cosa" in line:
                    match = LINE_REGEX.search(line)
                    if not match:
                        continue

                    breedte_cm = prijs_cm_van_mm(int(match.group("breedte")))
                    hoogte_cm = prijs_cm_van_mm(int(match.group("hoogte")))
                    factuurprijs = float(match.group("prijs").replace(",", "."))

                    row = {
                        "Originele regel": line,
                        "Breedte prijs (cm)": breedte_cm,
                        "Hoogte prijs (cm)": hoogte_cm,
                        "Factuurprijs": round(factuurprijs, 2),
                    }

                    # Voor elke plooi een prijs ophalen
                    for sheet, df in matrices.items():
                        prijs = None
                        if hoogte_cm in df.index and breedte_cm in df.columns:
                            prijs = df.loc[hoogte_cm, breedte_cm]
                            if pd.notna(prijs):
                                prijs = round(float(prijs), 2)

                        row[f"Matrixprijs – {sheet}"] = prijs

                    rows.append(row)

    st.subheader("Cosa-gordijnen – alle plooien")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
