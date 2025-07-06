# generator_script.py

import os
import random
import faker
import pandas as pd
import requests
import json
from faker.providers import address, phone_number, person, date_time, internet, company
# Keep BankProvider import if you still want the class object,
# but you won't add it manually anymore
# from faker.providers.bank import Provider as BankProvider

IBAN_CACHE_FILE = "iban_cache.json"
EXCLUDED_IBAN_FILE = "iban_exclude.json"

def iban_valido(iban):
    url = f"https://openiban.com/validate/{iban}?getBIC=true&validateBankCode=true"
    try:
        # Use a slightly longer timeout just in case the service is slow
        response = requests.get(url, timeout=10) 
        if response.status_code == 200:
            data = response.json()
            return data.get("valid", False)
        else:
            # Handle non-200 responses explicitly
            # print(f"Validation failed for {iban}: Status code {response.status_code}") 
            return False
    except requests.exceptions.RequestException as e:
        # Catch specific request exceptions for better debugging if needed
        # print(f"Validation error for {iban}: {e}")
        return False
    except Exception as e:
        # Catch any other unexpected errors
        # print(f"An unexpected error occurred during validation for {iban}: {e}")
        return False

def carica_cache():
    if os.path.exists(IBAN_CACHE_FILE):
        try:
            with open(IBAN_CACHE_FILE, "r") as f:
                 # Add error handling for empty or invalid JSON
                 content = f.read()
                 if not content:
                     return {}
                 return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading IBAN cache: {e}")
            return {} # Return empty cache on error
    return {}

def salva_cache(cache):
    try:
        with open(IBAN_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4) # Add indent for readability
    except Exception as e:
        print(f"Error saving IBAN cache: {e}")


def carica_esclusi():
    if os.path.exists(EXCLUDED_IBAN_FILE):
        try:
            with open(EXCLUDED_IBAN_FILE, "r") as f:
                # Add error handling for empty or invalid JSON
                content = f.read()
                if not content:
                    return set()
                return set(json.loads(content))
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading excluded IBANs: {e}")
            return set() # Return empty set on error
    return set()

def salva_esclusi(exclude_set):
    try:
        with open(EXCLUDED_IBAN_FILE, "w") as f:
            json.dump(list(exclude_set), f, indent=4) # Add indent for readability
    except Exception as e:
        print(f"Error saving excluded IBANs: {e}")


def ottieni_o_aggiungi_iban(country_code):
    country_code_upper = country_code.upper() # Use a new variable to avoid shadowing input
    cache = carica_cache()
    esclusi = carica_esclusi()

    if country_code_upper not in cache:
        cache[country_code_upper] = []

    if len(cache[country_code_upper]) >= 5:
        salva_cache(cache) # Ensure cache is saved even if we return early
        # Only return from cached IBANs that are NOT excluded
        available_ibans = [iban for iban in cache[country_code_upper] if iban not in esclusi]
        if available_ibans:
             return random.choice(available_ibans)
        else:
             # If all cached IBANs for this country are now excluded, try generating new ones
             cache[country_code_upper] = [] # Clear the cache for this country to force regeneration
             # Continue below to generate new ones

    # Mapping from ISO 2-letter code to Faker locale string
    iso_to_locale = {
        'IT': 'it_IT',
        'FR': 'fr_FR',
        'DE': 'de_DE',
        'LU': 'fr_LU' # Using the same locale as in genera_dati
    }

    locale = iso_to_locale.get(country_code_upper, 'en_US') # Get locale based on country_code

    if locale == 'en_US' and country_code_upper not in iso_to_locale:
         # Handle unsupported country codes explicitly if needed
         print(f"Warning: No specific locale mapped for country code {country_code}. Using en_US which might not support IBAN generation for this country.")
         # Optionally return None or raise an error here if the country is not in your mapping

    tentativi = 0
    # Increase attempts slightly as validation can sometimes fail randomly or service is down
    max_attempts = 100 
    
    while len(cache[country_code_upper]) < 5 and tentativi < max_attempts:
        try:
            # Initialize Faker WITH the specific locale
            fake_temp = faker.Faker(locale=locale)
            # The bank provider is typically auto-loaded with the locale,
            # so we no longer need fake_temp.add_provider(BankProvider)

            # Generate IBAN for the specific country code
            # Use the keyword argument country_code_upper for clarity and robustness
            nuovo_iban = fake_temp.iban(country_code=country_code_upper) 
        except AttributeError:
             # Handle cases where the 'iban' method might not be available for the chosen locale
             print(f"Faker locale {locale} does not support IBAN generation directly or for country code {country_code_upper}. Skipping.")
             tentativi = max_attempts # Exit loop if IBAN generation isn't possible
             continue
        except Exception as e:
            # Catch any other errors during generation
            print(f"Error generating raw IBAN for {country_code_upper} with locale {locale}: {e}")
            tentativi += 1
            continue # Skip this attempt

        if nuovo_iban in cache.get(country_code_upper, []) or nuovo_iban in esclusi:
            # Check against potential existing entries in the cache list *before* validation
            tentativi += 1
            continue

        # Perform external validation
        if iban_valido(nuovo_iban):
            cache[country_code_upper].append(nuovo_iban)
            # It's slightly more efficient to save the cache less frequently,
            # maybe only after the loop or when adding, but saving inside the loop (up to 5 times per country)
            # ensures you don't lose successful generations if the process is interrupted.
            # Let's keep saving inside for robustness in this case.
            salva_cache(cache) 
            # We've found a valid one, we can potentially return early,
            # but the loop continues until 5 are found or attempts run out.
            # Returning here would mean the cache might not reach 5 IBANs.
            # return nuovo_iban # Don't return here if you want to populate the cache up to 5

        tentativi += 1

    # After the loop, check if we have any cached IBANs to return
    if cache.get(country_code_upper):
         # Only return from cached IBANs that are NOT excluded
         available_ibans = [iban for iban in cache[country_code_upper] if iban not in esclusi]
         if available_ibans:
              return random.choice(available_ibans)
         # If the loop finished but no valid/non-excluded IBANs were found/generated
         return "Non trovato" # Or None, depending on desired output

    # If the loop finished and no IBANs were added to the cache for this country
    salva_cache(cache) # Save any changes made during the loop
    return "Non trovato" # Indicates no valid IBAN was found/generated

def escludi_iban(iban):
    esclusi = carica_esclusi()
    cache = carica_cache()

    found_in_cache = False
    for paese_code, lista in cache.items():
        # Create a new list excluding the iban to avoid modifying the list while iterating (though removing works here)
        new_lista = [item for item in lista if item != iban]
        if len(new_lista) < len(lista): # If the iban was found and removed
            cache[paese_code] = new_lista
            found_in_cache = True
            break # Assume an IBAN belongs to only one country cache

    if found_in_cache:
        esclusi.add(iban) # Add to excluded list only if it was in the cache
        salva_cache(cache)
        salva_esclusi(esclusi)
    else:
        # If the IBAN wasn't found in the cache, just add it to the excluded list anyway
        # This prevents attempting to re-generate/use an IBAN that was manually typed and excluded
        esclusi.add(iban)
        salva_esclusi(esclusi)
        print(f"IBAN {iban} not found in cache, added directly to excluded list.")


def genera_dati(paese_nome, n=1, campi=None): # Renamed parameter to avoid confusion
    localizzazioni = {
        'italia': 'it_IT',
        'francia': 'fr_FR',
        'germania': 'de_DE',
        'lussemburgo': 'fr_LU' # Using fr_LU as per your original code
    }
    iso_codes = {
        'italia': 'IT',
        'francia': 'FR',
        'germania': 'DE',
        'lussemburgo': 'LU'
    }

    paese_lower = paese_nome.lower() # Use a new variable name

    if paese_lower not in localizzazioni:
        raise ValueError(f"Paese non valido: {paese_nome}. Scegli tra Italia, Francia, Germania, Lussemburgo.")

    # Initialize Faker with the locale for generating *other* profile data
    fake = faker.Faker(localizzazioni[paese_lower])
    # Providers used here (address, phone, person, date, internet, company) are
    # typically loaded automatically with the locale, so add_provider isn't strictly necessary
    # unless you have custom providers.
    # fake.add_provider(address) # Not needed if locale is set
    # fake.add_provider(phone_number) # Not needed if locale is set
    # ... and so on for standard providers

    dati = []
    for _ in range(n):
        profilo = {}
        # Use .get() for fields that might not be available in all locales (like SSN, VAT)
        # Or handle them with checks as you did. Let's stick to your check method for consistency.
        if 'Nome' in campi: profilo['Nome'] = fake.first_name()
        if 'Cognome' in campi: profilo['Cognome'] = fake.last_name()
        if 'Data di Nascita' in campi:
             # Use date_of_birth from the fake instance initialized with the locale
             profilo['Data di Nascita'] = fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%d/%m/%Y')
        if 'Indirizzo' in campi: profilo['Indirizzo'] = fake.address().replace("\n", ", ")
        if 'Telefono' in campi: profilo['Telefono'] = fake.phone_number()
        if 'Email' in campi: profilo['Email'] = fake.email()
        if 'Codice Fiscale' in campi:
             # Codice Fiscale is specific to Italy, keep your check
             profilo['Codice Fiscale'] = fake.ssn() if paese_lower == 'italia' else 'N/A'
        if 'Partita IVA' in campi:
             # VAT ID provider method might vary by locale or availability
             # Use getattr for safer access
             profilo['Partita IVA'] = getattr(fake, 'vat_id', lambda: 'N/A')() if 'Partita IVA' in campi else 'N/A'
             # Or your original check is also fine: profilo['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
        if 'IBAN' in campi:
            # Pass the correct ISO code to the helper function
            iban = ottieni_o_aggiungi_iban(iso_codes[paese_lower])
            profilo['IBAN'] = iban if iban else "Non trovato" # ottieni_o_aggiungi_iban now returns "Non trovato" or an IBAN

        if 'Paese' in campi: profilo['Paese'] = paese_nome # Use the original name for display

        dati.append(profilo)

    # Filter out profiles where IBAN was requested but not found
    if 'IBAN' in campi:
        dati = [p for p in dati if p.get('IBAN') != "Non trovato"]

    return pd.DataFrame(dati)
