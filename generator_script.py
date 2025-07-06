# generator_script.py

import random
import faker
import pandas as pd
import streamlit as st # Necessario per st.session_state

# --- Lista Predefinita di IBAN ---
# Mantieni la lista predefinita di IBAN per paese.
# Aggiungi o modifica gli IBAN qui secondo necessità.
PREDEFINED_IBANS = {
    'IT': [
        'IT60X0542811101000000123456',
        'IT78 D030 0203 2804 1273 3151 412',
        'IT06 G030 0203 2803 5544 7775 818',
        'IT86 L030 0203 2805 6293 1199 695',
        'IT45 D030 0203 2803 4495 9799 571',
        'IT15 H030 0203 2809 1117 7641 215',
        'IT44 I030 0203 2807 4327 3327 374',
        'IT27 E030 0203 2802 8111 7359 146',
        'IT44 H030 0203 2807 3296 9844 712',
        'IT94 T030 0203 2804 1445 2728 118',
        'IT94 K030 0203 2803 5729 2872 147',
        'IT85 F030 0203 2801 2916 2286 758',
        'IT65 J030 0203 2806 8662 3939 289',
        'IT44 V030 0203 2804 5479 4388 283',
        'IT45 Z030 0203 2807 6759 9230 498',
        'IT75 K030 0203 2809 0692 3768 498',
        'IT61 P030 0203 2800 2395 5125 379',
        'IT25 F030 0203 2803 9194 6927 741',
        'IT17 O030 0203 2803 7705 6447 087',
        'IT11 Y030 0203 2807 4631 6636 899',
        'IT13 A030 0203 2803 3191 9543 821',
        'IT79 F030 0203 2807 9546 3211 669',
        'IT90 X030 0203 2800 4072 0407 262',
        'IT13 T030 0203 2804 6527 8979 017',
        # Aggiungi altri IBAN italiani...
    ],
    'FR': [
        'FR1420041010050500013M02606',
        'FR7630002055000000157841Z02',
        'FR2130076031001234567890189',
        # Aggiungi altri IBAN francesi...
    ],
    'DE': 
        'DE75 5121 0800 1245 1261 99',
        'DE12 5001 0517 0648 4898 90',
        'DE02 1001 0010 0006 8201 01',
        'DE89 3704 0044 0532 0130 00',
    ],
    'LU': [
        'LU56 0019 3610 8911 3870',
        'LU44 0013 2473 0390 0997',
        'LU11 0015 9035 6530 1365',
        'LU11 0013 4967 9797 0288',
        'LU64 0014 1801 4852 3415',
        'LU28 0012 8903 8353 9753',
        'LU38 0019 8872 1893 2556',
        'LU57 0017 8684 8572 7871',
        'LU46 0018 5979 5102 6154',
        'LU49 0018 2713 3726 4834',
    ],
}

# --- Gestione della Lista IBAN in Session State ---
# Usa session_state per mantenere la lista shuffled e l'indice per ogni paese.
def get_next_iban(country_code):
    country_code_upper = country_code.upper()

    # Inizializza o ottieni lo stato della lista IBAN per questo paese nella sessione
    if 'iban_list_state' not in st.session_state:
        st.session_state.iban_list_state = {}

    # Controlla se la lista per questo paese esiste e se l'indice non ha superato la lunghezza della lista
    if country_code_upper not in st.session_state.iban_list_state or \
       st.session_state.iban_list_state[country_code_upper]['index'] >= \
       len(st.session_state.iban_list_state[country_code_upper]['list']):

        # Se la lista non esiste o è stata esaurita, prendi la lista predefinita
        iban_list = list(PREDEFINED_IBANS.get(country_code_upper, [])) # Ottieni una COPIA della lista predefinita
        random.shuffle(iban_list) # Mescola la lista

        # Salva la lista mescolata e resetta l'indice nello stato della sessione
        st.session_state.iban_list_state[country_code_upper] = {
            'list': iban_list,
            'index': 0
        }
        # print(f"Inizializzata/Rimescolata lista IBAN per {country_code_upper}. Lunghezza: {len(iban_list)}") # Debug

    # Recupera lo stato aggiornato
    iban_list_state = st.session_state.iban_list_state[country_code_upper]

    # Se la lista mescolata non è vuota, prendi l'IBAN all'indice corrente
    if iban_list_state['list']:
        iban_to_return = iban_list_state['list'][iban_list_state['index']]
        # Incrementa l'indice per la prossima volta
        st.session_state.iban_list_state[country_code_upper]['index'] += 1
        # print(f"Assegnato IBAN {iban_to_return}. Prossimo indice per {country_code_upper}: {st.session_state.iban_list_state[country_code_upper]['index']}") # Debug
        return iban_to_return
    else:
        # Se la lista predefinita per questo paese era vuota
        # print(f"Lista predefinita IBAN vuota per {country_code_upper}") # Debug
        return "Lista IBAN predefinita vuota per " + country_code_upper

# --- Funzione Principale per Generare un Singolo Profilo ---
def genera_profilo_singolo(paese_nome, campi_aggiuntivi=None):
    # Mappature nome paese -> locale Faker e codice ISO
    localizzazioni = {
        'italia': 'it_IT',
        'francia': 'fr_FR',
        'germania': 'de_DE',
        'lussemburgo': 'fr_LU' # Usiamo la locale francese per il Lussemburgo
    }
    iso_codes = {
        'italia': 'IT',
        'francia': 'FR',
        'germania': 'DE',
        'lussemburgo': 'LU'
    }

    paese_lower = paese_nome.lower()

    # Validazione del nome paese rispetto alle nostre mappature
    if paese_lower not in localizzazioni:
        print(f"Errore: Nome paese non supportato: {paese_nome}")
        return pd.DataFrame() # Ritorna un DataFrame vuoto in caso di paese non supportato

    # Inizializza Faker con la locale specifica per generare i dati del profilo
    # Questo assicura che nome, indirizzo, data di nascita, telefono, email ecc. siano appropriati per il paese.
    try:
        fake = faker.Faker(localizzazioni[paese_lower])
        # Faker carica automaticamente i provider standard per la locale.
    except Exception as e:
         print(f"Errore durante l'inizializzazione di Faker per locale {localizzazioni[paese_lower]}: {e}")
         return pd.DataFrame() # Ritorna un DataFrame vuoto in caso di errore Faker


    profilo = {}

    # --- Genera SEMPRE i campi obbligatori ---
    profilo['Nome'] = fake.first_name()
    profilo['Cognome'] = fake.last_name()

    try:
       # Genera Data di Nascita (tipicamente tra 18 e 75 anni)
       profilo['Data di Nascita'] = fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%d/%m/%Y')
    except Exception: # Gestisce potenziali errori se date_of_birth fallisce per una locale
       profilo['Data di Nascita'] = 'N/A'

    try:
       # Genera Indirizzo (sostituisci newline con virgole per una riga singola)
       profilo['Indirizzo'] = fake.address().replace("\n", ", ")
    except Exception: # Gestisce potenziali errori se la generazione indirizzo fallisce
       profilo['Indirizzo'] = 'N/A'

    # Ottieni l'IBAN dalla lista predefinita usando la session state
    country_iso = iso_codes.get(paese_lower)
    profilo['IBAN'] = get_next_iban(country_iso) # Chiama la funzione per prendere il prossimo IBAN

    # Aggiungi il campo Paese
    profilo['Paese'] = paese_nome # Usa il nome paese originale per la visualizzazione

    # --- Genera i campi opzionali SOLO se selezionati ---
    # Assicurati che campi_aggiuntivi sia una lista, anche se None viene passato
    campi_aggiuntivi = campi_aggiuntivi if isinstance(campi_aggiuntivi, list) else []

    if 'Telefono' in campi_aggiuntivi:
        try:
           profilo['Telefono'] = fake.phone_number()
        except Exception:
           profilo['Telefono'] = 'N/A' # Gestisce errori se il telefono non è generabile

    if 'Email' in campi_aggiuntivi:
        try:
           profilo['Email'] = fake.email()
        except Exception:
           profilo['Email'] = 'N/A' # Gestisce errori se l'email non è generabile

    if 'Codice Fiscale' in campi_aggiuntivi:
        # Il Codice Fiscale (SSN) è molto specifico per l'Italia
        # Controlla sia se il paese è Italia SIA se il provider supporta ssn()
        profilo['Codice Fiscale'] = fake.ssn() if paese_lower == 'italia' and hasattr(fake, 'ssn') else 'N/A'

    if 'Partita IVA' in campi_aggiuntivi:
        # La Partita IVA (VAT ID) può esistere in diverse locale, ma il metodo può variare.
        # Usiamo getattr per accedere al metodo in modo sicuro e lo chiamiamo solo se esiste.
        profilo['Partita IVA'] = getattr(fake, 'vat_id', lambda: 'N/A')()


    # Restituisci il singolo profilo come DataFrame
    return pd.DataFrame([profilo])
