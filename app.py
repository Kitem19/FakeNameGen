
import streamlit as st
from generator_script import genera_dati

st.set_page_config(page_title="Generatore Profili Fittizi", layout="centered")
st.title("🔐 Generatore di Profili Fittizi Realistici")

paese = st.selectbox("🌍 Scegli un paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
numero = st.slider("🔢 Quanti profili vuoi generare?", 1, 50, 5)

tutti_i_campi = [
    "Nome", "Cognome", "Data di Nascita", "Indirizzo", "Telefono",
    "Email", "Codice Fiscale", "Partita IVA", "IBAN", "Paese"
]
campi_scelti = st.multiselect("🧩 Scegli i campi da generare", options=tutti_i_campi, default=tutti_i_campi)

if st.button("🎲 Genera Profili"):
    if not campi_scelti:
        st.error("Seleziona almeno un campo.")
    else:
        df = genera_dati(paese, n=numero, campi=campi_scelti)
        st.success(f"✅ {numero} profili generati per {paese}")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Scarica CSV", data=csv, file_name="profili_fittizi.csv", mime="text/csv")
