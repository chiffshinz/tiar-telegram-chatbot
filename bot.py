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

KEYWORDS_YES = ["ja", "yes", "jo", "sure", "klar", "sicher"]
KEYWORDS_NO  = ["no", "ne", "nie"]

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
    return "TODO"  

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
        send("aber sonst geht's mir gut. Also nochmal:")
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
            send("schön!")
        if not answer:
            send("ojemine!") #ist das der case, wenn ein nein kommt
        else:
            send("aha i see")

    s += 1
    if state(s):
        send("Upsi, hab vergessen mich vorzustellen!")
        send("Also ich bin äh")
        send("ein Chatbot")
        send("Warte, ich brauche einen Namen, damit das eine richtige normale Konversation ist")
        send("zwischen zwei Menschen äh Instanzen")
        send("Gib mir einen Namen, wie soll ich heissen?")

    s += 1
    if state(s):
        answer = current_convo["last_message"]
        name_self(answer)
        send(name_self())
        send(name_self() + " " + name_self() + " " + name_self())
        send("öhm")
        send("bisschen komischer Name aber okay")
        send("andere nennen mich " + random_self_names() + ", aber bei dir bin ich " + name_self() + ".. Okay?") 

    s += 1
    if state(s):
        answer = yes_or_no()
        if answer == None:
            not_understood()
            return
        if answer:
            send("Cool! Ich finds au cool.")
        if not answer:
            send("Häää.. Komisch")

    s += 1
    if state(s):
        send("Ich bin ebe so in top-down Spaghetti-code gschribe")

    s += 1
    if state(s):
        send("Wie isch din spitzname?")

    s += 1
    if state(s):
        sp = current_convo["last_message"]
        add_convo_data("spitzname", sp)
        send("Söll ich dir also lieber " + spitz() + " sege?")

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

