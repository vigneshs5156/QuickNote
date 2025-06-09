from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import whisper
import os
import torch
import warnings
import ollama
import json


warnings.filterwarnings("ignore")

app = FastAPI()

# Check if GPU is available
device = "cuda" if torch.cuda.is_available() else "cpu"
#device = "cpu"

# Load the Whisper model on GPU
model = whisper.load_model("small").to(device)

@app.get("/")
def greet():
    return "Hi welcome to the STT backend"

def get_output(text):
    prompt = f"""
    You are an expert at reading messy food orders and extracting structured data.  
    Given a text, extract all food items and their quantities.  
    Output a valid Python dictionary without any explanation or markdown.  
    Misspellings are common; correct them using your knowledge.

    Examples:

    Input: "3 momozz, 2 vege pizaa, 1 briyani"
    Output: {{"Momos": 3, "Veg Pizza": 2, "Biryani": 1}}

    Input: "1 chiken burger and 4 veg momos"
    Output: {{"Chicken Burger": 1, "Veg Momos": 4}}

    Input: "2 chicken juicy burger 5 veg pizza 7 burrito and 66 veg momos"
    Output: {{"Chicken juicy burger": 2, "Veg Pizza": 5, "Burrito":  7, "Veg Momos":66}}

    Input: "Veg sandwich, 4 veg pizza, 18 burritos"
    Output: {{"Veg sandwich": 1, "veg pizza": 4, "Burritos":18}}

    Your Input: {text}
    """
    model = ollama.chat(model= "gemma3:1b", messages= [{'role': 'user','content': prompt}])

    output = model['message']['content']

    return output



@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    file_path = "temp_audio.wav"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    result = model.transcribe(file_path, language = "en")
    os.remove(file_path)

    text = result["text"]
    raw_output = get_output(text)

    try:
        # Parse the string to a proper Python dict
        structured_data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        return JSONResponse(
            content={"error": f"Invalid output from model: {raw_output}"},
            status_code=500
        )

    return JSONResponse(content=structured_data)
