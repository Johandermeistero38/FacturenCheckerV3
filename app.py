import streamlit as st
import pandas as pd
import pdfplumber
import re
import math
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title="FacturenCheckerV3", layout="wide")
st.title("FacturenCheckerV3")
st.subheader("Stap A.6 – TOPPOINT volledige prijscontrole")

# -------------------------
# Config
# -------------------------
BASE_DIR = Path("suppliers/toppoint/gordijnen")

PLOOIEN = [
    "Enkele plooi",
    "Dubbele plooi",
    "Wave plooi",
    "Ring"
]

LINE_REGEX = re.compile(
    r"GORDIJN Curtain\s+"
    r"(?P<breedte>\d+)\s*x\s*(?P<hoogte>\d+)\s*mm,?\s*"
    r"(?P<stof>.+?)\s+\d+\s+(?P<prijs>\d+,\d+)"
)

# -------------------------
# Helpers
# -------------------------
def prijs_cm_van_mm(mm: int) -> int:
    cm = mm / 10
    return math.ceil(cm / 10) * 10


def normaliseer_stof(tekst: str) -> str:
    """
    Stof = alles vóór het eerste cijfer
    """
    tekst = tekst.lower()
    tekst = re.split(r"\d", tekst)[0]
    return tekst.strip()


def status_icon(verschil: float) -> str:
    if abs(verschil) < 0.01:
        return "✅"
    elif verschil > 0:
        return "🔴"
    else:
        return "🟢"


def laad_matrices():
    matrices = {}
    for file in BASE_DIR.glob("*price matrix.xlsx"):
        naam = file.stem.replace(" price matrix", "").lower()
        matrices[naam] = file
    return matrices


def laad_matrix_bestanden(matrix_path: Path):
    excel = pd.ExcelFile(matrix_path)
    matrices = {}

    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)
        df = df.rename(columns={df.columns[0]: "Hoogte"}).set_index("Hoogte")
        matrices[sheet] = df

    return matrices


# -------------------------
# UI
# -------------------------
leverancier = st.selectbox("Kies leverancier", ["TOPPOINT"])

uploaded_pdf = st.file_uploader("Upload factuur (PDF)", type=["pdf"])

if leverancier == "TOPPOINT" and uploaded_pdf:
    matrix_bestanden = laad_matrices()

    rows = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                match = LINE_REGEX.search(line)
                if not match:
                    continue

                breedte_mm = int(match.group("breedte"))
                hoogte_mm = int(match.group("hoogte"))
                factuur_prijs = float(match.group("prijs").replace(",", "."))

                stof_raw = match.group("stof")
                stof_norm = normaliseer_stof(stof_raw)

                matrix_file = matrix_bestanden.get(stof_norm)

                if not matrix_file:
                    rows.append({
                        "Originele regel": line,
                        "Stof": stof_raw,
                        "Matrix gevonden": False,
                        "Status": "❓"
                    })
                    continue

                matrices = laad_matrix_bestanden(matrix_file)

                b_cm = prijs_cm_van_mm(breedte_mm)
                h_cm = prijs_cm_van_mm(hoogte_mm)

                beste_plooi = None
                beste_prijs = None
                beste_verschil = None

                for plooi, df in matrices.items():
                    if h_cm not in df.index or b_cm not in df.columns:
                        continue

                    matrix_prijs = float(df.loc[h_cm, b_cm])
                    verschil = round(factuur_prijs - matrix_prijs, 2)

                    if beste_verschil is None or abs(verschil) < abs(beste_verschil):
                        beste_plooi = plooi
                        beste_prijs = round(matrix_prijs, 2)
                        beste_verschil = verschil

                rows.append({
                    "Originele regel": line,
                    "Stof": stof_raw,
                    "Matrix": matrix_file.name,
                    "Breedte prijs (cm)": b_cm,
                    "Hoogte prijs (cm)": h_cm,
                    "Gekozen plooi": beste_plooi,
                    "Factuurprijs (€)": round(factuur_prijs, 2),
                    "Matrixprijs (€)": beste_prijs,
                    "Verschil (€)": beste_verschil,
                    "Status": status_icon(beste_verschil)
                })

    # -------------------------
    # Resultaat
    # -------------------------
    st.subheader("TOPPOINT – prijscontrole resultaat")
    result_df = pd.DataFrame(rows)
    st.dataframe(result_df, use_container_width=True)

    # -------------------------
    # Export
    # -------------------------
    if not result_df.empty:
        st.divider()
        st.subheader("Exporteren")

        export_name = st.text_input(
            "Bestandsnaam (zonder extensie)",
            value="toppoint_prijscontrole"
        )

        export_type = st.selectbox(
            "Export formaat",
            ["Excel (.xlsx)", "CSV (.csv)"]
        )

        if export_type == "CSV (.csv)":
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"{export_name}.csv",
                mime="text/csv"
            )
        else:
            buffer = BytesIO()
            result_df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                "Download Excel",
                data=buffer,
                file_name=f"{export_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
