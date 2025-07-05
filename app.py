
import streamlit as st
import pandas as pd
import os
import json
from generator_script import genera_dati, escludi_iban, carica_cache, carica_esclusi
from datetime import datetime

IBAN_CACHE_FILE = "iban_cache.json"

st.set_page_config(page_title="Generatore Profili Fittizi", layout="centered")
st.title("🔐 Generatore di Profili Fittizi Realistici con IBAN Validati")

menu = st.sidebar.radio("📋 Menu", ["Generatore Profili", "Gestione IBAN", "📤 Esporta & Backup"])

if menu == "Generatore Profili":
    st.markdown("🔎 Gli IBAN sono validati e selezionati da una lista cache (massimo 5 per paese).")

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
            with st.spinner("Generazione e verifica in corso..."):
                df = genera_dati(paese, n=numero, campi=campi_scelti)
            if df.empty:
                st.error("Nessun profilo valido generato. Riprova.")
            else:
                st.success(f"✅ {len(df)} profili generati per {paese}")
                st.dataframe(df)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Scarica CSV", data=csv, file_name="profili_fittizi.csv", mime="text/csv")

elif menu == "Gestione IBAN":
    st.subheader("🔧 Gestione IBAN per Paese")

    if os.path.exists(IBAN_CACHE_FILE):
        with open(IBAN_CACHE_FILE, "r") as f:
            cache = json.load(f)
    else:
        cache = {}

    paese = st.selectbox("🌍 Seleziona il paese da gestire", list(cache.keys()))

    if paese in cache and cache[paese]:
        st.write("IBAN validi salvati:")
        for iban in cache[paese]:
            col1, col2 = st.columns([4, 1])
            col1.write(iban)
            if col2.button("❌ Elimina", key=iban):
                escludi_iban(iban)
                st.success(f"IBAN {iban} eliminato.")
                st.experimental_rerun()
    else:
        st.info("Nessun IBAN ancora generato per questo paese.")

elif menu == "📤 Esporta & Backup":
    st.subheader("📊 Esporta cache IBAN in Excel")
    cache = carica_cache()
    esclusi = list(carica_esclusi())

    excel_path = f"iban_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    with pd.ExcelWriter(excel_path) as writer:
        for paese, ibans in cache.items():
            df = pd.DataFrame({'IBAN': ibans})
            df.to_excel(writer, sheet_name=paese, index=False)
        pd.DataFrame({'Esclusi': esclusi}).to_excel(writer, sheet_name='Esclusi', index=False)

    with open(excel_path, 'rb') as f:
        st.download_button("⬇️ Scarica Excel", f.read(), file_name=excel_path, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    st.info("🔄 Backup automatico su Google Drive (placeholder - richiede configurazione PyDrive).")
