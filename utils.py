import json
import os
import tempfile

import subprocess
import audiosegment
from pydub import AudioSegment
from IPython.display import Audio, display
from playsound import playsound
from mutagen.mp3 import MP3

AudioSegment.ffmpeg = r'C:\ffmpeg\bin'


def get_identity(identity_path):  
    with open(identity_path, "r", encoding="utf-8") as f:
        identity_context = f.read()
        identity_context = identity_context.replace('\n', ' ')
    return {"role": "system", "content": identity_context}


def get_prompt():
    prompt = []
    identity = get_identity("character/eve.txt")
    prompt.append(identity)
    
    with open("conversation.json", "r") as f:
        data = json.load(f)
        history = data['history']
        
    if len(history) > 1:
        prompt.append({
            "role": "system",
            "content": f"Below is conversation history.\n"
        })
        for message in history[:-1]:
            prompt.append(message)
        
    prompt.append({
        "role" : "system",
        "content": "Here is the latest conversation.\n*Make sure your response is within 150 characters, and \
            dont use the same sentence as already recorded in conversation history!"
    })

    if len(history) != 0:
        prompt.append(history[-1])

    return prompt


def speech_text(text_input):
    gender = "Female" #@param ["Male", "Female"]
    text = text_input

    if gender == "Male":
        command = ['edge-tts', '--voice', 'id-ID-ArdiNeural', '--text', text, '--write-media', 'edge.mp3', '--write-subtitles', 'edge.vtt']
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        print(result.stdout)
    elif gender == "Female":
        command = ['edge-tts', '--voice', 'id-ID-GadisNeural', '--text', text, '--write-media', 'edge.mp3', '--write-subtitles', 'edge.vtt']
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        print(result.stdout)

    try:
        audio = Audio("edge.mp3")
    except Exception as e:  print("Error:", str(e))

    audio_mp3 = MP3('edge.mp3')
    duration = audio_mp3.info.length

    try:
        if not os.access("edge.mp3", os.R_OK):
            print("Cannot access the file:", "edge.mp3")
            return

        temp_filename = os.path.join(tempfile.gettempdir(), 'temp.mp3')

        with open("edge.mp3", 'rb') as file:
            with open(temp_filename, 'wb') as temp_file:
                temp_file.write(file.read())
            
        playsound(temp_filename)
        os.remove(temp_filename)
    except Exception as e:
        print("Error:", str(e))

    return duration
    
    # audio = audiosegment.from_file("edge.mp3")
    # # Set the output format to WAV
    # audio = audio.set_sample_width(2)
    # audio = audio.set_frame_rate(44100)
    # audio = audio.set_channels(1)
    # # Export the audio to WAV format
    # audio.export("edge-conv.wav", format='wav')

    # AUDIO = "edge-conv" #@param {type:"string"}
    # MODEL = "/content/so-vits-test/alice.pth" #@param {type:"string"}
    # CONFIG = "/content/so-vits-test/config.json" #@param {type:"string"}
    # METHOD = "harvest" #@param ["harvest", "dio", "crepe", "crepe-tiny", "parselmouth"]
    # PITCH = 0 #@param {type:"slider", min:-12, max:12, step:1}

    # # Auto Pitch Mode
    # command = f"svc infer {AUDIO}.wav -c {CONFIG} -m {MODEL} -fm {METHOD}"
    # subprocess.run(command, shell=True)

    # # Manual Pitch Mode
    # # !svc infer {AUDIO}.wav -c {CONFIG} -m {MODEL} -fm {METHOD} -na -t {PITCH}

    # try:
    #     display(Audio(f"{AUDIO}-out.wav", autoplay=True))
    # except Exception as e:  print("Error:", str(e))

            
