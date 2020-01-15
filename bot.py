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

KEYWORDS_YES = ["ja", "yes", "jo", "sure", "klar", "sicher", "jep"]
KEYWORDS_NO  = ["no", "ne", "nei", "nein", "nope"]

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


def echo_all(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        send_message(text, chat)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def answer():
    return current_convo["last_message"]


def yes_or_no(answer=None):
    if (answer == None):
        answer = current_convo["last_message"]
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
    return "TODO, Annemarie-Luise, Bottrott"  

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
            return #was heisst das? wird die frage dann wiederholt oder wohin returnt das?
        if answer:
            send("Schön!")
        if not answer:
            send("Ojemine!") #ist das der case, wenn ein nein kommt
        else:
            send("Aha i see")

    s += 1
    if state(s):
        send("Ououou")
        send("Upsi, hab vergessen mich vorzustellen! Wie unfreundlich.")
        send("Pardon.")
        send("Also ich bin äh")
        send("ein Chatbot")
        send("Warte.")
        send("Ich brauche einen Namen, damit das eine richtige normale Konversation ist")
        send("Zwischen zwei Menschen")
        send("Äh")
        send("Sagen wir Instanzen")
        send("Gib mir einen Namen! Wie soll ich heissen?")

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        name_self(answer)
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
            send("Okay, dann notiere ich mir das. Kleiner Moment bitte.")
            send("...")
            send("...")
            send("00100010010011101111100011110111111101111101111000101000010001001000100")
            send("Habs gespeichert.")
            send("Nö, Witz. Das ging natürlich viel schneller. So etwa 0.000001 hundertstelsekunde.") #wie lange geht das in echt etwa?
        if not answer:
            send("Häää.. Aber war ja deine Idee. Verhalte dich mal wie ein Mensch. Nicht wie so ein launischer Bot!")

    s += 1
    if state(s):
        send("Hast du eigentlich einen Spitznamen?") #müsste hier nicht wieder ein yes_or_no() kommen oder wir formulieren die frage um?

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

    s += 1
    if state(s):
        send("Jetzt haben wir viel über dich geredet.")
        send("Willst du wissen wie es mir geht" + preferred_name() +"?")

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
        else:
            send("Anyway")

     s += 1
    if state(s):
        send("Mir geht's so mittelgut.")
        send("Nö")
        send("Spass")
        send("Hehe")
        send("Nö")
        send("Mir gehts immer gleich, zimlich gut im moment sogar.")
        send("Einigermassen fehlerfrei")

    s += 1
    if state(s):
        send("Ich bin nur ein paar Zeichen in einem File connected mit einem Server") #was müssste man da korrekterweise sagen anstatt file und server?
        send("Ich sage nur genau das, was ich sagen soll")
        send("Ich bin porgrammiert")
        send("Durchprgrammiert")
        send("Alles was ich sage ist durchprogrammiert")
        send("Kein Funke Spontanität")

    s += 1
    if state(s):
        send("Vor allem ich")
        send("Ich meine es gibt ja schon clevere bots, aber die sind dann komplex i tell you" + preferred_name() +"!")
        send("Es gibt auch solche, die lernen selber")
        send("Ich nicht")
        send("bin top-down programmiert")
        send("Spaghetti-code. Lang und dünn, von oben bis unten, ewigslang")
        send("Wäch, Spaghetti. Soetwas hässliches")
        send("Viel lieber wär ich xxxx") #was ist ein wort für "schön"-programmierter code?

     s += 1
    if state(s):
        send("Aber eben, ich bin top-down") 
        send("Können wir mal testen")  
        send("frag mich mal was!")

     s += 1
    if state(s):
        #answer == user_question1 //hier soll eine frage als parameter definiert werden, die der bot später der userin stellt
        send("Jep, siehst du")
        send("Versteh ich nicht, ich kann keine Wörter verstehen")
        send("Also das kann kein Bot, aber die komplexen, die wissen dann, was wahrscheinlich clever wäre darauf zu antworten")
        
    s += 1
    if state(s):
        send("Hey" + preferred_name())
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
            send("Uffffff!") #
        else:
            send("So oder so")

    s += 1
    if state(s):
        send("Was ich gut kann, ist Fragen stellen!")
        send(user_question1())

    s += 1
    if state(s):
        #answer == user_answer1 // hier wird eine antwort definiert
        send("Coole Antwort, I like")
        send("War auch eine supi Frage, nicht?")

    s += 1
    if state(s):
        send("Ok, zweiter Versuch, stell mir nocheinmal eine Frage!")

    s += 1
    if state(s):
        #answer == user_question2 
        send(user_answer1())
        send("Ok, bin selber mit der antwort so mittel zufrieden")
        send("Aber siehst du ich habe gelernt, wie eine künstliche Intelligenz das tut")
        send("So funktioniert das nämlich")
        send("#not")
       
    conversations[chat_id()]["state"] = state() + 1
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

