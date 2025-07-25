# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time

st.set_page_config(page_title="Generatore di Profili (Guerrilla + MailTM)", page_icon="📫", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- FUNZIONE COPIA EMAIL CON TEXT_INPUT E BOTTONE ---

def email_copy_box(email):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text_input("Indirizzo email", value=email, key="mailtm_copy", disabled=True, label_visibility="collapsed")
    with col2:
        if st.button("📋", help="Copia email negli appunti", key="copy_btn"):
            st.session_state.clipboard_copied = email
            st.toast("Email copiata!")
    if st.session_state.get("clipboard_copied") == email:
        st.markdown(f"""
            <script>
            navigator.clipboard.writeText("{email}");
            </script>
            """, unsafe_allow_html=True)
        st.session_state.clipboard_copied = None

# --- GUERRILLA MAIL ---

def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER)
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "provider": "Guerrilla Mail"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nella creazione dell'email: {e}")
        return None

def inbox_guerrillamail(info):
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    if st.button("🔁 Controlla/Aggiorna messaggi (Guerrilla Mail)"):
        with st.spinner("Recupero messaggi..."):
            try:
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                r.raise_for_status()
                st.session_state.messages = r.json().get("list", [])
            except Exception as e:
                st.error(f"Errore lettura posta: {e}")
                st.session_state.messages = []

    if 'messages' in st.session_state:
        messages = st.session_state.messages
        if not messages:
            st.info("📭 La casella di posta è vuota.")
        else:
            st.success(f"Trovati {len(messages)} messaggi.")
            data = []
            for m in reversed(messages):
                timestamp = int(m['mail_timestamp'])
                date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                data.append({
                    "ID": m['mail_id'],
                    "Da": m['mail_from'],
                    "Oggetto": m['mail_subject'],
                    "Data": date_str
                })
            df_msgs = pd.DataFrame(data)
            st.dataframe(df_msgs.drop("ID", axis=1), use_container_width=True)
            selected_id = st.selectbox("Seleziona il messaggio per visualizzare il corpo", options=df_msgs["ID"])
            if selected_id:
                full_email_resp = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={selected_id}&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                email_body = full_email_resp.json().get('mail_body', '<i>Corpo non disponibile.</i>')
                st.markdown("### Corpo del messaggio")
                st.components.v1.html(email_body, height=400, scrolling=True)

# --- MAIL.TM ---

def get_mailtm_domains():
    try:
        r = requests.get("https://api.mail.tm/domains")
        r.raise_for_status()
        data = r.json()
        return [d['domain'] for d in data.get('hydra:member', [])]
    except:
        return []

def create_mailtm_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    data = {"address": address, "password": password}
    try:
        requests.post("https://api.mail.tm/accounts", json=data).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json=data)
        token_resp.raise_for_status()
        return {"address": address, "token": token_resp.json()['token'], "provider": "mail.tm"}
    except Exception as e:
        st.error(f"Errore creazione account mail.tm: {e}")
        return None

def inbox_mailtm(info):
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    # Visualizza indirizzo con tasto copia
    email_copy_box(info['address'])

    # Aggiornamento automatico messaggi
    autorefresh = st.button("⏳ Aggiorna inbox ogni 10s per 2 minuti o fino al primo messaggio")
    if autorefresh:
        with st.spinner("Controllo inbox su mail.tm in background..."):
            poll_end = time.time() + 120  # 2 minuti
            found = False
            while time.time() < poll_end and not found:
                try:
                    headers = {'Authorization': f'Bearer {info["token"]}'}
                    r = requests.get("https://api.mail.tm/messages", headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    if isinstance(data, dict) and 'hydra:member' in data:
                        messages = data['hydra:member']
                    elif isinstance(data, list):
                        messages = data
                    else:
                        messages = []
                    if messages:
                        st.success(f"📬 Arrivati {len(messages)} messaggi!")
                        found = True
                        st.session_state.mailtm_messages = messages
                    else:
                        st.info("⏳ Nessun messaggio ancora, riprovo tra 10 secondi...")
                except Exception as e:
                    st.error(f"Errore durante polling: {e}")
                    break
                if not found:
                    time.sleep(10)
            if not found:
                st.info("⏱️ Tempo scaduto senza nuovi messaggi.")
    else:
        # Aggiornamento manuale
        if st.button("🔁 Controlla/Aggiorna messaggi adesso (mail.tm)"):
            try:
                headers = {'Authorization': f'Bearer {info["token"]}'}
                r = requests.get("https://api.mail.tm/messages", headers=headers)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and 'hydra:member' in data:
                    messages = data['hydra:member']
                elif isinstance(data, list):
                    messages = data
                else:
                    messages = []
                st.session_state.mailtm_messages = messages
            except Exception as e:
                st.error(f"Errore lettura posta: {e}")
                st.session_state.mailtm_messages = []

    if 'mailtm_messages' in st.session_state:
        messages = st.session_state.mailtm_messages
        if not messages:
            st.info("📭 La casella di posta è vuota.")
        else:
            st.success(f"Trovati {len(messages)} messaggi.")
            for m in reversed(messages):
                sender = m.get('from', {}).get('address', 'Sconosciuto')
                subject = m.get('subject', 'Senza oggetto')
                with st.expander(f"✉️ {sender} | {subject}"):
                    msg_id = m["id"]
                    try:
                        headers = {'Authorization': f'Bearer {info["token"]}'}
                        detail_resp = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
                        detail_resp.raise_for_status()
                        msg = detail_resp.json()
                        st.markdown(f"**Oggetto:** {msg.get('subject', 'N/A')}")
                        st.markdown(f"**Mittente:** {msg.get('from', {}).get('address', 'N/A')}")
                        st.markdown(f"**Data:** {msg.get('createdAt', '')}")
                        st.markdown("---")
                        html_content = msg.get("html")
                        if html_content:
                            st.markdown("**Contenuto (HTML):**", unsafe_allow_html=True)
                            st.components.v1.html(html_content, height=300, scrolling=True)
                        elif msg.get("text"):
                            st.markdown("**Contenuto (Testo):**")
                            st.code(msg["text"])
                        else:
                            st.code(msg.get("intro", "Nessun contenuto."))
                        if msg.get("attachments"):
                            st.markdown("**📂 Allegati:**")
                            for att in msg["attachments"]:
                                st.markdown(f"- [{att.get('filename')}]({att.get('downloadUrl')})")
                    except Exception as e:
                        st.warning(f"Errore nella lettura corpo: {e}")

# ------- PROVIDER MAPPING ---------

PROVIDERS = {
    "Guerrilla Mail": (create_guerrillamail_account, inbox_guerrillamail),
    "mail.tm": (create_mailtm_account, inbox_mailtm)
}

def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state:
        st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"])
        random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, provider, mailtm_domain=None):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    fake = Faker(locs[country])
    profile = {
        'Nome': fake.first_name(),
        'Cognome': fake.last_name(),
        'Paese': country,
        'IBAN': get_next_iban(codes[country])
    }
    if 'Email' in extra_fields:
        if provider == "Guerrilla Mail":
            result = PROVIDERS[provider][0]()
        elif provider == "mail.tm" and mailtm_domain:
            result = PROVIDERS[provider][0](mailtm_domain)
        else:
            result = None
        if not result or not result.get("address"):
            profile["Email"] = "Creazione email fallita"
            st.session_state.email_info = None
        else:
            profile["Email"] = result["address"]
            st.session_state.email_info = result
    if 'Telefono' in extra_fields:
        profile['Telefono'] = fake.phone_number()
    return profile

# ---------------- UI -----------------

st.title("📫 Generatore di Profili Guerrilla Mail / mail.tm")

if 'final_profiles' not in st.session_state:
    st.session_state.final_profiles = []
if 'email_info' not in st.session_state:
    st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 10, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono"], default=["Email"])
    provider = st.selectbox("Provider email", list(PROVIDERS.keys()))
    mailtm_domain = None
    if provider == "mail.tm":
        all_domains = get_mailtm_domains()
        if not all_domains:
            st.error("Nessun dominio mail.tm disponibile")
            st.stop()
        mailtm_domain = st.selectbox("Dominio mail.tm", sorted(all_domains))
    if st.button("🚀 Genera Profili"):
        st.session_state.final_profiles = []
        for _ in range(n):
            prof = generate_profile(country, fields, provider, mailtm_domain=mailtm_domain)
            st.session_state.final_profiles.append(prof)

if st.session_state.final_profiles:
    df_profiles = pd.DataFrame(st.session_state.final_profiles)
    st.success(f"✅ Generati {len(df_profiles)} profili.")
    st.dataframe(df_profiles, use_container_width=True)
    csv = df_profiles.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if info:
        if info.get("provider") == "Guerrilla Mail":
            inbox_guerrillamail(info)
        elif info.get("provider") == "mail.tm":
            inbox_mailtm(info)
