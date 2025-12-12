import streamlit as st
import pandas as pd
import pdfplumber
import re
import math
from pathlib import Path
from io import BytesIO

# =========================
# App setup
# =========================
st.set_page_config(page_title="Raamdecoratie.com Facturen Checker", layout="wide")

st.title("Raamdecoratie.com – Facturen checker")

# =========================
# Stap 1 – Leverancier
# =========================
st.header("Stap 1: Kies leverancier")
leverancier = st.selectbox(
    "Leverancier",
    ["TOPPOINT"],  # later uitbreidbaar
)

# =========================
# Stap 2 – Upload factuur
# =========================
st.header("Stap 2: Upload je factuur")
uploaded_pdf = st.file_uploader(
    "Upload factuur (PDF)",
    type=["pdf"]
)

# =========================
# Config
# =========================
BASE_DIR = Path("suppliers/toppoint/gordijnen")

LINE_REGEX = re.compile(
    r"GORDIJN Curtain\s+"
    r"(?P<breedte>\d+)\s*x\s*(?P<hoogte>\d+)\s*mm,?\s*"
    r"(?P<stof>.+?)\s+\d+\s+(?P<prijs>\d+,\d+)"
)

PLOOIEN = ["Enkele plooi", "Dubbele plooi", "Wave plooi", "Ring"]

# =========================
# Helpers
# =========================
def prijs_cm_van_mm(mm: int) -> int:
    cm = mm / 10
    return math.ceil(cm / 10) * 10


def normaliseer_stof(tekst: str) -> str:
    tekst = tekst.lower()
    tekst = tekst.replace("inbetween", "").replace("in between", "")
    tekst = re.split(r"\d", tekst)[0]
    return tekst.strip()


def laad_matrix_bestanden():
    matrices = {}
    for file in BASE_DIR.glob("*price matrix.xlsx"):
        naam = file.stem.replace(" price matrix", "").lower()
        matrices[naam] = file
    return matrices


def laad_matrix_sheets(matrix_path: Path):
    excel = pd.ExcelFile(matrix_path)
    sheets = {}

    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)
        df = df.rename(columns={df.columns[0]: "Hoogte"}).set_index("Hoogte")
        sheets[sheet] = df

    return sheets


# =========================
# Stap 3 – Verwerken
# =========================
result_df = None

if leverancier == "TOPPOINT" and uploaded_pdf:
    st.header("Stap 3: Verwerken factuur")

    progress = st.progress(0)
    status_text = st.empty()

    matrix_files = laad_matrix_bestanden()
    rows = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        total_pages = len(pdf.pages)
        gevonden_regels = 0

        for i, page in enumerate(pdf.pages):
            status_text.info(f"Verwerken pagina {i + 1} van {total_pages}…")
            progress.progress((i + 1) / total_pages * 0.7)

            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                match = LINE_REGEX.search(line)
                if not match:
                    continue

                gevonden_regels += 1

                breedte_mm = int(match.group("breedte"))
                hoogte_mm = int(match.group("hoogte"))
                factuur_prijs = round(
                    float(match.group("prijs").replace(",", ".")), 2
                )

                stof_raw = match.group("stof")
                stof_norm = normaliseer_stof(stof_raw)

                matrix_path = matrix_files.get(stof_norm)
                if not matrix_path:
                    continue

                matrices = laad_matrix_sheets(matrix_path)

                b_cm = prijs_cm_van_mm(breedte_mm)
                h_cm = prijs_cm_van_mm(hoogte_mm)

                plooi_prijzen = {}
                plooi_verschillen = {}

                for plooi in PLOOIEN:
                    df = matrices.get(plooi)
                    if df is None or h_cm not in df.index or b_cm not in df.columns:
                        plooi_prijzen[plooi] = None
                        plooi_verschillen[plooi] = None
                        continue

                    prijs = round(float(df.loc[h_cm, b_cm]), 2)
                    verschil = round(factuur_prijs - prijs, 2)

                    plooi_prijzen[plooi] = prijs
                    plooi_verschillen[plooi] = verschil

                beste_plooi = None
                beste_verschil = None

                for plooi, verschil in plooi_verschillen.items():
                    if verschil is None:
                        continue
                    if beste_verschil is None or abs(verschil) < abs(beste_verschil):
                        beste_plooi = plooi
                        beste_verschil = verschil

                rows.append({
                    "Originele regel": line,
                    "Stof": stof_norm.capitalize(),
                    "Matrix": matrix_path.name,
                    "Breedte prijs (cm)": b_cm,
                    "Hoogte prijs (cm)": h_cm,
                    "Enkele plooi (€)": plooi_prijzen["Enkele plooi"],
                    "Dubbele plooi (€)": plooi_prijzen["Dubbele plooi"],
                    "Wave plooi (€)": plooi_prijzen["Wave plooi"],
                    "Ring (€)": plooi_prijzen["Ring"],
                    "Gekozen plooi": beste_plooi,
                    "Factuurprijs (€)": factuur_prijs,
                    "Verschil (€)": beste_verschil,
                })

    progress.progress(1.0)
    status_text.success(f"Klaar! {gevonden_regels} regels gevonden.")
    result_df = pd.DataFrame(rows)

# =========================
# Resultaat (ingeklapt)
# =========================
if result_df is not None and not result_df.empty:
    with st.expander("📊 Prijscontrole resultaat bekijken"):
        st.dataframe(result_df, use_container_width=True)

# =========================
# Stap 4 – Exporteren
# =========================
if result_df is not None and not result_df.empty:
    st.header("Stap 4: Exporteren")

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
            "⬇ Download CSV",
            data=csv,
            file_name=f"{export_name}.csv",
            mime="text/csv"
        )
    else:
        buffer = BytesIO()
        result_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "⬇ Download Excel",
            data=buffer,
            file_name=f"{export_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
