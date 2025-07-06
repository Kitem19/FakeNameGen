# generator_script.py

import os
import random
import faker
import pandas as pd
import requests
import json
# Importa i provider standard (anche se spesso caricati con la locale)
from faker.providers import address, phone_number, person, date_time, internet, company
# Non importiamo più BankProvider per aggiungerlo manualmente

# Definiamo i nomi dei file
IBAN_CACHE_FILE = "iban_cache.json"
EXCLUDED_IBAN_FILE = "iban_exclude.json"

def iban_valido(iban):
    # Usa l'API esterna per la validazione
    url = f"https://openiban.com/validate/{iban}?getBIC=true&validateBankCode=true"
    try:
        # Aumentato il timeout per dare più tempo alla risposta
        response = requests.get(url, timeout=15)
        # Controlla esplicitamente lo status code
        if response.status_code == 200:
            data = response.json()
            # Controlla la chiave 'valid' nel JSON di risposta
            return data.get("valid", False)
        else:
            # Potresti loggare o stampare lo status code per debug
            # print(f"Validazione fallita per {iban}: Status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        # Logga o stampa errori specifici di request (timeout, connection error, ecc.)
        # print(f"Errore di richiesta validazione IBAN per {iban}: {e}")
        return False
    except Exception as e:
        # Logga o stampa altri errori inattesi
        # print(f"Errore inatteso durante validazione IBAN per {iban}: {e}")
        return False

# Funzioni per caricare e salvare cache/esclusi con gestione errori
def carica_cache():
    if os.path.exists(IBAN_CACHE_FILE):
        try:
            with open(IBAN_CACHE_FILE, "r") as f:
                 content = f.read()
                 # Gestisce il caso di file vuoto
                 if not content:
                     return {}
                 return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            # Stampa un messaggio di errore se il file cache è corrotto o illeggibile
            print(f"Errore caricamento cache IBAN '{IBAN_CACHE_FILE}': {e}")
            return {} # Restituisce una cache vuota per non bloccare l'app
    return {}

def salva_cache(cache):
    try:
        with open(IBAN_CACHE_FILE, "w") as f:
            # Aggiunge indentazione per rendere il file JSON leggibile
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"Errore salvataggio cache IBAN '{IBAN_CACHE_FILE}': {e}")


def carica_esclusi():
    if os.path.exists(EXCLUDED_IBAN_FILE):
        try:
            with open(EXCLUDED_IBAN_FILE, "r") as f:
                content = f.read()
                # Gestisce il caso di file vuoto
                if not content:
                    return set() # Restituisce un set vuoto
                # Assicura che sia una lista prima di convertirla in set
                data = json.loads(content)
                if isinstance(data, list):
                    return set(data)
                else:
                    print(f"Contenuto non valido nel file esclusi '{EXCLUDED_IBAN_FILE}'.")
                    return set() # Restituisce un set vuoto se il formato non è corretto
        except (json.JSONDecodeError, Exception) as e:
            # Stampa un messaggio di errore se il file esclusi è corrotto o illeggibile
            print(f"Errore caricamento lista esclusi '{EXCLUDED_IBAN_FILE}': {e}")
            return set() # Restituisce un set vuoto per non bloccare l'app
    return set()

def salva_esclusi(exclude_set):
    try:
        with open(EXCLUDED_IBAN_FILE, "w") as f:
            # Salva come lista perché il JSON set non esiste
            json.dump(list(exclude_set), f, indent=4)
    except Exception as e:
        print(f"Errore salvataggio lista esclusi '{EXCLUDED_IBAN_FILE}': {e}")


def ottieni_o_aggiungi_iban(country_code):
    country_code_upper = country_code.upper()
    cache = carica_cache()
    esclusi = carica_esclusi()

    # Assicura che la chiave paese esista nella cache con una lista vuota se nuova
    if country_code_upper not in cache:
        cache[country_code_upper] = []

    # Filtra gli IBAN in cache per rimuovere quelli che sono stati esclusi nel frattempo
    cache[country_code_upper] = [iban for iban in cache.get(country_code_upper, []) if iban not in esclusi]

    # Se abbiamo già 5 IBAN validi in cache per questo paese (e non esclusi), ne scegliamo uno a caso
    if len(cache.get(country_code_upper, [])) >= 5:
        salva_cache(cache) # Salva la cache pulita prima di tornare
        # Assicura che ci siano IBAN disponibili dopo la pulizia
        if cache.get(country_code_upper):
            return random.choice(cache[country_code_upper])
        # Se non ci sono, continua per generarne di nuovi

    # Mappatura codice ISO 2 lettere -> locale Faker
    iso_to_locale = {
        'IT': 'it_IT',
        'FR': 'fr_FR',
        'DE': 'de_DE',
        'LU': 'fr_LU' # O 'lb_LU' se esiste una locale più specifica, ma fr_LU è comune
    }

    # Ottiene la locale corrispondente o usa 'en_US' come fallback (potrebbe non generare IBAN specifici)
    locale = iso_to_locale.get(country_code_upper, 'en_US')

    # Controlla se la locale è supportata da Faker (opzionale ma utile per debug)
    if locale not in faker.config.AVAILABLE_LOCALES:
         print(f"Warning: Locale '{locale}' per paese '{country_code_upper}' non disponibile in Faker. Usando fallback 'en_US'.")
         locale = 'en_US'


    tentativi = 0
    # Aumentato significativamente il numero di tentativi per trovare un IBAN valido
    max_attempts = 300 
    valid_iban_trovato = None # Variabile per memorizzare l'IBAN valido trovato nella ricerca

    while len(cache[country_code_upper]) < 5 and tentativi < max_attempts:
        try:
            # Inizializza Faker con la locale specifica SOLO per generare il formato IBAN
            # Questo assicura che il formato generato sia quello del paese.
            fake_iban_gen = faker.Faker(locale=locale)
            # Il provider Bank è già incluso nelle locale che lo supportano

            # Genera l'IBAN. Passa il country_code_upper per sicurezza, anche se la locale dovrebbe bastare
            # Alcune versioni di Faker potrebbero richiedere solo il locale, altre supportare country_code qui.
            # Usiamo il locale primariamente.
            # Controllo se il metodo iban esiste per la locale corrente
            if not hasattr(fake_iban_gen, 'iban'):
                 print(f"Locale '{locale}' non sembra supportare la generazione di IBAN. Impossibile procedere.")
                 tentativi = max_attempts # Esce dal ciclo se non si può generare
                 continue # Passa al prossimo tentativo (uscirà subito)

            # Tenta di generare l'IBAN. Alcune locale potrebbero richiedere argomenti diversi o fallire.
            try:
                nuovo_iban = fake_iban_gen.iban() # Tenta prima senza country_code qui, basandosi sul locale
            except Exception: # Se il metodo iban() senza argomenti fallisce, prova con country_code
                 try:
                     nuovo_iban = fake_iban_gen.iban(country_code=country_code_upper) # Prova a passare il country_code
                     print(f"Generato IBAN con country_code: {nuovo_iban}") # Debug
                 except Exception as e:
                     print(f"Errore generazione IBAN per {country_code_upper} con locale {locale} e country_code: {e}") # Debug
                     tentativi += 1
                     continue # Passa al prossimo tentativo

            # print(f"Tentativo {tentativi+1}: Generato raw IBAN {nuovo_iban} per {country_code_upper} con locale {locale}") # Debug

        except Exception as e:
            # Logga o stampa errori durante la generazione con Faker
            print(f"Errore generazione raw IBAN con Faker per {country_code_upper} e locale {locale}: {e}")
            tentativi += 1
            continue # Salta il tentativo corrente

        # Ignora se l'IBAN generato è già in cache o nella lista esclusi
        if nuovo_iban in cache.get(country_code_upper, []) or nuovo_iban in esclusi:
            # print(f"IBAN {nuovo_iban} già in cache o escluso. Tentativo {tentativi+1}") # Debug
            tentativi += 1
            continue

        # Valida l'IBAN generato tramite servizio esterno
        # print(f"Validazione esterna IBAN {nuovo_iban}...") # Debug
        if iban_valido(nuovo_iban):
            # print(f"Validazione riuscita per {nuovo_iban}. Aggiungo alla cache.") # Debug
            cache[country_code_upper].append(nuovo_iban)
            # Salva la cache ogni volta che si aggiunge un IBAN valido
            salva_cache(cache)
            # Se volevi restituire il primo valido trovato, potresti farlo qui
            # ma l'obiettivo è popolare la cache fino a 5, quindi non ritorniamo ancora.
            # valid_iban_trovato = nuovo_iban # Potrebbe memorizzare e restituire dopo il ciclo

        # else:
            # print(f"Validazione fallita per {nuovo_iban}. Tentativo {tentativi+1}") # Debug


        tentativi += 1

    # Dopo il ciclo di generazione, scegli un IBAN dalla cache (ora popolata o meno)
    # Assicurati di scegliere solo IBAN non esclusi (la cache è già stata pulita all'inizio, ma ricontrolliamo)
    ibans_disponibili = [iban for iban in cache.get(country_code_upper, []) if iban not in esclusi]

    if ibans_disponibili:
         # print(f"Restituisco IBAN casuale dalla cache ({len(ibans_disponibili)} disponibili).") # Debug
         return random.choice(ibans_disponibili)
    else:
         # print("Nessun IBAN valido trovato/disponibile per questo paese dopo i tentativi.") # Debug
         # Se nessun IBAN valido è stato aggiunto alla cache o tutti sono esclusi
         # Salva comunque la cache se ci sono stati tentativi di aggiunta
         salva_cache(cache) 
         return "Non trovato" # Indica che non è stato possibile ottenere un IBAN valido

def escludi_iban(iban):
    esclusi = carica_esclusi()
    cache = carica_cache()

    iban_found = False
    # Itera su tutti i paesi nella cache
    for paese_code in list(cache.keys()): # Itera su una copia delle chiavi se modifichi cache[paese_code]
        # Crea una nuova lista escludendo l'IBAN da rimuovere
        new_lista = [item for item in cache.get(paese_code, []) if item != iban]
        # Se l'IBAN è stato trovato e rimosso dalla lista di questo paese
        if len(new_lista) < len(cache.get(paese_code, [])):
            cache[paese_code] = new_lista # Aggiorna la lista nella cache
            iban_found = True # Segna che l'IBAN era in cache
            # Non fare break qui se un IBAN potesse trovarsi nella cache di più paesi (non dovrebbe accadere con IBAN veri, ma con fittizi...)
            # Tuttavia, per IBAN fittizi da un generatore con locale, dovrebbe essere legato a un paese, quindi break è ok.
            break # Esci dal ciclo una volta trovato e rimosso

    # Aggiunge l'IBAN alla lista degli esclusi
    esclusi.add(iban)

    # Salva entrambe le liste
    salva_cache(cache)
    salva_esclusi(esclusi)
    # print(f"IBAN {iban} escluso. Presente in cache prima dell'esclusione: {iban_found}") # Debug


def genera_dati(paese_nome, n=1, campi=None): # Renamed parameter for clarity
    # Mappature nome paese -> locale Faker e codice ISO
    localizzazioni = {
        'italia': 'it_IT',
        'francia': 'fr_FR',
        'germania': 'de_DE',
        'lussemburgo': 'fr_LU' # Usiamo la locale francese per il Lussemburgo come nel codice originale
    }
    iso_codes = {
        'italia': 'IT',
        'francia': 'FR',
        'germania': 'DE',
        'lussemburgo': 'LU'
    }

    paese_lower = paese_nome.lower()

    # Validazione del paese
    if paese_lower not in localizzazioni:
        raise ValueError(f"Paese non valido: {paese_nome}. Scegli tra Italia, Francia, Germania, Lussemburgo.")

    # Inizializza Faker con la locale specifica per generare gli altri dati del profilo
    # Questo assicura che nome, indirizzo, telefono ecc. siano appropriati per il paese.
    try:
        fake = faker.Faker(localizzazioni[paese_lower])
        # Aggiungere provider standard è di solito ridondante se la locale è impostata,
        # ma non fa male se vuoi essere esplicito o usi provider personalizzati.
        # fake.add_provider(address)
        # fake.add_provider(phone_number)
        # fake.add_provider(person)
        # fake.add_provider(date_time)
        # fake.add_provider(internet)
        # fake.add_provider(company)
         # Assicurati che il provider Bank sia disponibile se IBAN è richiesto
        if 'IBAN' in campi:
             # Questo check può aiutare se una locale non ha il provider bank
             if not hasattr(fake, 'iban'):
                 print(f"Attenzione: La locale {localizzazioni[paese_lower]} non sembra supportare la generazione di IBAN direttamente. La generazione IBAN potrebbe fallire.")


    except Exception as e:
         print(f"Errore durante l'inizializzazione di Faker per locale {localizzazioni[paese_lower]}: {e}")
         # Potrebbe essere necessario gestire questo errore, magari restituendo un dataframe vuoto o con un messaggio
         return pd.DataFrame()


    dati = []
    # Genera i profili richiesti
    for i in range(n): # Usa un contatore per debug se necessario
        profilo = {}
        # Aggiunge i campi richiesti al profilo
        if 'Nome' in campi: profilo['Nome'] = fake.first_name()
        if 'Cognome' in campi: profilo['Cognome'] = fake.last_name()
        if 'Data di Nascita' in campi:
             # Assicura che date_of_birth funzioni per la locale scelta
             try:
                profilo['Data di Nascita'] = fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%d/%m/%Y')
             except Exception: # Gestisce errori se la data di nascita non è generabile
                profilo['Data di Nascita'] = 'N/A'

        if 'Indirizzo' in campi:
             try:
                profilo['Indirizzo'] = fake.address().replace("\n", ", ")
             except Exception: # Gestisce errori se l'indirizzo non è generabile
                profilo['Indirizzo'] = 'N/A'

        if 'Telefono' in campi:
             try:
                profilo['Telefono'] = fake.phone_number()
             except Exception: # Gestisce errori se il telefono non è generabile
                profilo['Telefono'] = 'N/A'

        if 'Email' in campi:
             try:
                profilo['Email'] = fake.email()
             except Exception: # Gestisce errori se l'email non è generabile
                profilo['Email'] = 'N/A'

        # Campi specifici che potrebbero non esistere in tutte le locale
        if 'Codice Fiscale' in campi:
             # Questo campo è molto specifico per l'Italia
             profilo['Codice Fiscale'] = fake.ssn() if paese_lower == 'italia' and hasattr(fake, 'ssn') else 'N/A'

        if 'Partita IVA' in campi:
             # Usa getattr per accedere al metodo in modo sicuro
             # Chiama il metodo solo se esiste e se il campo è richiesto
             profilo['Partita IVA'] = getattr(fake, 'vat_id', lambda: 'N/A')()


        if 'IBAN' in campi:
            # Chiama la funzione helper per ottenere o generare un IBAN valido
            iban = ottieni_o_aggiungi_iban(iso_codes[paese_lower])
            profilo['IBAN'] = iban # Ora non filtriamo più se è "Non trovato"

        if 'Paese' in campi: profilo['Paese'] = paese_nome # Usa il nome del paese originale

        dati.append(profilo)

    # Ora ritorniamo il DataFrame completo, anche se alcuni IBAN sono "Non trovato"
    # La notifica all'utente avverrà nell'app.py
    return pd.DataFrame(dati)
