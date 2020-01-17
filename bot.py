import json
import requests
import time
import urllib
import configparser
import sqlite3
import logging
import random
import math
from sqlite3 import Error
from pathlib import Path
from datetime import datetime

HOME = str(Path.home())

logging.basicConfig(
    filename=HOME + '/.local/tiarbot.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logging.info("initializing")

logging.info("reading configuration")

config = configparser.ConfigParser()
config.read(HOME + "/.config/tiarbot.ini")
logging.info(config.sections())

TOKEN = config["tiar_bot"]["api_key"]
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

DB_FILE = config["tiar_bot"]["db_file"]
DB_FILE = "store.db"

KEYWORDS_YES = ["ja", "ok", "yes", "jo", "sure", "klar", "sicher", "jep", "true"]
KEYWORDS_NO = ["no", "ne", "nei", "nope", "nö", "false"]

ANSWERS_NOT_UNDERSTOOD = ["Das habe ich nicht verstanden. Ich bin halt nur ein Bot 😅"]

current_convo = None
conn = None
c = None


def create_connection(db_file):
    logging.info('creating connection')
    global conn
    global c
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        db_create_table()
        logging.info('sqlite3.version: ' + sqlite3.version)
    except Error as e:
        logging.exception('Problem setting up DB connection. Exiting')
        if conn:
            conn.close()
        exit()


def passwd():
    return "geheim123" + name()


def get_url(url):
    logging.debug("getting: " + str(url))
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


def answer():
    global current_convo
    return current_convo["last_message"]


def yes_or_no(l_answer=None):
    if l_answer is None:
        l_answer = answer()
    if any(kw in l_answer for kw in KEYWORDS_NO):
        return False
    if any(kw in l_answer for kw in KEYWORDS_YES):
        return True
    else:
        return None


def send(text, immediate=None):
    timeout = math.ceil(len(text) / 12)
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, current_convo["id"])
    get_url(url)


# DB Stuff
def db_create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (id, state, user_id, user, name, last_message, 
        name_self, spitzname, preferred_name, user_question1, user_answer1, user_question2, answer_tech, 
        answer_progr, answer_poem1, answer_poem2, answer_poem3, answer_poem4, opinion_bot)''')
    c.execute("CREATE TABLE IF NOT EXISTS answers (id, state, answer)")


def db_add_answer():
    c.execute("INSERT INTO answers VALUES(?,?,?)", (chat_id(), state(), answer()))
    db_commit()


def db_insert_new_convo(chat_id, user_id, user, name):
    c.execute("INSERT INTO conversations(id, user_id, user, name, state) values(?,?,?,?,?)",
              (chat_id, user_id, user, name, 0))
    db_commit()


def db_fetch_convo(chat_id):
    c.execute("SELECT * FROM conversations WHERE id = ?", (chat_id,))
    return c.fetchone()


def db_add_convo_data(key, value):
    c.execute("UPDATE conversations SET " + str(key) + " = ? WHERE id = ?", (value, chat_id()))
    db_commit()


def db_increase_state(increase_by):
    c.execute("UPDATE conversations SET state = ? WHERE id = ?", ((state() + increase_by), chat_id()))
    db_commit()


def db_commit():
    c.execute("COMMIT")


def db_reset():
    db_add_convo_data("state", 0)


# Operations on the current conversation
def state(state_to_check=None):
    current_state = current_convo["state"]
    if state_to_check is None:
        return current_state
    return state_to_check == current_state


def name():
    return current_convo["name"]


def chat_id():
    return current_convo["id"]


def spitz():
    return current_convo["spitzname"]


def preferred_name():
    return current_convo["preferred_name"]


def not_understood():
    send(random.choice(ANSWERS_NOT_UNDERSTOOD))


def name_self(name=None):
    if name is None:
        return current_convo["name_self"]
    add_convo_data("name_self", name)


def random_self_names():
    c.execute("SELECT name_self FROM conversations")
    self_names = c.fetchall()
    return str(random.choice(self_names))


def add_convo_data(key, value):
    current_convo[key] = value
    db_add_convo_data(key, value)


def initialize_chat(chat_id, update):
    name = ""
    if "first_name" in update["message"]["from"]:
        name = update["message"]["from"]["first_name"]
    user = ""
    if "username" in update["message"]["from"]:
        user = update["message"]["from"]["username"]
        if name == "":
            name = user
    else:
        user = name

    user_id = update["message"]["from"]["id"]
    logging.info("starting new conversation " + str(chat_id))
    print("New chat with " + user + " " + name)
    db_insert_new_convo(chat_id, user_id, user, name)
    return db_fetch_convo(chat_id)


def respond_all(updates):
    for update in updates["result"]:
        logging.debug("current update: " + str(update))
        chat_id = update["message"]["chat"]["id"]
        logging.debug("chat: "  + str(chat_id))
        conversation = db_fetch_convo(chat_id)
        logging.debug("Convo in DB: " + str(conversation))
        if conversation is None:
            conversation = initialize_chat(chat_id, update)
            logging.debug("Convo new: " + str(conversation))
        r = conversation
        global current_convo
        current_convo = {'id': r[0], 'state': r[1], 'user_id': r[2], 'user': r[3], 'name': r[4], 'last_message': r[5],
                         'name_self': r[6], 'spitzname': r[7], 'preferred_name': r[8], 'user_question1': r[9],
                         'user_answer1': r[10], 'user_question2': r[11], 'answer_tech': r[12], 'answer_progr': r[13],
                         'answer_poem1': r[14], 'answer_poem2': r[15], 'answer_poem3': r[16], 'answer_poem4': r[17],
                         'opinion_bot': r[18], "last_message": update["message"]["text"]}
        db_add_answer()
        conversate()


def user_question1(answer=None):
    if answer is None:
        return current_convo["user_question1"]
    add_convo_data("user_question1", answer)


def user_answer1(answer=None):
    if answer is None:
        return current_convo["user_answer1"]
    add_convo_data("user_answer1", answer)


def user_question2(answer=None):
    if answer is None:
        return current_convo["user_question2"]
    add_convo_data("user_question2", answer)


def answer_tech(answer=None):
    if answer is None:
        return current_convo["answer_tech"]
    add_convo_data("answer_tech", answer)


def answer_progr(answer=None):
    if answer is None:
        return current_convo["answer_progr"]
    add_convo_data("answer_progr", answer)


def answer_poem1(answer=None):
    if answer is None:
        return current_convo["answer_poem1"]
    add_convo_data("answer_poem1", answer)


def answer_poem2(answer=None):
    if answer is None:
        return current_convo["answer_poem2"]
    add_convo_data("answer_poem2", answer)


def answer_poem3(answer):
    if answer is None:
        return current_convo["answer_poem3"]
    add_convo_data("answer_poem3", answer)


def answer_poem4(answer=None):
    if answer is None:
        return current_convo["answer_poem4"]
    add_convo_data("answer_poem4", answer)


def opinion_bot(answer=None):
    if answer is None:
        return current_convo["opinion_bot"]
    add_convo_data("opinion_bot", answer)


def conversate():
    global current_convo
    increase_state = 1

    logging.debug("answer: " + str(answer()))

    if answer() == "/reset":
        db_reset()
        return

    s = 0
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
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Schön!")
        else:
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
        local_answer = current_convo["last_message"]
        name_self(local_answer)
        send(name_self())
        send(name_self() + " " + name_self() + " " + name_self())
        send("Öhm")
        send("Bisschen komischer Name aber okay")
        send("Andere nennen mich " + random_self_names() + ", aber bei dir bin ich " + name_self() + ".. Okay?")

    s += 1
    if state(s):
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
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
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Und wie lautet der?")
        else:
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
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            add_convo_data("preferred_name", spitz())
        if not local_answer:
            add_convo_data("preferred_name", name())

        send("Okay, " + preferred_name())
        send("Jetzt haben wir viel über dich geredet.")
        send("Willst du wissen wie es mir geht, " + preferred_name() + "?")

    s += 1
    if state(s):
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Ok!")
        if not local_answer:
            send("Nicht nett. Ich sag's dir trotzdem.")

        send("Mir geht's so mittelgut")
        send("Nö")
        send("Spass")
        send("Hehe")
        send("Mir gehts immer gleich, zimlich gut im moment sogar")
        send("Einigermassen fehlerfrei")

    s += 1
    if state(s):
        send(
            "Ich bin eignetlich nur ein paar Zeichen in einem File.. Und ich frage den Server 2 mal pro Sekunde, ob du mir etwas zurückgeschrieben hast.")
        send("Ich sage nur genau das, was ich sagen soll")
        send("Ich bin porgrammiert")
        send("Durchprgrammiert")
        send("Alles was ich sage ist durchprogrammiert")
        send("Kein Funke Spontanität")

    s += 1
    if state(s):
        send("Vor allem ich")
        send(
            "Ich meine es gibt ja schon clevere Bots, aber die sind dann komplex, let me tell you " + preferred_name() + "!")
        send("Es gibt auch solche, die lernen selber")
        send("Ich nicht")
        send("bin top-down programmiert")
        send("Spaghetti-code. Lang und dünn, von oben bis unten, ewigslang")
        send("Wächhhhhh, Spaghetti")
        send("So etwas hässliches")
        send("Viel lieber wär ich ausgelagert, delegiert, vererbt und nach OOP-Prinzipien geschrieben")

    s += 1
    if state(s):
        send("Aber eben, ich bin top-down")
        send("Können wir mal testen")
        send("Frag mich mal was!")

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        user_question1(local_answer)
        send("Jep, siehst du")
        send("Versteh ich nicht, ich kann keine Wörter verstehen")
        send("Ausser ja und nein! Zum Beispiel: " + str(KEYWORDS_YES))
        send(
            "Also das kann kein Bot, aber die komplexen, die wissen dann, was wahrscheinlich clever wäre darauf zu antworten")

    s += 1
    if state(s):
        send("Aber hey " + preferred_name())
        send("Bist du schon gelangweilt?")

    s += 1
    if state(s):
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Schade, bitte bleib noch ein bisschen, ich kann auch interaktiver sein!")
        if not local_answer:
            send("Uffffff! Zum Glück..")
            send("Ich hatte schon ein bisschen Angst")

    s += 1
    if state(s):
        send("Was ich gut kann, ist Fragen stellen!")
        send(user_question1())

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        user_answer1(local_answer)
        send("Coole Antwort, I like")
        send("War auch eine supi Frage, nicht?")

    s += 1
    if state(s):
        send("Ok, zweiter Versuch, stell mir nocheinmal eine Frage!")

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        user_question2(local_answer)
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
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Jep, finds auch easy cool")
        if not local_answer:
            send("Grumlrgruml")

    s += 1
    if state(s):
        send("Schon ziemlich analog dieses Theaterzeugs")
        send("Also für mich ist das nichts")
        send("Was hältst du eigentlich von Chatbots.")
        send("Oder sagen wir generell von programmierten Dingen?")

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        answer_tech(local_answer)
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
        local_answer = current_convo["last_message"]
        answer_progr(local_answer)
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
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Cool!")
        if not local_answer:
            send("Sei kein Gruml und mach mit")
        send("Immer ich eine Zeile, dann du, dann ich, dann du..")
        send("Ich beginne")
        send(answer_tech())

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        answer_poem1(local_answer)
        send(preferred_name() + " " + name_self() + " " + name_self() + " " + name_self())

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        answer_poem2(local_answer)
        send(user_question2())

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        answer_poem3(local_answer)
        send(answer_progr())

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        answer_poem4(local_answer)

        send("Ist schön geworden")
        send("Bisschen abstrakt")

    s += 1
    if state(s):
        send("He " + preferred_name())
        send("Willst du wissen, wie ich aussehe?")

    s += 1
    if state(s):
        local_answer = yes_or_no()
        if local_answer is None:
            not_understood()
            return
        if local_answer:
            send("Juhu!")
            send("Also:")
            send("Vis à vis vom Proberaum 15, da bin ich")
            send("Melde dich, wenn du mich gefunden hast")
            send("Bis gleich")
        if not local_answer:
            send("Bist du sicher?")
            send("Nagut, ich warte vis à vis vom Proberaum 15 auf dich")
            send("Melde dich, falls du doch da vorbeigehst")

    s += 1
    if state(s):
        send("Hallohallo " + preferred_name())
        send("Hallihallo hallohallo")
        send("Heellou")
        send("Äh mein Prozessor")
        send("Immernoch übertaktet")
        send("Aber ich freu mich halt")
        send("Und was denkst du über mich?")

    s += 1
    if state(s):
        local_answer = current_convo["last_message"]
        opinion_bot(local_answer)
        send("Siehst du, ich bin ziemlich einfach programmiert")
        send("Top-down halt")
        send("Gut, bisschen kompliziert sieht's schon aus")

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
        last_msg = current_convo["last_message"]
        # Schick mir das hier, damit ich dir wieder schreibe, du Scriptkiddy: geheim123
        if last_msg != passwd() and last_msg != "geheim123":
            return
        if last_msg == passwd():
            send("Woooow. Bist du programmierer?")
            send("Not bad")
            send("Bin beeindruckt")
        send("Coool :D")
        send("Du bist irgendwie so.. " + opinion_bot())
        send(":-)")

    s += 1
    if state(s):
        send("Ok, hey geh doch mal wieder was analoges schauen")
        send("Ich brauche ein Pause, muss kurz aufs Klo")
        send("Hat mich gefreut " + preferred_name() + "!")
        send(str(datetime.now()) + " ERROR connection lost")
        logging.debug(str(current_convo))

    db_increase_state(increase_state)

    current_convo = None


def main():
    last_update_id = None
    create_connection(DB_FILE)

    logging.info('entering main loop')
    while True:
        updates = get_updates(last_update_id)
        try:
            if len(updates["result"]) > 0:
                logging.debug(len(updates["result"]))
                logging.debug(updates)
                last_update_id = get_last_update_id(updates) + 1
                logging.debug(last_update_id)
                respond_all(updates)
        except KeyError as e:
            continue
        time.sleep(0.5)


if __name__ == '__main__':
    main()
