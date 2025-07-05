
import streamlit as st
from generator_script import genera_dati

st.set_page_config(page_title="Generatore Profili Fittizi", layout="centered")
st.title("🔐 Generatore di Profili Fittizi Realistici")

paese = st.selectbox("🌍 Scegli un paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
numero = st.slider("🔢 Quanti profili vuoi generare?", 1, 50, 5)

if st.button("🎲 Genera Profili"):
    df = genera_dati(paese, n=numero)
    st.success(f"✅ {numero} profili generati per {paese}")
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Scarica CSV", data=csv, file_name="profili_fittizi.csv", mime="text/csv")
