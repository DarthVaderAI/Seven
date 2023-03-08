import asyncio
import io
import pyttsx3
import discord
import openai
import requests
import tempfile
from gtts import gTTS
import os
import asyncio

# Replace the path below with the path to your ffmpeg installation
FFMPEG_PATH = 'C:\\ffmpeg\\bin\\ffmpeg.exe'

# Set the FFMPEG_PATH environment variable
os.environ['PATH'] += os.pathsep + os.path.dirname(FFMPEG_PATH)

API_KEY = "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"
openai.api_key = API_KEY


def get_prayer_times():
    response = requests.get(
        'https://api.aladhan.com/v1/timingsByCity/23-02-2023?city=London&country=United+Kingdom&method=2')
    data = response.json()['data']
    timings = data['timings']
    return timings


async def play_text_to_speech(voice_channel, text):
    # Set voice_client to None initially
    voice_client = None

    # Check if bot is already connected to a voice channel
    if voice_channel.guild.voice_client is not None:
        voice_client = voice_channel.guild.voice_client
        await voice_client.move_to(voice_channel)
    else:
        voice_client = await voice_channel.connect()

    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    text_to_speech = gTTS(' '.join(text.split()[1:]))
    text_to_speech.save(temp_file.name)

    # Play audio and wait for it to finish
    voice_client.play(discord.FFmpegPCMAudio(temp_file.name))
    while voice_client.is_playing():
        await asyncio.sleep(200)

    # Delete the temporary file
    os.unlink(temp_file.name)

    await voice_client.disconnect()


messages = [{"role": "system", "content": 'Your name is Seven you are a kind hearted helpful Assistant'}]


async def generate_chat_response(message):
    global messages
    prompt = message.content.replace('!chat', '').strip()
    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
    )
    system_message = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": system_message})
    text = response.choices[0].message.content

    return text


# Main function to generate chat response and speak it in voice channel
async def generate_chat_speech(message):
    global messages
    prompt = message.content.replace('!talk', '').strip()
    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
    )
    system_message = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": system_message})
    return system_message


async def handle_message(message):
    if message.content.startswith('!prayer time'):
        await send_prayer_times(message)
    elif message.content.startswith('!chat'):
        response = await generate_chat_response(message)
        await message.channel.send(response)
    elif message.content.startswith('!tts'):
        voice_channel = message.author.voice.channel
        text = ' '.join(message.content.split()[1:])
        await play_text_to_speech(voice_channel, text)
    elif message.content.startswith('!talk'):
        voice_channel = message.author.voice.channel
        system_message = await generate_chat_speech(message)
        await play_text_to_speech(voice_channel, system_message)


async def send_prayer_times(message):
    timings = get_prayer_times()

    if timings is None:
        await message.channel.send('Sorry, I could not retrieve the prayer times at this time. Please try again later.')
        return

    prayer_times = f"Fajr: {timings['Fajr']}\nDhuhr: {timings['Dhuhr']}\nAsr: {timings['Asr']}\nMaghrib: {timings['Maghrib']}\nIsha: {timings['Isha']}"
    await message.channel.send(prayer_times)


def run_discord_bot():
    TOKEN = "MTA3ODQwMTg4OTUyMTExMTEwMw.G7oTA-.RaJvQonMovrj0VFd-zFmdax-SJ2jMxlGzZKNUU"
    API_KEY = "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"

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        await handle_message(message)

    client.run('MTA3ODQwMTg4OTUyMTExMTEwMw.G7oTA-.RaJvQonMovrj0VFd-zFmdax-SJ2jMxlGzZKNUU')
