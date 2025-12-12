import streamlit as st
import pandas as pd
import os

st.title("FacturenCheckerV3")
st.write("Stap A.4 – Leverancier & matrixen laden")

# ---------------------------
# Leverancier kiezen
# ---------------------------
supplier = st.selectbox(
    "Kies leverancier",
    ["TOPPOINT"]
)

if supplier == "TOPPOINT":
    MATRIX_DIR = "suppliers/toppoint/gordijnen"

    if not os.path.exists(MATRIX_DIR):
        st.error("Matrix map niet gevonden")
        st.stop()

    matrices = {}

    for filename in os.listdir(MATRIX_DIR):
        if not filename.lower().endswith(".xlsx"):
            continue

        # Maak stof-sleutel uit bestandsnaam
        stof_key = (
            filename
            .lower()
            .replace(" price matrix.xlsx", "")
            .strip()
        )

        path = os.path.join(MATRIX_DIR, filename)

        try:
            excel = pd.ExcelFile(path)
            matrices[stof_key] = excel.sheet_names
        except Exception as e:
            st.warning(f"Kon {filename} niet laden: {e}")

    st.subheader("Gevonden TOPPOINT gordijn-matrixen")
    st.write(
        {
            stof: sheets
            for stof, sheets in sorted(matrices.items())
        }
    )
