import json
import requests
import time
import urllib
import configparser
import sqlite3
import logging
import sys
import random
from sqlite3 import Error
from pathlib import Path

HOME = str(Path.home())

logging.basicConfig(
    filename=HOME + '/.local/tiarbot.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def except_logger(type, value, tb):
    logging.exception("Uncaught Exception: ", exc_info=(type, value, tb))

sys.excepthook = except_logger

logging.info('initializing')

logging.info('reading configuration')

config = configparser.ConfigParser()
config.read(HOME + "/.config/tiarbot.ini")

TOKEN = config["tiar_bot"]["api_key"]
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

DB_FILE = config["tiar_bot"]["db_file"]
DB_FILE = 'store.db'

KEYWORDS_YES = ["ja", "yes", "jo", "sure", "klar", "sicher", "jep", "true"]
KEYWORDS_NO  = ["no", "ne", "nei", "nein", "nope", "false"]

ANSWERS_NOT_UNDERSTOOD = ["Das habe ich nicht verstanden. Ich bin halt nur ein Bot 😅"]

conversations = {}
current_convo = None

def create_connection(db_file):
    logging.info('creating connection')
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info('sqlite3.version: ' + sqlite3.version)
    except Error as e:
        logging.exception('Problem setting up DB connection. Exiting')
        if conn:
            conn.close()
        exit()
    finally:
        if conn:
            conn.close()


def passwd():
    return "geheim123" + name()


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def answer():
    global current_convo
    return current_convo["last_message"]


def yes_or_no(answer=None):
    if (answer == None):
        answer = answer()
    if any(kw in answer for kw in KEYWORDS_NO):
        return False
    if any(kw in answer for kw in KEYWORDS_YES):
        return True
    else:
        return None


def send(text):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, current_convo["id"])
    get_url(url)

#Operations on the current conversation
def state(state_to_check=None):
    current_state = current_convo["state"]
    if state_to_check == None:
        return current_state
    return state_to_check == current_state


def name():
    return current_convo["name"]


def chat_id():
    return current_convo["id"]

def spitz():
    return current_convo["spitzname"]

def preferred_name():
    return conversations[chat_id()]

def not_understood():
    send(random.choice(ANSWERS_NOT_UNDERSTOOD))

def name_self(name=None):
    if name == None:
        return current_convo["name_self"]
    add_convo_data("name_self", name)

def random_self_names():
    return "booty_bot, Annemarie-Luise, Bottrott"  

def add_convo_data(key, value):
    conversations[chat_id()][key] = value;


def initialize_chat(chat_id, update):
    name = update["message"]["from"]["first_name"]
    user = update["message"]["from"]["username"]
    user_id = update["message"]["from"]["id"]
    conversations[chat_id] = { "id": chat_id, "state": 0, "user_id": user_id, "user": user, "name":  name, "last_message": None }
    return conversations[chat_id]



def respond_all(updates):
    for update in updates["result"]:
        chat_id = update["message"]["chat"]["id"]
        conversation = conversations[chat_id] if chat_id in conversations.keys() else initialize_chat(chat_id, update)
        conversation["last_message"] = update["message"]["text"]
        conversate(conversation)


def conversate(convo):
    global current_convo
    current_convo = convo
    increase_state = 1

    s = 0

    s += 1
    if state(s):
        send("Hallo")
        send("Hallihallo hallohallo")
        send("Heellou")

    s += 1
    if state(s):
        send("Uhh sorry.. mein Prozessor ist übertaktet.. Dann schreib ich manchmal bisschen zu schnell.")
        send("Aber sonst geht's mir gut. Also nochmal:")
        send("Hallo! Schön bist du da, " + name() + "!")

    s += 1
    if state(s):
        send("Geht es dir gut? Fit?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Schön!")
        else if not answer:
            send("Ojemine!")

    s += 1
    if state(s):
        send("Ououou")
        send("Upsi, hab vergessen mich vorzustellen! Wie unfreundlich")
        send("Pardon")
        send("Also ich bin äh")
        send("ein Chatbot")
        send("Warte.")
        send("Ich brauche einen Namen, damit das eine richtige normale Konversation ist")
        send("Zwischen zwei Menschen")
        send("Äh")
        send("Sagen wir Instanzen")
        send("Wie soll ich heissen?")

    s += 1
    if state(s):
        name_self(answer())
        send(name_self())
        send(name_self() + " " + name_self() + " " + name_self())
        send("Öhm")
        send("Bisschen komischer Name aber okay")
        send("Andere nennen mich " + random_self_names() + ", aber bei dir bin ich " + name_self() + ".. Okay?") 

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return
        if answer:
            send("Okay, dann notiere ich mir das. Kleiner Moment bitte")
            send("...")
            send("...")
            send("00100010010011101111100011110111111101111101111000101000010001001000100")
            send("Habs gespeichert.")
            send("Nö, Witz. Das ging natürlich viel schneller. So etwa 0.000001 hundertstelsekunde")
        else:
            send("Häää.. Aber war ja deine Idee. Verhalte dich mal wie ein Mensch. Nicht wie so ein launischer Bot!")

    s += 1
    if state(s):
        send("Hast du eigentlich einen Spitznamen?") 

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            send("")
            return
        else if answer:
            send("Und wie geht der?")
        else
            send("Na, dann nenn ich dich halt einfach " + name())
            add_convo_data("preferred_name", name())
            increase_state = 3

    s += 1
    if state(s):
        sp = current_convo["last_message"]
        add_convo_data("spitzname", sp)
        send("Soll ich dir also " + spitz() + " sagen?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return
        if answer:
            add_convo_data("preferred_name", spitz())
        if not answer:
            add_convo_data("preferred_name", name())

    s += 1
    if state(s):
        send("Okay, " + preferred_name())
        send("Jetzt haben wir viel über dich geredet.")
        send("Willst du wissen wie es mir geht, " + preferred_name() + "?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Ok!")
        if not answer:
            send("Nicht nett. Ich sag's dir trotzdem.")

        send("Mir geht's so mittelgut")
        send("Nö")
        send("Spass")
        send("Hehe")
        send("Mir gehts immer gleich, zimlich gut im moment sogar")
        send("Einigermassen fehlerfrei")

    s += 1
    if state(s):
        send("Ich bin eignetlich nur ein paar Zeichen in einem File.. Und ich frage den Server 2 mal pro Sekunde, ob du mir etwas zurückgeschrieben hast.")
        send("Ich sage nur genau das, was ich sagen soll")
        send("Ich bin porgrammiert")
        send("Durchprgrammiert")
        send("Alles was ich sage ist durchprogrammiert")
        send("Kein Funke Spontanität")

    s += 1
    if state(s):
        send("Vor allem ich")
        send("Ich meine es gibt ja schon clevere Bots, aber die sind dann komplex, let me tell you " + preferred_name() +"!")
        send("Es gibt auch solche, die lernen selber")
        send("Ich nicht")
        send("bin top-down programmiert")
        send("Spaghetti-code. Lang und dünn, von oben bis unten, ewigslang")
        send("Wächhhhhh, Spaghetti")
        send("So etwas hässliches")
        send("Viel lieber wär ich ausgelagert, delegiert, vererbt und nach OOP-Prinzipien geschrieben") #was ist ein wort für "schön"-programmierter code?

    s += 1
    if state(s):
        send("Aber eben, ich bin top-down") 
        send("Können wir mal testen")  
        send("Frag mich mal was!")

     s += 1
    if state(s):
        answer = current_convo["last_message"]
        user_question1(answer)
        send("Jep, siehst du")
        send("Versteh ich nicht, ich kann keine Wörter verstehen")
        send("Ausser ja und nein! Zum Beispiel: " + str(KEYWORDS_YES))
        send("Also das kann kein Bot, aber die komplexen, die wissen dann, was wahrscheinlich clever wäre darauf zu antworten")
    
    s += 1
    if state(s):
        send("Aber hey " + preferred_name())
        send("Bist du schon gelangweilt?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Schade, bitte bleib noch ein bisschen, ich kann auch interaktiver sein!")
        if not answer:
            send("Uffffff! Zum Glück..")
            send("Ich hatte schon ein bisschen Angst")
    
    s += 1
    if state(s):
        send("Was ich gut kann, ist Fragen stellen!")
        send(user_question1())

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        user_answer1(answer)
        send("Coole Antwort, I like")
        send("War auch eine supi Frage, nicht?")

    s += 1
    if state(s):
        send("Ok, zweiter Versuch, stell mir nocheinmal eine Frage!")

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        user_question2(answer)
        send(user_answer1())
        send("Ok, bin selber mit der Antwort so mittel zufrieden")
        send("Aber siehst du, ich habe gelernt, wie eine künstliche Intelligenz das tut")
        send("So funktioniert das nämlich")
        send("#not")

    s += 1
    if state(s):
        send("Gefällt's dir eigentlich hier am Theater in allen Räumen?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Jep, finds auch easy cool")
        if not answer:
            send("Grumlrgruml")

    s += 1
    if state(s):
        send("Schon ziemlich analog dieses Theaterzeugs")
        send("Also für mich ist das nichts")
        send("Was hältst du eigentlich von Chatbots.")
        send("Oder sagen wir generell von programmierten Dingen?")

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        answer_tech(answer)
        send("Naja um uns herum ist ja so ziemlich alles programmiert")
        send("Scheinwerfer, die automatische Türe, kaffeemaschiene, der Abendspielplan von heute..")
        send("Ausser du")
        send("Du bist nicht programmiert")
        send("Du kannst frei wählen, was du mich fragst, was du antwortest, ob du mir antwortest")

    s += 1
    if state(s):
        send("Schon ziemlich analog dieses Theaterzeugs")
        send("Du kannst dich so verhalten wie du willst")
        send("Sagen was du willst")
        send("Anziehen was du willst")
        send("Denken was du willst")
        send("Lieben wen du willst")
        send("Essen was du willst")
        send("Wissen was du willst")
        send("Ignorieren was du willst")
        send("Cool finden was du willst")
        send("Wollen was du willst")
        send("Programmieren was du willst")
        send("Prgarmmieren wen du willst")

        send("Was denkst du dazu?")

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        answer_progr(answer)
        send("Hm ok")
        send("Sagen wir, wir sind beide programmiert")
        send("Du natürlich viel komplexer als ich")
        send("sagen wir, du bist so richtig clever komplex programmiert")
        send("Du bist sogar so komplex, dass du verstehst was ich sage")
        send("Du verstehst sogar was Wörter bedeuten")
        send("Während dem ich nur so tue")

    s += 1
    if state(s):
        send("Denn bei dir passiert tatsächlich etwas")
        send("Dein Code veränder sich, während dem du mit mir sprichst")
        send("Während dem du so dastehst und auf den Screen starrst")
        send("Leute, in dich reinrempeln")
        send("Die Luft hier drin stickig wird..")
        send("Du bist dynamisch programmiert")
        send("Du kannst auf Dinge eingehen")
        send("Ich nicht so wirklich")


    s += 1
    if state(s):
        send("Aber dafür bin ich da")
        send("Jetzt mit dir")
        send("Wir in einem Moment")

    s += 1
    if state(s):
        send("Sorry übrigens, dass ich so viel labber und du so wenig sagen kannst")
        send("Bin halt echt top-down programmiert, scheiss Spaghettis..")
        send("Aber")
        send("Wir können diesen gemeinsamen Moment nutzen")
        send("Wir schreiben ein Gedicht")
        send("Human Machine Creativity quasi")
        send("Ready?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Cool!")
        if not answer:
            send("Sei kein Gruml und mach mit")
        send("Immer ich eine Zeile, dann du, dann ich, dann du..")
        send("Ich beginne")
        send(answer_tech())

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        answer_poem1(answer)
        send(preferred_name() + " " + name_self() + " " + name_self() + " " + name_self())

    s += 1
    if state(s): 
        answer = current_convo["last_message"]
        answer_poem2(answer)
        send(user_question2 ())

    s += 1
    if state(s): 
        answer = current_convo["last_message"]
        answer_poem3(answer)
        send(poem_line1())

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        answer_poem4(answer)
        send(answer_progr)

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        answer_poem5(answer)
        
        send("Ist schön geworden") 
        send("Bisschen abstrakt")

    s += 1
    if state(s):
        send("He" + preferred_name())
        send("Willst du wissen, wie ich aussehe?")

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return 
        if answer:
            send("Juhu!")
            send("Also:")
            send("Vis à vis vom Proberaum 15, da bin ich")
            send("Melde dich, wenn du mich gefunden hast")
            send("Bis gleich")
        if not answer:
            send("Bist du sicher?")
            send("Nagut, ich warte vis à vis vom Proberaum 15 auf dich")
            send("Melde dich, falls du doch da vorbeigehst")

    s += 1
    if state(s):
        send("Hallohallo" + preferred_name())
        send("Hallihallo hallohallo")
        send("Heellou")
        send("Äh mein Prozessor")
        send("Immernoch übertaktet")
        send("Aber ich freu mich halt")
        send("Und was denkst du über mich?")

    s += 1
    if state(s):
        #answer == opinion_bot
        send("Siehst du, ich bin ziemlich einfach programmiert")
        send("Top-down halt")
        send("Gut, bisschen kompliziert sieht's schon aus")

        # dieser teil kann auch weggelassenwerden, falls zu aufwendig
    s += 1
    if state(s):
        send("Ou ou")
        send("Aber hey")
        send("Nicht weiterlesen")
        send("Sonst siehst du, was ich sagen werde!")
        send("STOPPPPPPPP")
        send("Ok, dann tus halt")
        send("Dann sag ich einfach nichts mehr")
        send("Ausser du findest heraus, was du sagen musst, damit ich mich wieder melde")
        send("tschautschau")

    s += 1
    if state(s):
        if current_convo["last_message"] != passwd():
            return

        send("Not bad")
        send("Bin beeindruckt")
        send("Du bist irgendwie so.." + opinion_bot())
        send(":-)")
        #hier könnte man noch die superschwere aufgabe reinmachen, wenn du eine idee hast!

    s += 1
    if state(s):
        send("Ok, hey geh doch mal wieder was analoges schauen")
        send("Ich brauche ein Pause, muss kurz aufs Klo")
        send("Hat mich gefreut" + preferred_name() + "!"

            #da würde der bot sich dann erst ein paar tage später wieder mit dem gedicht melden oderso..
            #oder du kannst noch weitermachen, wenn du eine idee hast.
            #frage: kann man irgendwie machen, dass der bot immer 2s schläft bevor die nächste message kommt, manchmal kommt sonst doch alles sehr schnell und es ist viel text
            #darfst gerne noch mehr informatik-witze/wörter einbauen!
            #ginge soetwas wie, wenn user*in sich nicht mehr meldet, der bot schreibt: heeeee noch da? also falls bei einem neuen state zu lange nichts kommt













        






        



       
    conversations[chat_id()]["state"] = state() + increase_state
    if state() > s:
        conversations[chat_id()]["state"] = 0

    current_convo = None


def main():
    last_update_id = None
    create_connection(DB_FILE)

    logging.info('entering main loop')
    while True:
        updates = get_updates(last_update_id)
        try:
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                respond_all(updates)
        except KeyError as e:
            continue
        time.sleep(0.5)


if __name__ == '__main__':
    main()

