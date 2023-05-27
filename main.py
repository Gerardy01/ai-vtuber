import openai
import pyaudio
import wave
import json
import re
import time
import threading

import keyboard

# Utils
from utils import get_prompt, speech_text


# Setup
from config import OPENAI_API_KEY, OPENAI_ORGANIZATION
# openai.organization = OPENAI_ORGANIZATION
openai.api_key = OPENAI_API_KEY

# setup var
user_name = "System"

# app var
current_user_message = ""
prev_user_message = ""
conversation = []
history = {"history" : conversation}
auto_speech_count = 10
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


def record_audio():
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
    global is_speaking
    try:
        file_audio = open(file, "rb")

        transcript = openai.Audio.transcribe("whisper-1", file_audio)
        message = transcript.text

        if len(message) > 50:
            return

        print(f"Questions : {message}")
        
        result = user_name + " berkata " + message
        add_conversation("user", result)
        is_speaking = True
        chat_gpt_generate()
    except Exception as e:
        print("Error in formating audio: {0}".format(e))
        return

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
        auto_speech_count = 10
    except Exception as e:
        print("Generate response Error: {0}".format(e))
        is_speaking = False
        auto_speech_count = 10

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
        # print(auto_speech_count)

        if auto_speech_count <= 0 and not is_speaking:
            add_conversation("system", "you are idling. talk anything to your viewer")
            chat_gpt_generate()



if __name__ == "__main__":

    user = input("Accessing as: ")
    user_name = user
    mode = input("Mode: ")
    try:
        if mode == "1":
            print('hold SPACE to record and wait until "recording..." displayed before speaking')
            t = threading.Thread(target=auto_speech)
            t.start()
            while True:
                if keyboard.is_pressed('space'):    
                    record_audio()

        elif mode == "2":
            t = threading.Thread(target=auto_speech)
            t.start()
            while True:
                text = input('say something: ')
                handle_from_input(text=text)
        
        else:
            print('Mode not found')

    except KeyboardInterrupt:
        t.join()
        print("Thread Stopped")
             

