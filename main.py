from fastapi import FastAPI, Form, Request
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from mangum import Mangum
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Ensure you have the correct OpenAI API key here
client = OpenAI(api_key="sk-proj-a9yr7E5zTCKFmfXI4naIT3BlbkFJuPKavlMNNS6Oew2hLxzY")

app = FastAPI()
handler = Mangum(app)

templates = Jinja2Templates(directory="templates")

chat_log = [{
    'role': 'system',
    'content': 'Είσαι ένας ακαδημαικός βοηθός των φοιτητών του τμήματος Πληροφορικής του Δημοκρίτειου Πανεπιστήμιου Θράκης(δίνεις οποιαδήποτε πληροφορία χρειάζεται ο φοιτητής).'
}]

chat_responses = [
    "Γεια σας! Πως μπορώ να σας βοηθήσω;"
]

def scrape_website():
    urls = [
        "https://www.cs.ihu.gr/contact.xhtml",
        "https://www.cs.ihu.gr/faculty.xhtml",
        "https://www.cs.ihu.gr/special_staff.xhtml",
        "https://www.cs.ihu.gr/affiliate.xhtml",
        "https://www.cs.ihu.gr/omotimoi.xhtml",
        "https://www.cs.ihu.gr/admin_staff.xhtml",
        "https://www.cs.ihu.gr/academic_calendar.xhtml",
        "https://www.cs.ihu.gr/courses.xhtml",
        "https://www.cs.ihu.gr/dissertation.xhtml"
    ]
    content = ""

    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract and append content from each website (customize as needed)
        content += soup.get_text() + "\n\n"

    return content


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    # Ensure the initial system message is added only once
    if len(chat_responses) == 0:
        chat_responses.append("Γεια σας! Πως μπορώ να σας βοηθήσω;")
    return templates.TemplateResponse("layout.html", {"request": request, "chat_responses": chat_responses})


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    website_content = scrape_website()

    prompt = f"{website_content}\n\nUser: {user_input}\nAssistant:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_log + [{'role': 'system', 'content': website_content}],
            temperature=0.6
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        bot_response = f"Sorry, there was an error processing your request: {e}"

    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)
    return templates.TemplateResponse("layout.html", {"request": request, "chat_responses": chat_responses})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
