import json
import requests
import time
import urllib

TOKEN = "645253267:AAG_Z5hCkeJj96NXupLzIcAf9xRGImQUudI"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

conversation_state = {}

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


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text + "blabla", chat_id)
    get_url(url)

def ablauf(updates):
    for update in updates["result"]:
        chat = update["message"]["chat"]["id"]
        convstate = 0

        if chat in conversation_state.keys():
            convstate = conversation_state[chat]

        if convstate == 0:
            text = "hallo"
            send_message(text, chat)
            text = "halloooo"
            send_message(text, chat)
            text = "wie heisst du?" 
            send_message(text, chat)


        if convstate == 1:
            name = update["message"]["text"]
            text = "hallo" + name + "!"
            send_message(text, chat)


        conversation_state[chat] = convstate + 1
        if convstate == 2:
            conversation_state[chat] = 0

def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        try:
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                ablauf(updates)
        except KeyError as e:
            continue
        time.sleep(0.5)


if __name__ == '__main__':
    main()