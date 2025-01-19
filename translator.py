import asyncio
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

#print(asyncio.run(yandex_translate("Les manuels de droit constitutionnel sont très nombreux et variés. Si les questions traitées sont les mêmes, les approches et les doctrines peuvent être profondément différentes. Ces différences s’expliquent : en effet, ce que l’on appelle la science du droit constitutionnel n’est pas seulement une somme de connaissances. C’est aussi un ensemble de problèmes auxquels les réponses les plus diverses peuvent être apportées. La pertinence et la cohérence de ces réponses dépen- dent de la rigueur du raisonnement qui les justifie. Et il est au moins aussi important d’acquérir la maîtrise du raisonnement que de retenir les grands traits des systèmes constitutionnels. L’un des moyens d’y parvenir est de confronter sur chaque question les thèses de plusieurs auteurs. Cette confrontation ne peut cependant être fruc- tueuse que si l’on prend en compte tous les présupposés explicites ou impli- cites des raisonnements. Les plus importants tiennent au langage. Bien des différences doctrinales peuvent s’éclairer et bien des problèmes se dissiper, dès lors qu’on s’aperçoit qu’ils tiennent principalement aux usages linguisti- ques. La maîtrise du raisonnement suppose donc la maîtrise d’un langage et c’est pourquoi, dans la première partie du présent ouvrage, un soin particu- lier a été apporté à la définition des concepts fondamentaux.")))