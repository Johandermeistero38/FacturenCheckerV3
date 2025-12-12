import streamlit as st
import pdfplumber

st.title("FacturenCheckerV3")

st.write("Stap 3: Alleen Cosa-gordijnregels filteren")

uploaded_file = st.file_uploader(
    "Upload een factuur (PDF)",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success("PDF succesvol geüpload")

    cosa_lines = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                # Alleen regels met GORDIJN Curtain én Cosa
                if "GORDIJN Curtain" in line and "Cosa" in line:
                    cosa_lines.append(line)

    st.subheader("Gevonden Cosa-gordijnregels")

    if cosa_lines:
        for l in cosa_lines:
            st.text(l)
    else:
        st.warning("Geen Cosa-gordijnregels gevonden.")
