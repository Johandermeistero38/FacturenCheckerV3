import streamlit as st
import pdfplumber

st.title("FacturenCheckerV3")

st.write("Stap 2: PDF uploaden en tekst uitlezen")

uploaded_file = st.file_uploader(
    "Upload een factuur (PDF)",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success("PDF succesvol geüpload")

    all_text = ""

    with pdfplumber.open(uploaded_file) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                all_text += f"\n--- PAGINA {i + 1} ---\n"
                all_text += page_text

    st.subheader("Uitlezen resultaat (ruwe tekst)")
    st.text(all_text)
