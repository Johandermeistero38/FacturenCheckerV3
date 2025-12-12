import streamlit as st
import pdfplumber
import re
import math
import pandas as pd

st.title("FacturenCheckerV3")
st.write("Prijscontrole Cosa – automatische plooi-keuze")

uploaded_pdf = st.file_uploader("Upload een factuur (PDF)", type=["pdf"])
uploaded_matrix = st.file_uploader("Upload Cosa prijsmatrix (Excel)", type=["xlsx"])

TOLERANTIE = 0.50  # euro

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

def status_icoon(verschil):
    if verschil is None:
        return "⚪"
    return "🟢" if abs(verschil) <= TOLERANTIE else "🔴"

if uploaded_pdf and uploaded_matrix:
    st.success("PDF en matrix succesvol geüpload")

    # Alle matrix sheets inlezen
    excel = pd.ExcelFile(uploaded_matrix)
    matrices = {}

    for sheet in excel.sheet_names:
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
                if "GORDIJN Curtain" not in line or "Cosa" not in line:
                    continue

                match = LINE_REGEX.search(line)
                if not match:
                    continue

                breedte_cm = prijs_cm_van_mm(int(match.group("breedte")))
                hoogte_cm = prijs_cm_van_mm(int(match.group("hoogte")))
                factuurprijs = round(float(match.group("prijs").replace(",", ".")), 2)

                beste_plooi = None
                beste_matrixprijs = None
                beste_verschil = None

                for plooi, df in matrices.items():
                    if hoogte_cm in df.index and breedte_cm in df.columns:
                        prijs = df.loc[hoogte_cm, breedte_cm]
                        if pd.notna(prijs):
                            matrixprijs = round(float(prijs), 2)
                            verschil = round(factuurprijs - matrixprijs, 2)

                            if (
                                beste_verschil is None
                                or abs(verschil) < abs(beste_verschil)
                            ):
                                beste_plooi = plooi
                                beste_matrixprijs = matrixprijs
                                beste_verschil = verschil

                rows.append({
                    "Originele regel": line,
                    "Breedte prijs (cm)": breedte_cm,
                    "Hoogte prijs (cm)": hoogte_cm,
                    "Factuurprijs (€)": factuurprijs,
                    "Gekozen plooi": beste_plooi,
                    "Matrixprijs (€)": beste_matrixprijs,
                    "Verschil (€)": beste_verschil,
                    "Status": status_icoon(beste_verschil),
                })

    st.subheader("Controle-resultaat Cosa gordijnen")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
