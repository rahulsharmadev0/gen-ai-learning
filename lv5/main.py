import json
import requests
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAwoZd3iMs-_wiiopXr3Ys3Jg0exenAkoU")


def get_weather(city: str):
    print(f"\n-----------🔨 Tool Called: get_weather({city})-----------")
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return "Something went wrong"


with open("lv5/sys-inst.txt", "r") as file:
    system_instructions = file.read()


geminiModel:str = "gemini-2.0-flash"

configWithMySysInstruction = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text=system_instructions),
        ],
    )


# -----TOPIC: function calling-----
#   1. write system instructions
#        1.1: steps --> [plan, action, observe, output]
#   2. define weather funciton
#   3. Connect function with system instructions
#   4. Set ♾️ Loop for chat

message = [] # List<Map>


while True:
    inputText =  input("> ")
    message.append({"role": "user", "content": inputText}) # store at index 0

    while True:
        response =  client.models.generate_content( 
            model=geminiModel,
            contents = json.dumps(message), # convert into String
            # candidate_count=1,
            config = configWithMySysInstruction
        )

        jsonResponse = json.loads(response.text)
        step:str = jsonResponse.get('step')
        content:str = jsonResponse.get('content')
        functionName:str = jsonResponse.get('function')
        functionArguments:str = jsonResponse.get('input')

        print(f"\n{step}: {content}")
        if(functionName == 'get_weather'):
                content = get_weather(functionArguments) # function calling 
                message.append({"role": "assistant", "content": json.dumps({ "step":"observe", "output": content})})
                continue

        message.append({ "role": "assistant", step:content})
        if(step == 'output'):
            break




