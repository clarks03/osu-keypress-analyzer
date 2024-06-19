import requests
import lzma
import base64
import matplotlib.pyplot as plt
from utils import *
import sys
from dotenv import load_dotenv
import os
import time

load_dotenv()
# API_KEY = os.getenv("API_KEY")
# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
API_KEY = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

def get_token():
    """Returns the Authorization token.
    """

    # Getting token
    get_token = "https://osu.ppy.sh/oauth/token"

    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "public"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token = requests.post(get_token, headers=headers, data=params)
    return token.json()["access_token"]


def make_request(url: str, token: str, params: dict={}):
    """Makes a request to osu!'s API (v2).
    """
    base_url = "https://osu.ppy.sh/api/v2/"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    return requests.get(f"{base_url}{url}", headers=headers, json=params)


def fetch_user_replay_ids(uid: str, token: str):
    """Gets and returns user's top 100 score replay IDs (if the replay is saved).
    """
    all_scores = make_request(f"users/{uid}/scores/best", token, params={"limit": 100}).json()

    # In each ID, I also want to store the username, the map artist and name (romanized) and difficulty
    ids = []
    for score in all_scores:
        # print(score)
        if score["replay"]:
            # ids[score["beatmap"]["id"]] = score["id"]
            current_score = {}
            current_score["id"] = score["id"]
            current_score["artist"] = score["beatmapset"]["artist"]
            current_score["title"] = score["beatmapset"]["title"]
            current_score["difficulty"] = score["beatmap"]["version"]
            current_score["user"] = score["user"]["username"]
            ids.append(current_score)
            # ids.append(score["id"])

    return ids


def get_lzma_from_id(score_id: str, api_key: str):
    """Gets and returns the LZMA compressed replay data from a replay with id <id>.
    """
    url = "https://osu.ppy.sh/api/get_replay"

    url = f"{url}?k={api_key}&s={score_id}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # "Authorization": f"Bearer {token}"
    }

    return requests.get(url, headers=headers)


def keypress_from_lzma(lzma_str, is_base64: bool=False, keypress_durations: dict={}):
    """Determines keypress durations given lzma replay data.
    Graphs them nicely :3
    """

    # Extra Base64 stuff (thanks to apiv1!)
    if is_base64:
        lzma_str = base64.b64decode(lzma_str)
    
    # Decompressing the LZMA stream
    decompressed_data = lzma.decompress(lzma_str).decode("utf-8")

    # Converting the string to a list of events
    events = decompressed_data.split(",")[:-2]

    # keypress_durations = {}
    key1_pressed = False
    key2_pressed = False
    key1_keypress_duration = 0
    key2_keypress_duration = 0
    for event in events:
        event = event.split("|") 
        # If a key is being pressed (key1)
        if (int(event[3]) & 0b00100) != 0:
            # If this is the first event where the key is pressed
            if not key1_pressed:
                key1_pressed = True
            else:
                key1_keypress_duration += int(event[0])
        # If a key is being pressed (key2)
        elif (int(event[3]) & 0b01000) != 0: 
            # If this is the first event where the key is pressed
            if not key2_pressed:
                key2_pressed = True
            else:
                key2_keypress_duration += int(event[0])
        # If no keys are being pressed
        else:
            # Checking if key1 was held up until this point
            if key1_pressed:
                key1_keypress_duration += int(event[0])
                if "K1" not in keypress_durations:
                    keypress_durations["K1"] = [key1_keypress_duration]
                else:
                    keypress_durations["K1"].append(key1_keypress_duration)
                key1_keypress_duration = 0
                key1_pressed = False

            # Checking if key2 was held up until this point
            if key2_pressed:
                key2_keypress_duration += int(event[0])
                if "K2" not in keypress_durations:
                    keypress_durations["K2"] = [key2_keypress_duration]
                else:
                    keypress_durations["K2"].append(key2_keypress_duration)
                key2_keypress_duration = 0
                key2_pressed = False

    if key1_pressed:
        if "K1" not in keypress_durations:
            keypress_durations["K1"] = [key1_keypress_duration]
        else:
            keypress_durations["K1"].append(key1_keypress_duration)

    if key2_pressed:
        if "K2" not in keypress_durations:
            keypress_durations["K2"] = [key2_keypress_duration]
        else:
            keypress_durations["K2"].append(key2_keypress_duration)

    return keypress_durations


def graph_keypresses(keypress_durations: dict[str, list[int]], metadata: dict={}):

    # Converting keypress_durations to freq dict
    key1_freq_d = {}
    key2_freq_d = {}
    for item in keypress_durations["K1"]:
        if item in key1_freq_d:
            key1_freq_d[item] += 1
        else:
            key1_freq_d[item] = 1

    for item in keypress_durations["K2"]:
        if item in key2_freq_d:
            key2_freq_d[item] += 1
        else:
            key2_freq_d[item] = 1

    RANGE=200

    # Limiting the x-axis between 0 and 200.
    x_values = list(range(RANGE+1))

    y_values1 = [0] * (RANGE+1)
    y_values2 = [0] * (RANGE+1)

    for key, value in key1_freq_d.items():
        if 0 <= key <= RANGE:
            y_values1[key] = value

    for key, value in key2_freq_d.items():
        if 0 <= key <= RANGE:
            y_values2[key] = value

    plt.figure(figsize=(10, 5))


    plt.bar(x_values, y_values1, color='red', alpha=0.1, edgecolor='black', linewidth=1.5, label="K1")
    plt.bar(x_values, y_values2, color='blue', alpha=0.1, edgecolor='black', linewidth=1.5, label="K2")

    # Setting the x-axis range from 0 to 100
    plt.xlim(0, RANGE)

    # Adding labels and title
    plt.xlabel('Delays (in ms)')
    plt.ylabel('Frequency')
    if "artist" not in metadata:
        plt.title(f"Scores from {metadata['user']}")
    elif metadata != {}:
        plt.title(f"{metadata['user']} on {metadata['artist']} - {metadata['title']} [{metadata['difficulty']}]")
    else:
        plt.title(f"Combined Replays")

    plt.legend()

    plt.grid(True, linestyle='--', alpha=0.7)

    # Display the plot
    plt.show()


def get_lzma_from_file(file):
    """Given a file object, returns a bytes object consisting of the lzma-compressed replay data.
    """
    read_byte(file)
    read_integer(file)
    beatmap_hash = read_string(file)
    username = read_string(file)
    replay_hash = read_string(file)
    read_short(file)
    read_short(file)
    read_short(file)
    read_short(file)
    read_short(file)
    read_short(file)
    read_integer(file)
    read_short(file)
    read_byte(file)
    read_integer(file)
    read_string(file)
    read_long(file)
    replay_data_length = read_integer(file)
    replay_data = file.read(replay_data_length)

    return replay_data, username


if __name__ == "__main__":

    # Checking if the argument provided is a file
    if len(sys.argv) >= 2:
        # Try to open each of the files
        keypress_durations = {}
        username_s = []
        for i in range(1, len(sys.argv)):
            with open(sys.argv[i], "rb") as file:
                lzma_str, username = get_lzma_from_file(file)
                if username not in username_s:
                    username_s.append(username)
                keypresses = keypress_from_lzma(lzma_str, keypress_durations=keypress_durations)

        graph_keypresses(keypress_durations, metadata={"user": ", ".join(username_s)})
        
        # print(sys.argv)
    else:

        API_KEY = os.getenv("API_KEY")
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")

        token = get_token()
        uid = input("Select a user id: ")
        ids = fetch_user_replay_ids(uid, token)

        print(f"{len(ids)} replays found. Select an index for the replay you would like to see analyzed: ")
        for i, id in enumerate(ids):
            print(f"\t{i}) {id['artist']} - {id['title']} [{id['difficulty']}]")
        print(f"\t*) ALL REPLAYS")
        idx = input("Select an index: ")

        while (idx != '*' and not idx.isdigit()) or (idx.isdigit() and (int(idx) < 0 or int(idx) >= len(ids))):
            print("Invalid index.")
            # print(f"{len(ids)} replays found. Select an index for the replay you would like to see analyzed: ")
            # for i, id in enumerate(ids):
            #     print(f"\t{i}) {id['artist']} - {id['title']} [{id['difficulty']}]")
            # print(f"\t*) ALL REPLAYS")
            idx = input("Select an index: ")

        if idx != "*":
            idx = int(idx)
            replay_id = ids[idx]
            API_KEY = API_KEY if API_KEY else ""
            data = get_lzma_from_id(replay_id["id"], API_KEY)
            keypresses = keypress_from_lzma(data.json()["content"], True)
            graph_keypresses(keypresses, replay_id)

        else:
            # All replays!!!
            # Need some way to rate limit the requests.
            temp_d = {}
            keypresses = {}
            for i, replay_id in enumerate(ids):
                API_KEY = API_KEY if API_KEY else ""
                data = get_lzma_from_id(replay_id["id"], API_KEY)
                keypresses = keypress_from_lzma(data.json()["content"], True, keypress_durations=keypresses)
                temp_d['user'] = replay_id['user']
                # For rate limiting requests!
                print(f"{i+1}/{len(ids)} complete.")
                if i != len(ids) - 1:
                    time.sleep(6)

            graph_keypresses(keypresses, temp_d)

