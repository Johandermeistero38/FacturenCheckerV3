import streamlit as st
import pdfplumber
import re

st.title("FacturenCheckerV3")

st.write("Stap 4: Cosa-regels ontleden")

uploaded_file = st.file_uploader(
    "Upload een factuur (PDF)",
    type=["pdf"]
)

# Regex om onderdelen uit de regel te halen
LINE_REGEX = re.compile(
    r"GORDIJN Curtain\s+"
    r"(?P<breedte>\d+)\s*x\s*(?P<hoogte>\d+)\s*mm,\s*"
    r"(?P<stof>Cosa\s+\d+\s+\w+)\s+"
    r"\d+\s+"
    r"(?P<prijs>\d+,\d+)"
)

if uploaded_file is not None:
    st.success("PDF succesvol geüpload")

    parsed_rows = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                if "GORDIJN Curtain" in line and "Cosa" in line:
                    match = LINE_REGEX.search(line)
                    if match:
                        parsed_rows.append({
                            "Originele regel": line,
                            "Breedte (mm)": int(match.group("breedte")),
                            "Hoogte (mm)": int(match.group("hoogte")),
                            "Stof (raw)": match.group("stof"),
                            "Factuurprijs": float(match.group("prijs").replace(",", "."))
                        })

    st.subheader("Ontlede Cosa-gordijnregels")

    if parsed_rows:
        st.table(parsed_rows)
    else:
        st.warning("Geen regels succesvol ontleed.")
