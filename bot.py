import json
import requests
import time
import urllib
import configparser
import sqlite3
import logging
import sys
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

KEYWORDS_YES = ["ja", "yes", "jo", "sure", "klar", "sicher"]
KEYWORDS_NO  = ["no", "ne", "nie"]

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
    print(content)
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

def preferred_name():
    return conversations[chat_id()]

def not_understood():
    send("Das habe ich nicht verstanden...")


def add_convo_data(key, value):
    conversations[chat_id()][key] = value;


def initialize_chat(chat_id, update):
    name = update["message"]["from"]["first_name"]
    user = update["message"]["from"]["username"]
    user_id = update["message"]["from"]["id"]
    conversations[chat_id] = { "id": chat_id, "state": 0, "user_id": user_id, "user": user, "name":  name, "last_message": None }
    return conversations[chat_id]



def respond_all(updates):
    print('updates: ' + str(updates))
    for update in updates["result"]:
        print('update: ' + str(update))
        chat_id = update["message"]["chat"]["id"]
        print('id: ' + str(chat_id))
        conversation = conversations[chat_id] if chat_id in conversations.keys() else initialize_chat(chat_id, update)
        print('conversation: ' + str(conversation))
        conversation["last_message"] = update["message"]["text"]
        print
        print('        convo: ' + str(conversation))
        print
        conversate(conversation)


def conversate(convo):
    global current_convo
    current_convo = convo

    if state(0):
        send("Hallo")
        send("Hallihallo hallohallo")
        send("Heellou")
        send("Uhh sorry.. mein Prozessor ist übertaktet.. Dann schreib ich manchmal bisschen zu schnell. Also nochmal:")
        send("Hallo! Schön bist du da!")
        send("Es gibt eine Regel: Du darfst nur antworten, wenn ich dich etwas frage") #sonst geht springt der bot ja zum nächsten state oder?
        send("Sonst geh ich kaputt") #gibt es ein wort, das mehr stimmt, so ein informatikerwort, evt "crashe ich" oderso?
        send("aber sonst geht's mir gut")
        send("Wie heisst du?") #fehlt hier nicht die Frage nach dem Namen? Wie setze ich diese Variabel fest?

    if state(1):
        #answer = name()
        send("Ahhh " + name() + ". schöner name!")
        send("Schön bist du da, " + name() + "!")
        send("Geht es dir gut? Fit?")

    if state(2):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return #was heisst das? wird die frage dann wiederholt oder wohin returnt das?
        if answer:
            send("schön!")
        if not answer:
            send("ojemine!") #ist das der case, wenn ein nein kommt
        else:
            send("aha i see")

    if state(3):
        send("Upsi, hab vergessen mich vorzustellen!")
        send("Also ich bin äh")
        send("ein Chatbot")
        send("Warte, ich brauche einen Namen, damit das eine richtige normale Konversation ist")
        send("zwischen zwei Menschen äh Instanzen")
        send("Gib mir einen Namen, wie soll ich heissen?")

    if state(4):
        name_chatbot = answer()
        send(name_chatbot)
        send(name_chatbot + " " + name_chatbot + " " + name_chatbot)
        send("öhm")
        send("bisschen komischer Name aber okay")
        send("andere nennen mich " + "last_tree_chatbot_names" + ", aber bei dir bin ich " + chatbot_name) #geht das? also eine methode für die letzen drei chatbot_namen, hab gedacht weil es so ähnliches oben schon gibt, vielleicht geht das

    if state(3):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return
        if answer:
            send("Cool! Ich finds au cool.")
        if not answer:
            send("Häää.. Komisch")

    if state(4):
        send("Ich bin ebe so in top-down Spaghetti-code gschribe")

    if state(5):
        send("Wie isch din spitzname?")

    if state(6):
        add_convo_data("spitzname", answer())
        send("Söll ich dir also lieber " + spitz() + " sege?")

    if state(7):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return
        if answer:
            add_convo_data("preferred_name", spitz())
        if not answer:
            add_convo_data("preferred_name", name())

    if state(8):
        send("Okay, " + preferred_name())

    conversations[chat_id()]["state"] = state() + 1
    if state() > 8:
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

