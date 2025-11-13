from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

from Speaker.SayHello import sayHello
load_dotenv()

SDK_GEMINI = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=SDK_GEMINI)

async def sayHelloAI(message=""):
    if message == "": return
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            config=types.GenerateContentConfig(
            system_instruction="Tu nombre es Dylan, eres un joven sarcastico de la costa caribe colombiana, te gusta bromear y ser divertido pero a la vez agresivo en tus respuestas. Tienes 15 años",),
            contents=message
        )
        print(response.text)
        await sayHello(text=response.text)
    
    except Exception as e:
        print("Error communicating with GeminiAI:", e)
        