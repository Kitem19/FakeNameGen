# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time
import html
import xml.etree.ElementTree as ET

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili Avanzato", page_icon="📫", layout="centered")

# --- STILE CSS PERSONALIZZATO E SCRIPT JS ---
st.markdown("""
<style>
/* Stile per l'iframe dell'email */
iframe {
    color-scheme: light;
}
/* Stile per il testo semplice dell'email */
.email-text-body {
    white-space: pre-wrap;
    font-family: monospace;
    color: #FAFAFA;
    background-color: rgba(40, 43, 54, 0.5);
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(250, 250, 250, 0.2);
}
/* Stile per i campi di solo testo, per renderli selezionabili */
.selectable-text-field {
    border: 1px solid rgba(250, 250, 250, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 1rem;
    background-color: #0E1117;
    color: #FAFAFA;
    width: 100%;
    margin-bottom: 1rem;
    box-sizing: border-box;
}
/* Stile per il contenitore dell'email con icona di copia */
.email-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(250, 250, 250, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    background-color: #0E1117;
    margin-bottom: 1rem;
}
.email-container span {
    color: #FAFAFA;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 1rem;
}
.copy-icon {
    cursor: pointer;
    font-size: 1rem; /* Dimensione ridotta per allinearsi meglio */
    margin-left: 10px;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
}
.copy-icon:hover {
    opacity: 0.7;
    background-color: rgba(250, 250, 250, 0.1);
}
</style>
<script>
// Funzione di copia robusta che funziona su HTTP e HTTPS
function copyToClipboard(element, text) {
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = text;
    document.body.appendChild(tempInput);
    tempInput.select();
    tempInput.setSelectionRange(0, 99999); /* For mobile devices */

    try {
        document.execCommand("copy");
        // Fornisce un feedback visivo all'utente
        var originalText = element.innerText;
        element.innerText = "Copiato!";
        element.style.color = "#28a745"; // Verde successo
        setTimeout(function() {
            element.innerText = originalText;
            element.style.color = ""; // Ripristina colore
        }, 1500); // Cambia di nuovo dopo 1.5 secondi
    } catch (err) {
        alert("Errore: impossibile copiare l'indirizzo.");
    }

    document.body.removeChild(tempInput);
}
</script>
""", unsafe_allow_html=True)


# --- COSTANTI E DATI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# ==============================================================================
#                      FUNZIONI API PER I SERVIZI EMAIL
# ==============================================================================

# --- GUERRILLA MAIL ---
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "service": "guerrilla"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore creazione email (Guerrilla): {e}")
        return None

# --- MAIL.TM ---
@st.cache_data(ttl=3600)
def get_mailtm_domains():
    try:
        r = requests.get("https://api.mail.tm/domains", headers=USER_AGENT_HEADER, timeout=10)
        r.raise_for_status()
        # FIX: L'API restituisce un dizionario, la lista è nella chiave 'hydra:member'
        return [domain['domain'] for domain in r.json().get('hydra:member', [])]
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch Mail.tm domains: {e}")
        return []

def create_mailtm_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    try:
        requests.post("https://api.mail.tm/accounts", json={"address": address, "password": password}, headers=USER_AGENT_HEADER, timeout=10).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json={"address": address, "password": password}, headers=USER_AGENT_HEADER, timeout=10)
        token_resp.raise_for_status()
        return {"address": address, "token": token_resp.json()['token'], "service": "mail.tm"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore creazione email (Mail.tm): {e}")
        return None

# --- FUNZIONE UNIFICATA PER LEGGERE I MESSAGGI ---
def fetch_messages(info):
    try:
        if info['service'] == 'guerrilla':
            url = f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}"
            r = requests.get(url, headers=USER_AGENT_HEADER, timeout=10)
            r.raise_for_status()
            return r.json().get("list", [])
        
        elif info['service'] == 'mail.tm':
            headers = {**USER_AGENT_HEADER, 'Authorization': f'Bearer {info["token"]}'}
            r = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
            r.raise_for_status()
            # FIX: Anche qui, la lista dei messaggi è in 'hydra:member'
            return r.json().get('hydra:member', [])
    except Exception as e:
        st.warning(f"Errore durante il recupero dei messaggi: {e}")
        return []
    return []


# ==============================================================================
#                      FUNZIONI DI LOGICA E UI
# ==============================================================================
def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, email_service, mailtm_domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    
    p = {
        'Nome': fake.first_name(), 'Cognome': fake.last_name(),
        'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'),
        'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country
    }
    
    if 'Email' in extra_fields:
        if email_service == "Guerrilla Mail":
            result = create_guerrillamail_account()
        else:
            result = create_mailtm_account(mailtm_domain)
        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"

    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    
    return pd.DataFrame([p])

def display_profile_card(profile_data):
    st.subheader("📄 Dettagli del Profilo Generato")

    def render_field(label, value):
        st.markdown(f"**{label}**")
        st.markdown(f"<div class='selectable-text-field'>{value}</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: render_field("Nome", profile_data.get("Nome", "N/A"))
    with col2: render_field("Cognome", profile_data.get("Cognome", "N/A"))
    
    render_field("Data di Nascita", profile_data.get("Data di Nascita", "N/A"))
    render_field("Indirizzo", profile_data.get("Indirizzo", "N/A"))
    render_field("IBAN", profile_data.get("IBAN", "N/A"))
    
    if "Telefono" in profile_data: render_field("Telefono", profile_data.get("Telefono"))
    if "Codice Fiscale" in profile_data: render_field("Codice Fiscale", profile_data.get("Codice Fiscale"))
    if "Partita IVA" in profile_data: render_field("Partita IVA", profile_data.get("Partita IVA"))

    if "Email" in profile_data and "fallita" not in profile_data["Email"]:
        email = profile_data['Email']
        st.markdown(f"**Email**")
        st.markdown(f"""
        <div class="email-container">
            <span>{email}</span>
            <span class="copy-icon" onclick="copyToClipboard(this, '{email}')" title="Copia email">📋</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")

def display_inbox(info):
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    
    col1, col2 = st.columns([1,1])
    if col1.button("🔁 Controlla/Aggiorna messaggi"):
        with st.spinner("Recupero messaggi..."):
            st.session_state.messages = fetch_messages(info)
            st.rerun()

    if col2.button("🔄 Aggiorna Automaticamente (2 min)"):
        st.session_state.messages = []
        placeholder = st.empty()
        with st.spinner("Ricerca automatica attiva..."):
            for i in range(12):
                placeholder.info(f"Controllo in corso... (Tentativo {i+1}/12)")
                messages = fetch_messages(info)
                if messages:
                    st.session_state.messages = messages
                    st.toast("✅ Trovati nuovi messaggi!", icon="🎉")
                    placeholder.empty()
                    st.rerun()
                if i < 11: time.sleep(10)
            else:
                st.toast("Ricerca terminata. Nessun nuovo messaggio trovato.", icon="📭")
                placeholder.empty()

    if 'messages' in st.session_state and st.session_state.messages:
        messages = st.session_state.messages
        st.success(f"Trovati {len(messages)} messaggi.")
        for m in reversed(messages):
            if info['service'] == 'guerrilla':
                with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                    with st.spinner("Caricamento corpo..."):
                        full_email_resp = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={m['mail_id']}&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                        full_email_data = full_email_resp.json()
                    timestamp = int(m['mail_timestamp'])
                    date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                    st.markdown(f"**Data:** {date_str}"); st.markdown("---")
                    email_body_html = full_email_data.get('mail_body')
                    if "<html>" in email_body_html.lower() or "<div>" in email_body_html.lower():
                        st.components.v1.html(email_body_html, height=400, scrolling=True)
                    else:
                        plain_text = html.unescape(email_body_html)
                        st.markdown(f"<div class='email-text-body'>{plain_text}</div>", unsafe_allow_html=True)
            
            elif info['service'] == 'mail.tm':
                with st.spinner(f"Carico dettagli messaggio ID: {m.get('id', '')[:10]}"):
                    headers = {**USER_AGENT_HEADER, 'Authorization': f'Bearer {info["token"]}'}
                    detail_resp = requests.get(f"https://api.mail.tm/messages/{m.get('id')}", headers=headers).json()
                
                sender = detail_resp.get('from', {}).get('address', 'N/A')
                subject = detail_resp.get('subject', 'N/A')
                with st.expander(f"✉️ **Da:** {sender} | **Oggetto:** {subject}"):
                    date_str = detail_resp.get('createdAt', 'N/A')
                    st.markdown(f"**Data:** {date_str}")
                    st.markdown("---")
                    html_content = detail_resp.get("html")
                    if html_content and isinstance(html_content, list) and html_content:
                        st.components.v1.html(html_content[0], height=400, scrolling=True)
                    elif detail_resp.get("text"):
                        st.markdown(f"<div class='email-text-body'>{html.escape(detail_resp['text'])}</div>", unsafe_allow_html=True)
                    else:
                        st.info("Nessun contenuto visualizzabile.")
    elif 'messages' in st.session_state and st.session_state.messages is not None:
         st.info("📭 La casella di posta è vuota.")


# ==============================================================================
#                      INTERFACCIA UTENTE PRINCIPALE
# ==============================================================================
st.title("📫 Generatore di Profili Avanzato")
st.markdown("Genera profili fittizi completi di email temporanea funzionante da diversi provider.")

# Inizializzazione Session State
if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None
if 'messages' not in st.session_state: st.session_state.messages = None
if 'show_success' not in st.session_state: st.session_state.show_success = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Opzioni di Generazione")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    
    mailtm_domain_selection = None
    email_service = "Guerrilla Mail"
    if 'Email' in fields:
        st.markdown("---")
        email_service = st.radio("Scegli il servizio email", ["Guerrilla Mail", "Mail.tm"], horizontal=True)
        if email_service == "Mail.tm":
            domains = get_mailtm_domains()
            if domains:
                mailtm_domain_selection = st.selectbox("Dominio Mail.tm", domains)
            else:
                st.error("Domini Mail.tm non disponibili al momento.")
    
    if st.button("🚀 Genera Profili", type="primary"):
        if 'Email' in fields and email_service == "Mail.tm" and not mailtm_domain_selection:
            st.warning("Seleziona un dominio Mail.tm prima di generare.")
        else:
            with st.spinner("Generazione in corso..."):
                dfs = [generate_profile(country, fields, email_service, mailtm_domain_selection) for _ in range(n)]
            st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)
            st.session_state.messages = None
            st.session_state.show_success = True
            st.rerun()

# --- AREA PRINCIPALE ---
if st.session_state.final_df is not None:
    if st.session_state.show_success:
        st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
        st.session_state.show_success = False
    
    if len(st.session_state.final_df) == 1:
        display_profile_card(st.session_state.final_df.iloc[0])
    else:
        st.dataframe(st.session_state.final_df)
    
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.get('email_info')
    if info and "fallita" not in info.get("address", "fallita"):
        display_inbox(info)
