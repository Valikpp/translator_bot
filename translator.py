from googletrans import Translator
import requests
from dotenv import dotenv_values
import deepl
import os,sys

config = dotenv_values(".env")

if os.name == "nt": #If bot is hosted on Windows 
    # Encoding changing to avoid problems with special french symbols  
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

translator = deepl.Translator(config["DEEPL"])

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


def translate(message:str)->str:
    res = ""
    if (detect_lang(message)>0):
        res = translator.translate_text(source_lang="RU", text=message, target_lang="FR", formality="prefer_more")
    else: 
        res = translator.translate_text(source_lang="FR", text=message, target_lang="RU", formality="prefer_more")
    if res.status == 456:
        if (detect_lang(message)>0):
            res = translator.translate(message, dest='fr')
        else: 
            res = translator.translate(message, dest='ru')
    return str(res.text)

# def create_glossary(couple:tuple):
#     headers = {
#         "Host" : "https://api.deepl.com",
#         "Authorization": f"DeepL-Auth-Key {config['DEEPL']}",
#         "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
#         "Content-Type": "application/json"
#     }
#     src,dst = couple
#     string_couple = src+"\t"+dst
#     content = {"name":"Fr-Ru special glossary","source_lang":"fr","target_lang":"ru","entries":string_couple,"entries_format":"tsv"}
#     res = requests.get(headers=headers, url="https://api.deepl.com/v2/glossaries",json=content)
#     print(res.status_code)

#create_glossary(("Perceuse","Дрель"))