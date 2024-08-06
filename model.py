import os
from pathlib import Path

import dotenv
from openai import AsyncOpenAI
from shiny import ui
from media_extractor import split_video
import datauri

dotenv.load_dotenv(override=True)

api_key = os.environ["OPENAI_API_KEY"]='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'

# OR
# api_key = os.environ.get("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("OPENAI_API_KEY not found in .env file")

client = AsyncOpenAI()

async def chat(video_file: str, messages: list[any], progress: ui.Progress) -> str:
    progress.set(message="Decoding input...", value=0)
    audio_uri, image_uris = split_video(video_file)

    # Decode the audio file into text, using OpenAI's `whisper-1` model. The result will serve as the text prompt for the LLM.

    progress.set(message="Transcribing audio...", value=0.1)
    with datauri.as_tempfile(audio_uri) as audio_file:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1", file=Path(audio_file)
        )
        
    user_prompt = transcription.text
    
    progress.set(message="Waiting for response...", value=0.2)
    
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                'role': 'user',
                'content': [
                    {'type':'text', 'text': user_prompt},
                    *[
                        {
                            'type': 'image_url',
                            'image_url': {'url': image_uri, 'detail':'auto'},
                        }
                        for image_uri in image_uris
                    ]
                ]
            },
            {
                'role':'system',
                'content': Path("system_prompt.txt").read_text()
            },
        ],
    )
    
    response_text = response.choices[0].message.content
    
    # Maintaining History
    messages.append(response.choices[0].message)
    
    
    progress.set(message="Synthesizing audio...", value=0.8)
    audio = await client.audio.speech.create(
        model='tts-1',
        voice='nova',
        input=response_text,
        response_format='mp3',
    )
    response_audio_uri = datauri.from_bytes(audio.read(), "audio/mpeg")
    return response_audio_uri
