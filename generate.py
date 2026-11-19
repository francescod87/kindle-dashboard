import os
import datetime
import random
import requests
from icalendar import Calendar
from playwright.sync_api import sync_playwright

# --- CONFIGURAZIONE (usa i Secrets di GitHub) ---
LAT = os.environ.get("LAT", "43.7696")
LON = os.environ.get("LON", "11.2558")
ICAL_URL = os.environ.get("ICAL_URL", "")
APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL", "") # Opzionale per Tasks e Foto
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")

# 1. Recupera Meteo da Open-Meteo
def get_weather():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FRome"
    r = requests.get(url).json()
    curr = round(r["current_weather"]["temperature"])
    t_max = round(r["daily"]["temperature_2m_max"][0])
    t_min = round(r["daily"]["temperature_2m_min"][0])
    return curr, t_min, t_max, "Sereno/Variabile"

# 2. Recupera Eventi da Google Calendar (.ics)
def get_calendar_events():
    if not ICAL_URL:
        return "<li>Nessun calendario configurato</li>"
    r = requests.get(ICAL_URL)
    cal = Calendar.from_ical(r.content)
    today = datetime.date.today()
    events_html = []
    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            event_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
            if event_date == today:
                time_str = dtstart.strftime("%H:%M") if isinstance(dtstart, datetime.datetime) else "Tutto il giorno"
                summary = str(component.get('summary'))
                events_html.append(f"<li><span class='time'>{time_str}</span> {summary}</li>")
    return "".join(events_html) if events_html else "<li>Nessun evento oggi</li>"

# 3. Recupera Tasks e Foto (tramite il tuo Apps Script o fallback)
def get_tasks_and_photo():
    tasks_html = "<li>Completare configurazione</li>"
    # Foto di fallback ad alta risoluzione (paesaggio) se Google Foto non è collegato
    photo_url = "https://picsum.photos/758/360?grayscale"
    
    if APPS_SCRIPT_URL and ACCESS_CODE:
        try:
            r = requests.get(f"{APPS_SCRIPT_URL}?key={ACCESS_CODE}&nonce=12345678&origin=https://github.com").json()
            if r.get("ok") and r.get("data"):
                tasks = r["data"].get("tasks", [])
                if tasks:
                    tasks_html = "".join([f"<li>☐ {t['title']}</li>" for t in tasks[:6]])
                else:
                    tasks_html = "<li>Tutto completato!</li>"
        except Exception as e:
            print("Errore Apps Script:", e)
    return tasks_html, photo_url

# 4. Santo e Aforisma del giorno
def get_saint_and_quote():
    # Puoi espandere queste liste o collegarle a un file JSON nel repo
    santi = {
        "19-11": "San Ponziano, San Barlaam e Sant'Abdia",
        "20-11": "San Felice di Valois e Sant'Edmondo",
        "21-11": "Presentazione della Beata Vergine Maria"
    }
    oggi_key = datetime.date.today().strftime("%d-%m")
    santo = santi.get(oggi_key, "Santi del giorno")
    
    aforismi = [
        "La semplicità è la sofisticazione massima. — Leonardo da Vinci",
        "Non conta quanto lentamente vai, purché tu non ti fermi. — Confucio",
        "Il modo migliore per predire il futuro è crearlo. — Peter Drucker"
    ]
    return santo, random.choice(aforismi)

def main():
    now = datetime.datetime.now()
    giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    
    giorno_sett = giorni[now.weekday()]
    data_comp = f"{now.day} {mesi[now.month - 1]} {now.year}"
    curr, t_min, t_max, desc = get_weather()
    eventi = get_calendar_events()
    tasks, foto = get_tasks_and_photo()
    santo, aforisma = get_saint_and_quote()

    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{GIORNO_SETTIMANA}}", giorno_sett)
    html = html.replace("{{DATA_COMPLETA}}", data_comp)
    html = html.replace("{{TEMP_ATTUALE}}", str(curr))
    html = html.replace("{{TEMP_MIN}}", str(t_min))
    html = html.replace("{{TEMP_MAX}}", str(t_max))
    html = html.replace("{{METEO_DESC}}", desc)
    html = html.replace("{{FOTO_URL}}", foto)
    html = html.replace("{{LISTA_EVENTI}}", eventi)
    html = html.replace("{{LISTA_TASKS}}", tasks)
    html = html.replace("{{SANTO}}", santo)
    html = html.replace("{{AFORISMA}}", aforisma)

    with open("render.html", "w", encoding="utf-8") as f:
        f.write(html)

    # Renderizza in PNG 758x1024
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 758, "height": 1024})
        page.goto("file://" + os.path.abspath("render.html"))
        page.wait_for_timeout(1500) # Attende il caricamento della foto
        page.screenshot(path="dashboard.png")
        browser.close()

if __name__ == "__main__":
    main()
