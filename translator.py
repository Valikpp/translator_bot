from googletrans import Translator
import requests
from dotenv import dotenv_values
import json
import deepl
import os,sys

config = dotenv_values(".env")
API_URL = "https://api-free.deepl.com/v2/"
DEEPL_KEY = config["DEEPL"] 
HEADERS = {
    "Authorization": f"DeepL-Auth-Key {DEEPL_KEY}",
    "Content-Type": "application/json"
}

if os.name == "nt": #If bot is hosted on Windows 
    # Encoding changing to avoid problems with special french symbols  
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

translator = deepl.Translator(DEEPL_KEY)
google_translator = Translator()

ru_alph = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
fr_alph = set("abcdefghijklmnopqrstuvwxyz")

def detect_lang(message:str):
    """
    The function of determining the language of the message based on the frequency of occurrence of letters. 
    Accepts a message in string format and returns a value < zero if the language is French, value > zero if Russian.
    If value = 0, the language is not determined
    """
    letters = {c for c in message}
    return len(letters & ru_alph) - len(letters & fr_alph)


def translate(message:str, glossary_id_ru, glossary_id_fr)->str:
    res = ""
    if (detect_lang(message)>0):
        res = translator.translate_text(source_lang="RU", text=message, target_lang="FR", formality="prefer_more",glossary=glossary_id_ru)
    else: 
        res = translator.translate_text(source_lang="FR", text=message, target_lang="RU", formality="prefer_more",glossary=glossary_id_fr)
    return str(res.text)

def create_glossary(name, source_lang, target_lang, entries):
    ent = ""+entries[0]
    for entry in entries[1:]:
        ent += "\n"+entry
    data = {
        "name": name,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "entries": ent,
        "entries_format": "csv"
    }
    response = requests.post(API_URL + "glossaries", headers=HEADERS, data=json.dumps(data))
    return response.json()

def get_glossary_details(glossary_id):
    response = requests.get(API_URL + f"glossaries/{glossary_id}", headers=HEADERS)
    return response.json()

def list_glossaries():
    response = requests.get(API_URL + "glossaries", headers=HEADERS)
    return response.json()

def get_glossary_entries(glossary_id):
    headers = HEADERS.copy()
    headers["Accept"] = "text/tab-separated-values"
    response = requests.get(API_URL + f"glossaries/{glossary_id}/entries", headers=headers)
    return response.text

def delete_glossary(glossary_id):
    response = requests.delete(API_URL + f"glossaries/{glossary_id}", headers=HEADERS)
    return response.status_code == 204
    
def push_to_glossary(source_lang, dest_lang, entries):
    with open("glossaries.json",'r') as file:
        glossaries = json.load(file)
    glossary = glossaries[f"{source_lang}-{dest_lang}"]
    src, dest = entries
    if len(src)+len(dest)<2:
        return "Error:empty"
    glossary_id = glossary["glossary_id"]
    if (glossary_id != None and glossary_id!=""):
        print("old deleted : ",delete_glossary(glossary_id))
    if (f"{src},{dest}" in glossary["entries"]):
        return "Error:Already exists"
    new_glossary = create_glossary(f"{source_lang}-{dest_lang}",source_lang,dest_lang,glossary["entries"]+[f"{src},{dest}"])
    if new_glossary.get("ready")==True:
        glossary["glossary_id"] = new_glossary.get("glossary_id")
        glossary["entries"].append(f"{src},{dest}")
        with open("glossaries.json",'w') as file:
            json.dump(glossaries,file)
        return glossary["glossary_id"]
    else :
        return "Error:push error"
    
#5df558e7-9620-48a2-a092-0a1c68e3edd4 old id
#print(push_to_glossary('ru','fr',("лопата","pelle")))
# #delete_glossary("ed4cfed6-3d10-43c9-a236-5ee38dd012ff")
#print(push_to_glossary('ru','fr',("дрель", "perceuse")))
#print(push_to_glossary('fr','ru',("pelle","лопата")))
# #delete_glossary("ed4cfed6-3d10-43c9-a236-5ee38dd012ff")
#print(push_to_glossary('ru','fr',("дрель", "perceuse")))
#print(get_glossary_entries("daba8dc0-6bfc-4935-95d0-343441ce7d81"))
#print(list_glossaries())
#glossary = create_glossary("Myglos", "ru", "fr", ["test"])
#print("Created glossary:", glossary)
