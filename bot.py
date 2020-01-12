import json
import requests
import time
import urllib

TOKEN = "645253267:AAG_Z5hCkeJj96NXupLzIcAf9xRGImQUudI"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

KEYWORDS_YES = ["ja", "yes", "jo", "sure", "klar", "sicher"]
KEYWORDS_NO  = ["no", "ne", "nie"]

conversations = {}
current_convo = None

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


def add_convo_data(key, value):
    conversations[chat_id()][key] = value;


def initialize_chat(chat_id, update):
    name = update["from"]["first_name"]
    user = update["from"]["username"]
    user_id = update["from"]["id"]
    conversations[chat_id] = { "id": chat_id, "state": 0, "user_id": user_id, "user": user, "name":  name, "last_message": None }
    return conversations[chat_id]


def respond_all(updates):
    for update in updates["result"]:
        chat_id = update["message"]["chat"]["id"]
        conversation = conversations[chat_id] if chat_id in conversations.keys() else initialize_chat(chat_id, update)
        conversation["last_message": update["message"]["text"]]
        conversate(conversation)


def conversate(convo):
    current_convo = convo

    if state(0):
        send("Hallo")
        send("Hallo")
        send("Hallooooo?")

    if state(1):
        send("Ouh sorry.. min Prozessor isch übertaktet.. Denn schribi amigs chli z'schnell. Also nomal:")
        send("Hallo " + name())

    if state(2):
        send("Findsch s'Tiar cool?")

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

    conversations[chat_id()]["state"] = convstate + 1
    if convstate == 8:
        conversations[chat_id()]["state"] = 0

    current_convo = None


def main():
    last_update_id = None
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