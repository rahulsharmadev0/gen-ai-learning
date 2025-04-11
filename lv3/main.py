import json
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAwoZd3iMs-_wiiopXr3Ys3Jg0exenAkoU")

with open("lv3/sys-inst.txt", "r") as file:
    system_prompt = file.read()

messages = []

query_text = input("> ")
messages.append(types.Content(
    parts=[types.Part(text=query_text)],
    role="user"
))

while True:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=messages,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",           
            system_instruction=[
                types.Part(text=system_prompt),
            ],
        ),
    )
    response_content_text = response.text

    try:
        parsed_response = json.loads(response_content_text)
        messages.append(types.Content(parts=[types.Part(text=response_content_text)], role='assistant'))

    except json.JSONDecodeError:
        print("Error: Could not decode JSON response.")
        break
    if parsed_response.get("step") != "output":
       print(f"🧠: {parsed_response.get('content')}")
       messages.append(types.Content(
          role='user',
          parts=[types.Part(text="Continue to next step in the process")]
       ))
    continue

    print(f"🤖: {parsed_response.get('content')}")
    break