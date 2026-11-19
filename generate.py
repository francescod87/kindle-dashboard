import os
import requests
from icalendar import Calendar
from datetime import datetime
import pytz

LAT = os.environ.get("LAT", "43.7696")
LON = os.environ.get("LON", "11.2558")
ICAL_URL = os.environ.get("ICAL_URL", "")

def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,weather_code&timezone=auto"
        res = requests.get(url).json()
        current_temp = res['current']['temperature_2m']
        return f"{current_temp}°C"
    except Exception as e:
        print(f"Errore meteo: {e}")
        return "--°C"

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

def main():
    temp = get_weather()
    events = get_calendar()
    
    tz = pytz.timezone('Europe/Rome')
    last_update = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    
    # HTML di test forzato per verificare la generazione corretta dell'immagine
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                width: 600px;
                height: 800px;
                margin: 0;
                padding: 40px;
                background-color: white;
                color: black;
                font-family: Arial, sans-serif;
                box-sizing: border-box;
            }}
            h1 {{ font-size: 32px; border-bottom: 2px solid black; padding-bottom: 10px; }}
            .box {{ font-size: 24px; margin-top: 20px; }}
            ul {{ font-size: 20px; line-height: 1.6; }}
            .footer {{ position: absolute; bottom: 40px; font-size: 16px; color: #555; }}
        </style>
    </head>
    <body>
        <h1>Kindle Dashboard</h1>
        <div class="box"><b>Temperatura:</b> {temp}</div>
        <div class="box"><b>Prossimi eventi:</b></div>
        <ul>
            {events}
        </ul>
        <div class="footer">Ultimo aggiornamento: {last_update}</div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 800})
        page.goto(f"file://{os.path.abspath('index.html')}")
        page.screenshot(path="dashboard.png")
        browser.close()
    print("Dashboard generata correttamente!")

if __name__ == "__main__":
    main()
