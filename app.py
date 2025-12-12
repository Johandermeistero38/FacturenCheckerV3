import streamlit as st
import pdfplumber
import re
import math

st.title("FacturenCheckerV3")

st.write("Stap 6: Stof normaliseren (Cosa)")

uploaded_file = st.file_uploader(
    "Upload een factuur (PDF)",
    type=["pdf"]
)

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
    # Jouw business rule
    if stof_raw.lower().startswith("cosa"):
        return "Cosa"
    return stof_raw

if uploaded_file is not None:
    st.success("PDF succesvol geüpload")

    rows = []

    with pdfplumber.open(uploaded_file) as pdf:
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
                        stof_raw = match.group("stof")

                        rows.append({
                            "Originele regel": line,
                            "Stof (raw)": stof_raw,
                            "Stofgroep": normaliseer_stof(stof_raw),
                            "Breedte prijs (cm)": prijs_cm_van_mm(breedte_mm),
                            "Hoogte prijs (cm)": prijs_cm_van_mm(hoogte_mm),
                            "Factuurprijs": float(match.group("prijs").replace(",", "."))
                        })

    st.subheader("Cosa-gordijnregels (genormaliseerd)")
    st.table(rows)
