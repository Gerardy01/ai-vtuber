import openai
import pyaudio
import wave
import json
import re
import time
import threading
import pytchat

import keyboard

# Utils
from utils import get_prompt, speech_text


# Setup
from config import OPENAI_API_KEY, OPENAI_ORGANIZATION
# openai.organization = OPENAI_ORGANIZATION
openai.api_key = OPENAI_API_KEY

# setup var
user_name = "System"
auto_speech_default_count = 10

blacklist = ["Nightbot", "streamelements"]

# app var
current_user_message = ""
prev_live_chat = ""
live_chat = ""
live_chat_user = ""

conversation = []
history = {"history" : conversation}
auto_speech_count = auto_speech_default_count
is_speaking = False


def handle_from_input(text):
    global is_speaking

    if len(text) > 50:
        return
    
    is_speaking = True

    print("Questions: " + text)
    result = user_name + " berkata " + text 
    add_conversation("user", result)

    speech_text(f"dari {user_name}, {text}")

    # time.sleep(duration)
    chat_gpt_generate()

def yt_live(live_id):
    global live_chat, live_chat_user
    live = pytchat.create(video_id=live_id)
    while live.is_alive():
        for c in live.get().sync_items():
            if c.author.name in blacklist:
                 continue
            
            if not c.message.startswith("!"):
                chat_raw = re.sub(r':[^\s]+:', '', c.message)
                chat_raw = chat_raw.replace('#', '')
                live_chat = chat_raw
                live_chat_user = c.author.name
                print('new message')


def record_audio():
    # to prevent assistant idle talk when do voice input
    global is_speaking
    is_speaking = True

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print('recording...')

    frames = []

    while keyboard.is_pressed('space'): 
        data = stream.read(CHUNK)
        frames.append(data)


    print('stoped')
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open("recording.wav", "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    format_audio_to_text("recording.wav")

def format_audio_to_text(file):
    
    try:
        file_audio = open(file, "rb")

        transcript = openai.Audio.transcribe("whisper-1", file_audio)
        message = transcript.text

        if len(message) > 50:
            return

        print(f"Questions : {message}")
        
        result = user_name + " berkata " + message
        add_conversation("user", result)
        chat_gpt_generate()
    except Exception as e:
        print("Error in formating audio: {0}".format(e))
        return
    
def live_preparation():
    global live_chat, prev_live_chat, is_speaking, live_chat_user
    while True:
        if not is_speaking and prev_live_chat != live_chat:

            if len(live_chat) > 50:
                return

            is_speaking = True
            prev_live_chat = live_chat

            print("Questions: " + live_chat)

            result = live_chat_user + " berkata " + live_chat

            add_conversation("user", result)
            speech_text(f"dari {live_chat_user}, {live_chat}")
            chat_gpt_generate()
        time.sleep(1)

def chat_gpt_generate():
    global auto_speech_count, is_speaking

    total_characters = sum(len(d['content']) for d in conversation)
    while total_characters > 4000:
        try:
            conversation.pop(2) # 2 because the first one is the questions
            total_characters = sum(len(d['content']) for d in conversation)
        except Exception as e:
            print("Error removing old messages: {0}".format(e))

    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    prompt_data = get_prompt()

    try:
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = prompt_data,
            max_tokens = 128,
            temperature = 1,
            top_p = 0.9,
            frequency_penalty = 2.0,
            presence_penalty = 2.0,
        )
        message = response['choices'][0]['message']['content']
        clean_message = re.sub(r'[:;)(@]', '', message)
        conversation.append({'role': 'assistant', 'content': clean_message})
        print(f"Assistant: {clean_message}")

        # if conversation[-2]['role'] == 'user':
        #     message_to_speach = combined_message(clean_message)
        # else:
        #     message_to_speach = clean_message

        speech_text(clean_message)

        is_speaking = False
        auto_speech_count = auto_speech_default_count
    except Exception as e:
        print("Generate response Error: {0}".format(e))
        is_speaking = False
        auto_speech_count = auto_speech_default_count

def combined_message(message):
    global current_user_message
    return f"{current_user_message}. {message}"
    



def add_conversation(role, message):
    global conversation, current_user_message
    current_user_message = message
    conversation.append({"role": role, "content": current_user_message})


def auto_speech():
    global auto_speech_count

    while True:
        time.sleep(1)
        auto_speech_count -= 1
        print(auto_speech_count)

        if auto_speech_count <= 0 and not is_speaking:
            add_conversation("system", "you are idling. talk anything to your viewer without say hello")
            chat_gpt_generate()



if __name__ == "__main__":

    print('Mode Selection')
    print('"1" for Use Voice Mode')
    print('"2" for Use Terminal Mode')
    print('"3" for Use Youtube Live Mode')
    mode = input("Mode: ")

    auto_speech_default_count = int(input("Auto speech every: "))
    
    try:
        if mode == "1":
            user = input("Accessing as: ")
            user_name = user
            print('hold SPACE to record and wait until "recording..." displayed before speaking')
            t = threading.Thread(target=auto_speech)
            t.start()
            while True:
                if keyboard.is_pressed('space'):    
                    record_audio()

        elif mode == "2":
            user = input("Accessing as: ")
            user_name = user
            t = threading.Thread(target=auto_speech)
            t.start()
            while True:
                text = input('say something: ')
                handle_from_input(text=text)
        
        elif mode == '3':
            # live_id = input("Youtube Live ID: ")
            live_id = 'WcFABf4uxM8'
            t = threading.Thread(target=auto_speech)
            t.start()
            ytt = threading.Thread(target=live_preparation)
            ytt.start()
            yt_live(live_id)
        
        else:
            print('Mode not found')

    except KeyboardInterrupt:
        t.join()
        print("Thread Stopped")
             

