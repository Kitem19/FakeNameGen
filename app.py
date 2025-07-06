# app.py

import streamlit as st
import pandas as pd
import os
import json
# Importa le funzioni necessarie dal tuo script generator
from generator_script import genera_dati, escludi_iban, carica_cache, carica_esclusi 
from datetime import datetime

# I nomi dei file di cache e esclusi sono definiti in generator_script.py, non è necessario ridefinirli qui.

st.set_page_config(page_title="Generatore Profili Fittizi", layout="centered")
st.title("🔐 Generatore di Profili Fittizi Realistici") # Titolo leggermente modificato per riflettere che IBAN potrebbe non essere sempre valido

# Menu di navigazione nella sidebar
menu = st.sidebar.radio("📋 Menu", ["Generatore Profili", "Gestione IBAN", "📤 Esporta & Backup"])

# --- Sezione Generatore Profili ---
if menu == "Generatore Profili":
    st.markdown("🔎 Gli IBAN sono validati e selezionati da una lista cache (massimo 5 per paese) o generati e validati al momento.")
    st.markdown("⚠️ **Nota:** La generazione di IBAN validi dipende da un servizio esterno (openiban.com) che potrebbe non essere sempre disponibile, stabile o superare i limiti di utilizzo gratuiti. In caso di problemi, il campo IBAN potrebbe mostrare 'Non trovato'.")

    # Selezione del paese e del numero di profili
    paese = st.selectbox("🌍 Scegli un paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    # Puoi aumentare il limite massimo se necessario per la tua applicazione
    numero = st.slider("🔢 Quanti profili vuoi generare?", 1, 100, 5)

    # Selezione dei campi da includere
    tutti_i_campi = [
        "Nome", "Cognome", "Data di Nascita", "Indirizzo", "Telefono",
        "Email", "Codice Fiscale", "Partita IVA", "IBAN", "Paese"
    ]
    campi_scelti = st.multiselect("🧩 Scegli i campi da generare", options=tutti_i_campi, default=tutti_i_campi)

    # Pulsante per generare i profili
    if st.button("🎲 Genera Profili"):
        if not campi_scelti:
            st.error("Seleziona almeno un campo da generare.")
        else:
            # Mostra uno spinner durante la generazione
            with st.spinner("Generazione e verifica in corso... Potrebbe richiedere del tempo per la validazione IBAN esterna."):
                # Chiama la funzione genera_dati dallo script generator
                # Passiamo i campi_scelti per generare solo quelli richiesti
                df = genera_dati(paese, n=numero, campi=campi_scelti)

            # Controlla se il DataFrame non è vuoto
            if df.empty:
                 # Questo caso dovrebbe verificarsi solo se la generazione base fallisce (es. nessuna locale trovata, nessun campo selezionato)
                 st.error("Nessun profilo generato. Controlla la selezione dei campi e riprova.")
            else:
                st.success(f"✅ {len(df)} profili richiesti generati per {paese}.")

                # Controlla specificamente il campo IBAN se è stato richiesto
                if 'IBAN' in campi_scelti:
                    # Conta quanti IBAN non sono stati trovati
                    non_trovati_count = (df['IBAN'] == 'Non trovato').sum()
                    if non_trovati_count > 0:
                        # Mostra un avviso se alcuni IBAN non sono stati generati/validati con successo
                        st.warning(f"⚠️ Impossibile generare/validare IBAN validi per {non_trovati_count} profilo/i dopo diversi tentativi. Il campo mostrerà 'Non trovato'.")

                # Mostra il DataFrame generato
                st.dataframe(df)

                # Pulsante per scaricare i dati in formato CSV
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Scarica CSV",
                    data=csv,
                    file_name="profili_fittizi.csv",
                    mime="text/csv"
                )

# --- Sezione Gestione IBAN ---
elif menu == "Gestione IBAN":
    st.subheader("🔧 Gestione IBAN Memorizzati")
    st.info("Qui puoi vedere gli IBAN validati e memorizzati nella cache locale. Puoi escluderli se non vuoi che vengano più usati. Gli IBAN esclusi non verranno più generati o utilizzati dalla cache.")

    # Carica la cache e la lista degli esclusi
    cache = carica_cache()
    esclusi = carica_esclusi()

    # Mostra gli IBAN in cache per paese
    st.markdown("#### IBAN validati in cache per paese:")
    paesi_con_iban_in_cache = list(cache.keys())
    if not paesi_con_iban_in_cache:
         st.info("Nessun IBAN valido ancora salvato in cache.")
    else:
        # Permette di selezionare un paese per vedere i suoi IBAN in cache
        paese_selezionato_cache = st.selectbox("🌍 Seleziona un paese dalla cache", paesi_con_iban_in_cache)

        if paese_selezionato_cache in cache and cache[paese_selezionato_cache]:
            st.write(f"IBAN in cache per **{paese_selezionato_cache}**:")
            # Mostra ogni IBAN con un pulsante per escluderlo
            for iban in cache[paese_selezionato_cache]:
                col1, col2 = st.columns([4, 1])
                col1.write(iban)
                # Usa una key univoca per ogni pulsante "Escludi"
                if col2.button("❌ Escludi", key=f"escludi_{iban}_{paese_selezionato_cache}"):
                    escludi_iban(iban) # Chiama la funzione escludi_iban
                    st.success(f"IBAN {iban} aggiunto alla lista esclusi.")
                    st.experimental_rerun() # Ricarica la pagina per aggiornare le liste

        else:
             st.info(f"Nessun IBAN salvato in cache per {paese_selezionato_cache}.")

    st.markdown("---")
    st.markdown("#### 🚫 IBAN Esclusi:")
    # Mostra la lista degli IBAN esclusi
    if esclusi:
        st.write("Questi IBAN sono stati esclusi e non verranno più usati:")
        for iban_escluso in esclusi:
             col_e1, col_e2 = st.columns([4, 1])
             col_e1.write(iban_escluso)
             # Potresti aggiungere qui un pulsante per "Rimuovi da esclusi" se necessario
             # if col_e2.button("✅ Riabilita", key=f"riabilita_{iban_escluso}"):
             #     # Implementa logica per rimuovere da esclusi (richiede modifica generator_script)
             #     pass # Placeholder

    else:
        st.info("Nessun IBAN nella lista esclusi al momento.")

# --- Sezione Esporta & Backup ---
elif menu == "📤 Esporta & Backup":
    st.subheader("📊 Esporta Cache IBAN e Lista Esclusi")
    st.info("Scarica i dati memorizzati sugli IBAN (validati in cache ed esclusi) in un file Excel.")

    cache = carica_cache()
    esclusi = list(carica_esclusi()) # Converte il set in lista per l'esportazione

    # Prepara i dati per l'esportazione in formato Excel
    excel_filename = f"iban_cache_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Creiamo un dizionario dove ogni chiave è un nome di foglio/colonna
    excel_data = {}
    # Aggiungiamo i dati dalla cache per paese
    for paese, ibans in cache.items():
        excel_data[paese] = ibans
    # Aggiungiamo la lista degli esclusi
    excel_data['Esclusi'] = esclusi

    # Creiamo un DataFrame per l'esportazione. Gestiamo lunghezze diverse delle liste aggiungendo None.
    max_len = max((len(v) for v in excel_data.values()), default=0) # Trova la lunghezza massima delle liste
    export_df_data = {k: v + [None]*(max_len - len(v)) for k, v in excel_data.items()} if excel_data else {}
    export_df = pd.DataFrame(export_df_data)

    # Esporta il DataFrame in un buffer di memoria in formato Excel
    if not export_df.empty:
        import io
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
             # Scrive il DataFrame in un foglio chiamato 'IBAN Cache'
             export_df.to_excel(writer, sheet_name='IBAN Cache', index=False)

        excel_buffer.seek(0) # Torna all'inizio del buffer prima di leggere/scaricare

        # Pulsante per scaricare il file Excel
        st.download_button(
            label="⬇️ Scarica Excel Cache IBAN",
            data=excel_buffer,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nessun dato nella cache IBAN o nella lista esclusi da esportare.")


    st.markdown("---")
    st.info("🔄 Backup automatico su Google Drive (placeholder). Questa funzionalità non è attiva in questa versione e richiederebbe configurazione aggiuntiva (es. PyDrive).")
