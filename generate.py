import os
import requests
from icalendar import Calendar
from datetime import datetime
import pytz

LAT = os.environ.get("LAT", "43.7696")
LON = os.environ.get("LON", "11.2558")
ICAL_URL = os.environ.get("ICAL_URL", "")

# 1. Meteo Avanzato (Corrente + Min/Max giornaliere)
def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        res = requests.get(url).json()
        current = res['current']['temperature_2m']
        t_max = res['daily']['temperature_2m_max'][0]
        t_min = res['daily']['temperature_2m_min'][0]
        return {
            "current": f"{current}°C",
            "forecast": f"Min: {t_min}°C / Max: {t_max}°C"
        }
    except Exception as e:
        print(f"Errore meteo: {e}")
        return {"current": "--°C", "forecast": "N/D"}

# 2. Santo del giorno
def get_saint():
    saints = {
        "01-01": "Maria SS. Madre di Dio", "01-06": "Epifania del Signore", "03-19": "San Giuseppe",
        "04-25": "San Marco Evangelista", "05-01": "San Giuseppe Lavoratore", "06-24": "San Giovanni Battista",
        "06-29": "Santi Pietro e Paolo", "08-15": "Assunzione di Maria", "11-01": "Tutti i Santi",
        "11-02": "Commemorazione dei Defunti", "12-08": "Immacolata Concezione", "12-25": "Natale del Signore"
    }
    today_key = datetime.now().strftime("%m-%d")
    return saints.get(today_key, "Santo del Giorno protettore della famiglia")

# 3. Aforisma del giorno (Corretto con tm_yday)
def get_aphorism():
    quotes = [
        "Il modo per iniziare è smettere di parlare e iniziare a fare. (Walt Disney)",
        "Chi cerca la Verità è libero; chi la crede posseduta è schiavo. (A. T.)",
        "La vita è ciò che ti accade mentre sei occupato a fare altri progetti. (John Lennon)",
        "Il futuro appartiene a coloro che credono nella bellezza dei propri sogni. (Eleanor Roosevelt)",
        "Non giudicare ogni giorno dal raccolto che mieti, ma dai semi che pianti. (R. L. Stevenson)",
        "Agisci come se quello che fai potesse fare la differenza. Lo fa. (William James)",
        "L'istruzione è l'arma più potente che puoi usare per cambiare il mondo. (Nelson Mandela)"
    ]
    day_of_year = datetime.now().timetuple().tm_yday
    return quotes[day_of_year % len(quotes)]

# 4. Calendario iCal
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
            events = sorted(events, key=lambda x: x['time'])[:3]
            if events:
                for ev in events:
                    events_html += f"<li><b>{ev['time']}</b> - {ev['title']}</li>"
            else:
                events_html = "<li>Nessun evento imminente</li>"
    except Exception as e:
        print(f"Errore calendario: {e}")
        events_html = "<li>Errore caricamento calendario</li>"
    return events_html

def main():
    weather = get_weather()
    saint = get_saint()
    aphorism = get_aphorism()
    events = get_calendar()
    
    tz = pytz.timezone('Europe/Rome')
    last_update = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    
    day_seed = datetime.now().strftime("%Y%m%d")
    photo_url = f"https://picsum.photos/seed/{day_seed}/758/300"
    
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    else:
        html_template = "<html><body><h1>Errore template</h1></body></html>"
    
    html_content = html_template.replace("{{TEMP_CURRENT}}", weather["current"])
    html_content = html_content.replace("{{TEMP_FORECAST}}", weather["forecast"])
    html_content = html_content.replace("{{SAINT}}", saint)
    html_content = html_content.replace("{{APHORISM}}", aphorism)
    html_content = html_content.replace("{{PHOTO_URL}}", photo_url)
    html_content = html_content.replace("{{EVENTS}}", events)
    html_content = html_content.replace("{{UPDATE_TIME}}", last_update)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 758, "height": 1024})
        page.goto(f"file://{os.path.abspath('index.html')}")
        page.screenshot(path="dashboard.png")
        browser.close()
    print("Dashboard avanzata generata con successo!")

if __name__ == "__main__":
    main()
