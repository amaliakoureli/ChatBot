from openai import OpenAI
from fastapi import FastAPI,Form, Request
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from mangum import Mangum
import json

data_path = "data/fineTuning.json"

# Load the dataset
with open(data_path, 'r', encoding='utf-8') as f:
    dataset = [json.loads(line) for line in f]

# Initial dataset stats
print("Num examples:", len(dataset))
print("First example:")
for message in dataset[0]["messages"]:
    print(message)


client = OpenAI(
    api_key="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"
)
client.files.create(
    file=open("fineTuning.json", "rb"),
    purpose="fine-tune"
)

app = FastAPI()
handler = Mangum(app)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("layout.html", {"request":request})


chat_log = [{'role':'system',
             'content': ' Είσαι ένας ακαδημαικός βοηθός των φοιτητών του τμήματος Πληροφορικής του Διεθνούς Πανεπιστημίου της Ελλάδος, που βρίσκεται στην πόλη της Καβάλας'
             }]

chat_responses = []

@app.post("/", response_class=HTMLResponse)

async def chat(request: Request, user_input: Annotated[str, Form()]):

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_log,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)
    return templates.TemplateResponse("layout.html",{"request": request, "chat_responses": chat_responses})