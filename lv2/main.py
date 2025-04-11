from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAwoZd3iMs-_wiiopXr3Ys3Jg0exenAkoU")


with open("lv2/sys-inst.txt", "r") as file:
    system_instructions = file.read()


query =  input("> ")

response =  client.models.generate_content(
    model="gemini-2.0-flash", contents= query,
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text=system_instructions),
        ],
    )
)

print(response.text);