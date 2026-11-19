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

# 1. Recupera Meteo da Open-Meteo
def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FRome"
        r = requests.get(url).json()
        curr = round(r["current_weather"]["temperature"])
        t_max = round(r["daily"]["temperature_2m_max"][0])
        t_min = round(r["daily"]["temperature_2m_min"][0])
        return curr, t_min, t_max, "Aggiornato"
    except Exception as e:
        print("Errore meteo:", e)
        return "--", "--", "--", "Meteo non disp."

# 2. Recupera Eventi da Google Calendar (.ics)
def get_calendar_events():
    if not ICAL_URL:
        return "<li>Nessun calendario configurato (imposta ICAL_URL)</li>"
    try:
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
        return "".join(events_html) if events_html else "<li>Nessun evento in programma oggi</li>"
    except Exception as e:
        print("Errore calendario:", e)
        return "<li>Errore nel caricamento del calendario</li>"

# 3. Foto del giorno (Placeholder di qualità in scala di grigi o URL personalizzabile)
def get_photo():
    # Usa un'immagine fissa o un servizio di foto casuali ad alto contrasto
    return "https://picsum.photos/758/340?grayscale"

# 4. Santo e Aforisma del giorno
def get_saint_and_quote():
    santi = {
        "19-11": "San Ponziano, San Barlaam e Sant'Abdia",
        "20-11": "San Felice di Valois e Sant'Edmondo",
        "21-11": "Presentazione della Beata Vergine Maria",
        "22-11": "Santa Cecilia",
        "23-11": "San Clemente I e San Colombano"
    }
    oggi_key = datetime.date.today().strftime("%d-%m")
    santo = santi.get(oggi_key, "Santo del giorno")
    
    aforismi = [
        "La semplicità è la sofisticazione massima. — Leonardo da Vinci",
        "Non conta quanto lentamente vai, purché tu non ti fermi. — Confucio",
        "Il modo migliore per predire il futuro è crearlo. — Peter Drucker",
        "Chi cerca la verità non deve temere di trovarla. — Anonimo",
        "Fai quello che puoi, con quello che hai, là dove sei. — Theodore Roosevelt"
    ]
    return santo, random.choice(aforismi)

def main():
    now = datetime.datetime.now()
    giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre"]
