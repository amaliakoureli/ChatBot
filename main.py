# Εισαγωγές απαραίτητων βιβλιοθηκών.
from fastapi import FastAPI, Form, Request  # FastAPI για το API, Form και Request για φόρμες και αιτήματα.
from typing import Annotated  # Annotated για τύπους δεδομένων (π.χ., στη φόρμα).
from fastapi.templating import Jinja2Templates  # Jinja2Templates για τη διαχείριση templates.
from fastapi.responses import HTMLResponse  # HTMLResponse για να επιστρέφουμε HTML απαντήσεις.
from fastapi.staticfiles import StaticFiles  # StaticFiles για τη διαχείριση στατικών αρχείων.
from mangum import Mangum  # Mangum για υποστήριξη AWS Lambda εκτέλεσης.
import requests  # requests για αποστολή HTTP αιτημάτων.
from bs4 import BeautifulSoup # BeautifulSoup για την εξαγωγή δεδομένων από HTML.
from openai import OpenAI  # Βιβλιοθήκη OpenAI για πρόσβαση στο GPT μοντέλο.
import uvicorn  # uvicorn για την εκκίνηση του FastAPI server.
from datetime import datetime  # datetime για τη διαχείριση και μορφοποίηση ημερομηνιών.

# client = OpenAI(api_key="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")  # Ρυθμίσεις OpenAI κλειδιού API.
client = OpenAI(api_key="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")  # Ρυθμίσεις OpenAI κλειδιού API.

app = FastAPI() #  Δημιουργία FastAPI εφαρμογής.

handler = Mangum(app)  # Ορίζουμε handler για AWS Lambda υποστήριξη με το Mangum.

templates = Jinja2Templates(directory="templates") # Ορισμός του φακέλου templates για HTML rendering με Jinja2.

app.mount("/static", StaticFiles(directory="static"), name="static") # Ορισμός του φακέλου στατικών αρχείων (π.χ., CSS, εικόνες).

# Αρχικό σύστημα, που περιέχει τις βασικές πληροφορίες και οδηγίες για το chatbot.
chat_log = [{
    'role': 'system',
    'content': 'Είσαι ένας ακαδημαϊκός βοηθός που παρέχει πληροφορίες '
               'για μαθήματα, καθηγητές και διοικητικές υποθέσεις σχετικά με τις σπουδές '
               'σε φοιτητές και μη, του Τμήματος Πληροφορικής του Δημοκρίτειου Πανεπιστημίου Θράκης.'
               'Δώσε συγκεκριμένες και ακριβείς απαντήσεις, με επίκεντρο την ερώτηση.'
}]

# Αρχικό μήνυμα του chatbot για το UI.
chat_responses = [
    {
        'message': "Γεια σας! Πως μπορώ να σας βοηθήσω;",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Φόρμα ημερομηνίας και ώρας.
    }
]

# Συνάρτηση για τη μορφοποίηση κειμένου που σχετίζεται με πληροφορίες επικοινωνίας #(σχολής/καθηγητών).
def format_as_contact_info(text: str):
    parts = text.split("\n", 1)  # Χωρίζει το κείμενο σε δύο μέρη με βάση την πρώτη αλλαγή γραμμής.
    if len(parts) < 2:
        return text  # Επιστρέφει το αρχικό κείμενο αν δεν υπάρχει δεύτερο μέρος.
    introduction = parts[0].strip()  # Παίρνει την εισαγωγή του χρήστη.
    contact_items = parts[1].split("\n")  # Διαχωρίζει τα στοιχεία επικοινωνίας.
    contact_items = [line.replace("**", "").strip() for line in contact_items if line.strip()]  # Καθαρισμός γραμμών.
    formatted_intro = f"<p>{introduction}</p>"  # Μορφοποιεί την εισαγωγή ως παράγραφο.
    formatted_contact_info = "<p>" + "<br>".join(contact_items) + "</p>"   # Μορφοποιεί τα στοιχεία επικοινωνίας.
    return formatted_intro + formatted_contact_info

# Συνάρτηση μορφοποίησης κειμένου που σχετίζεται με τα μαθήματα του προγράμματος σπουδών σε παράγραφο και λίστα.
def format_as_paragraph_and_list(text: str):
    parts = text.split("\n", 1)
    if len(parts) < 2:
        return text  # Επιστρέφει το αρχικό κείμενο αν δεν υπάρχει δεύτερο μέρος.
    paragraph = parts[0].strip()  # Παίρνει την εισαγωγή (παράγραφο).
    list_items = parts[1].split("\n")  # Παίρνει τα στοιχεία της λίστας.
    formatted_response = f"<p>{paragraph}</p><p>" + "<br>".join(line.replace("**", "").strip() for line in list_items if line.strip()) + "</p>"   # Μορφοποιεί την απάντηση.
    return formatted_response

# Συνάρτηση καθαρισμού κειμένου ανακοινώσεων.
def clean_announcement_text(text: str):
    cleaned_text = text.replace("**", "").replace("-", "").strip()   # Αφαιρεί ειδικούς χαρακτήρες και κενά.
    cleaned_text = " ".join(cleaned_text.split())  # Συνενώνει πολλαπλά κενά.
    return cleaned_text

# Συνάρτηση επιλογής της κατάλληλης απάντησης του chatbot για την εκάστοτε ερώτηση.
def format_response(bot_response: str):
    if "ανακοίνωση" in bot_response.lower() or "πτυχιακή" in bot_response.lower(): #Αν η ερώτηση περιέχει τις λέξεις "ανακοίνωση" ή "πτυχιακή", επιστρέφεται η απάντηση με την κατάλληλη μορφοποίηση.
        cleaned_response = clean_announcement_text(bot_response)
    else:
        cleaned_response = bot_response  # Αλλιώς αφήνει το κείμενο ως έχει.
    if "επικοινωνίας" in cleaned_response:#Αν η ερώτηση περιέχει τη λέξη "επικοινωνίας", επιστρέφεται η απάντηση με την κατάλληλη μορφοποίηση.
        return format_as_contact_info(cleaned_response)
    elif "Διδακτικές Μονάδες" in cleaned_response or "μαθήματα" in cleaned_response: #Αλλιώς αν η ερώτηση περιέχει τις λέξεις "Διδακτικές Μονάδες" ή "μαθήματα", επιστρέφεται η απάντηση με την κατάλληλη #μορφοποίηση.
        return format_as_paragraph_and_list(cleaned_response)
    else:
        return cleaned_response  # Αλλιώς επιστρέφει το κείμενο χωρίς επιπλέον μορφοποίηση.

# Συνάρτηση που σαρώνει περιεχόμενο από τις ιστοσελίδες.
def scrape_website():
    urls = [
        "https://www.cs.ihu.gr/contact.xhtml",
        "https://www.cs.ihu.gr/faculty.xhtml",
        "https://www.cs.ihu.gr/special_staff.xhtml",
        "https://www.cs.ihu.gr/affiliate.xhtml",
        "https://www.cs.ihu.gr/omotimoi.xhtml",
        "https://www.cs.ihu.gr/announcements.xhtml",
        "https://www.cs.ihu.gr/dissertation.xhtml",
        "https://www.cs.ihu.gr/courses.xhtml"
    ]
    content = ""  # Αρχικό κενό περιεχόμενο.
    for url in urls:  # Για κάθε URL στη λίστα.
        response = requests.get(url)  # Στέλνουμε HTTP αίτημα στη σελίδα.
        soup = BeautifulSoup(response.content, "html.parser")  # Ανάλυση της HTML σελίδας.
        content += soup.get_text() + "\n\n"  # Προσθήκη του καθαρού κειμένου.
    return content

# Route για την αρχική σελίδα του chat.
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    if len(chat_responses) == 0:  # Αν δεν υπάρχουν απαντήσεις, προσθέτει μία.
        chat_responses.append({
            'message': "Γεια σας! Πως μπορώ να σας βοηθήσω;",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return templates.TemplateResponse("layout.html", {"request": request, "chat_responses": chat_responses})


# Route για την αποστολή και επεξεργασία απάντησης από τον chatbot.
@app.post("/get-response", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Τρέχουσα ώρα.
    chat_log.append({'role': 'user', 'content': user_input})  # Προσθήκη εισόδου χρήστη στο chat log.
    website_content = scrape_website()  # Scraping περιεχομένου από τις σελίδες.

    prompt = f"{website_content}\n\nUser: {user_input}\nAssistant:"  # Δημιουργία prompt με βάση το περιεχόμενο της εισόδου του χρήστη.

    try:
         # Κλήση στο GPT μοντέλο για να δημιουργήσει την απάντηση.
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Χρήση του GPT-4 μοντέλου.
            messages=chat_log + [{'role': 'system', 'content': website_content}],  # Προσθήκη του chat log.
            temperature=0.5  # Ελεγχόμενη δημιουργικότητα.
        )
        bot_response = response.choices[0].message.content  # Παίρνει την απάντηση του bot.
        formatted_response = format_response(bot_response)  # Μορφοποίηση της απάντησης.
    except Exception as e:
        formatted_response = f"Sorry, there was an error processing your request: {e}" # Σε περίπτωση λάθους, επιστρέφει μήνυμα λάθους.

    chat_log.append({'role': 'assistant', 'content': formatted_response}) # Προσθήκη της απάντησης του chatbot στο chat log και στο UI.
    chat_responses.append({
        'message': formatted_response,
        'timestamp': current_time
    })
    return formatted_response  # Επιστροφή της απάντησης.

# Εκκίνηση του FastAPI server.
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000) # Εκκίνηση του server στη διεύθυνση 0.0.0.0 και θύρα 8000.
