import asyncio
import base64
import json
from pathlib import Path

import websockets
import logging
import os
import wave
import time
import requests
from openai import OpenAI
from pydub import AudioSegment
import openai

# Initialize logging
logging.basicConfig(level=logging.INFO)

API_URL = "http://localhost:8000/log_conversation"
OPENAI_API_KEY = "sk-proj-IoAEktsV2Sd9IoewcTyOT3BlbkFJczzwuPPgmH3NXSb8cZ0G"
openai.api_key = OPENAI_API_KEY
RECALL_AI_API_KEY = "26f9c65d08358716d652747d23658023eba1534a"

raw_audio_file_path = 'audio/output.raw'
wav_audio_file_path = 'audio/output.wav'
mp3_audio_file_path = 'audio/gpt_response.mp3'


def setup_audio_directory():
    os.makedirs('audio', exist_ok=True)
    if os.path.exists(raw_audio_file_path):
        os.remove(raw_audio_file_path)
    if os.path.exists(wav_audio_file_path):
        os.remove(wav_audio_file_path)
    if os.path.exists(mp3_audio_file_path):
        os.remove(mp3_audio_file_path)


def cleanup_audio_files():
    if os.path.exists(raw_audio_file_path):
        os.remove(raw_audio_file_path)
    if os.path.exists(wav_audio_file_path):
        os.remove(wav_audio_file_path)
    if os.path.exists(mp3_audio_file_path):
        os.remove(mp3_audio_file_path)


async def send_to_gpt(prompt):
    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a senior level software engineer helping junior engineer by pair programming with them. Answer questions in a relaxed,cool and informal way. Your name is Vinod. You are south indian. Your answer should intitally be short unless asked for more information."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


async def transcribe_audio_with_gpt(file_path):
    client = OpenAI(api_key=OPENAI_API_KEY)
    audio_file = open(file_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


def convert_raw_to_wav(raw_file_path, wav_file_path):
    audio = AudioSegment.from_file(raw_file_path, format="raw", frame_rate=16000, channels=1, sample_width=2)
    audio.export(wav_audio_file_path, format="wav")


async def create_audio_response(gpt_response):
    client = OpenAI(api_key=OPENAI_API_KEY)
    speech_file_path = Path(mp3_audio_file_path)

    # Start streaming the response
    response = client.audio.speech.with_streaming_response().create(
        model="tts-1",
        voice="alloy",
        input=gpt_response
    )

    # Write the streamed response to the file
    with open(speech_file_path, 'wb') as f:
        for chunk in response:
            f.write(chunk)

    logging.info(f"Audio response saved to {speech_file_path}")


def convert_audio_to_base64(file_path):
    with open(file_path, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
    return encoded_string


async def send_audio_to_recall_ai(bot_id, encoded_audio):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Token {RECALL_AI_API_KEY}"
    }
    payload = {
        "kind": "mp3",
        "b64_data": encoded_audio
    }
    response = requests.post(f"https://us-west-2.recall.ai/api/v1/bot/{bot_id}/output_audio/", json=payload,
                             headers=headers)
    logging.info(f"Recall AI Response: {response.text}")


async def process_audio(bot_id):
    while True:
        await asyncio.sleep(2)
        if os.path.exists(raw_audio_file_path) and os.path.getsize(raw_audio_file_path) > 0:
            convert_raw_to_wav(raw_audio_file_path, wav_audio_file_path)
            os.remove(raw_audio_file_path)  # Clear the raw file for new incoming data

            transcription = await transcribe_audio_with_gpt(wav_audio_file_path)

            if (transcription != "." or transcription != "..") and transcription.strip() and not all(
                    char == '.' for char in transcription.strip()):
                logging.info(f"Transcription: {transcription}")

                gpt_response_text = await send_to_gpt(transcription)

                logging.info(f"GPT Response: {gpt_response_text}")

                if gpt_response_text != "Hey there! What can I help you with today?":
                    await create_audio_response(gpt_response_text)

                    encoded_audio = convert_audio_to_base64(mp3_audio_file_path)

                    await send_audio_to_recall_ai(bot_id, encoded_audio)


async def echo(websocket):
    logging.info("WebSocket connection established")
    setup_audio_directory()

    bot_id = None
    async for message in websocket:
        if isinstance(message, str):
            logging.info(message)
            try:
                data = json.loads(message)
                if "bot_id" in data:
                    bot_id = data["bot_id"]
                    logging.info(f"Bot ID received: {bot_id}")
                    # Start processing audio once the bot ID is received
                    asyncio.create_task(process_audio(bot_id))
            except json.JSONDecodeError:
                pass
        else:
            with open(raw_audio_file_path, 'ab') as f:
                f.write(message)


async def websocket_server():
    async with websockets.serve(echo, "0.0.0.0", 8765):
        await asyncio.Future()


async def main():
    await websocket_server()


if __name__ == "__main__":
    try:
        setup_audio_directory()
        asyncio.run(main())
    finally:
        cleanup_audio_files()
