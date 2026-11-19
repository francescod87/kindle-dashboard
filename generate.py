import os
import requests
from icalendar import Calendar
from datetime import datetime
import pytz

# Leggi i Secret da GitHub
LAT = os.environ.get("LAT", "43.7696")
LON = os.environ.get("LON", "11.2558")
ICAL_URL = os.environ.get("ICAL_URL", "")

# 1. Recupero Meteo (Open-Meteo)
def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
        res = requests.get(url).json()
        current_temp = res['current']['temperature_2m']
        return {"temp": current_temp}
    except Exception as e:
        print(f"Errore meteo: {e}")
        return {"temp": "--"}

# 2. Recupero Calendario (iCal)
def get_calendar():
    events = []
    try:
        if ICAL_URL:
            # Sostituisci webcal:// con https:// se necessario
            url = ICAL_URL.replace("webcal://", "https://")
            cal_data = requests.get(url).text
            cal = Calendar.from_ical(cal_data)
            
            tz = pytz.timezone('Europe/Rome')
            now = datetime.now(tz)
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    summary = component.get('summary')
                    dtstart = component.get('dtstart')
                    if dtstart:
                        dt = dtstart.dt
                        if isinstance(dt, datetime):
                            if dt.tzinfo is None:
                                dt = tz.localize(dt)
                            else:
                                dt = dt.astimezone(tz)
                        else:
                            # Se è una data secca (tutto il giorno)
                            continue
                        
                        # Prendi gli eventi da adesso in poi
                        if dt >= now:
                            events.append({
                                "title": str(summary),
                                "time": dt.strftime("%H:%M")
                            })
            # Ordina e prendi i primi 4
            events = sorted(events, key=lambda x: x['time'])[:4]
    except Exception as e:
        print(f"Errore calendario: {e}")
    return events

# Generazione della pagina HTML e salvataggio immagine tramite Playwright
def main():
    weather = get_weather()
    events = get_calendar()
    
    # Leggi il template HTML
    with open("template.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    
    # Inserisci i dati dinamici nel template (personalizza in base al tuo HTML)
    html_content = html_template.replace("{{TEMP}}", str(weather["temp"]))
    
    # Scrivi un file temporaneo renderizzato
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # Usa Playwright per catturare lo screenshot
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 800})
        page.goto(f"file://{os.path.abspath('index.html')}")
        page.screenshot(path="dashboard.png")
        browser.close()
    print("Dashboard generata con successo!")

if __name__ == "__main__":
    main()
