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
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,weather_code&timezone=auto"
        res = requests.get(url).json()
        current_temp = res['current']['temperature_2m']
        return {"temp": f"{current_temp}°C"}
    except Exception as e:
        print(f"Errore meteo: {e}")
        return {"temp": "--°C"}

# 2. Recupero Calendario (iCal)
def get_calendar():
    events_html = ""
    try:
        if ICAL_URL:
            url = ICAL_URL.replace("webcal://", "https://")
            cal_data = requests.get(url).text
            cal = Calendar.from_ical(cal_data)
            
            tz = pytz.timezone('Europe/Rome')
            now = datetime.now(tz)
            events = []
            
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
                            continue
                        
                        if dt >= now:
                            events.append({
                                "title": str(summary),
                                "time": dt.strftime("%H:%M")
                            })
            
            events = sorted(events, key=lambda x: x['time'])[:4]
            if events:
                for ev in events:
                    events_html += f"<li><b>{ev['time']}</b> - {ev['title']}</li>"
            else:
                events_html = "<li>Nessun evento imminente</li>"
    except Exception as e:
        print(f"Errore calendario: {e}")
        events_html = "<li>Errore caricamento calendario</li>"
    
    return events_html

# Generazione della pagina HTML e salvataggio immagine tramite Playwright
def main():
    weather = get_weather()
    events_list = get_calendar()
    
    # Orario corrente per forzare l'aggiornamento grafico dell'immagine
    tz = pytz.timezone('Europe/Rome')
    last_update = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    
    # Leggi il template HTML dal repository
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    else:
        html_template = "<html><body style='font-family:sans-serif; padding:40px;'><h1>Dashboard Kindle</h1><p>Aggiornato il: {{UPDATE_TIME}}</p><p>Temperatura: {{TEMP}}</p><ul>{{EVENTS}}</ul></body></html>"
    
    # Sostituisci i placeholder nel template (inclusa la gestione di eventuali tag personalizzati)
    html_content = html_template.replace("{{TEMP}}", weather["temp"])
    html_content = html_content.replace("{{EVENTS}}", events_list)
    html_content = html_content.replace("{{UPDATE_TIME}}", last_update)
    
    # Scrivi il file index.html locale
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
    print("Dashboard generata e salvata correttamente!")

if __name__ == "__main__":
    main()
