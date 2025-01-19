from googletrans import Translator

ru_alph = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
fr_alph = set("abcdefghijklmnopqrstuvwxyz")
translator = Translator()

def detect_lang(message:str):
    """
    The function of determining the language of the message based on the frequency of occurrence of letters. 
    Accepts a message in string format and returns a value < zero if the language is French, value > zero if Russian.
    If value = 0, the language is not determined
    """
    letters = {c for c in message}
    return len(letters & ru_alph) - len(letters & fr_alph)


async def translate(message:str)->str:
    res = ""
    if (detect_lang(message)>0):
        res = await translator.translate(message, dest='fr')
    else: 
        res = await translator.translate(message, dest='ru')
    return str(res.text)

