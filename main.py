from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
import time

def am_pm(events):
    for event in events:
        event['start_time'], event['end_time'] = event['time'].split(" - ")

        parts = event['start_time'].split(" ")
        start_time   = parts[0]  # format 'hh:mm'
        start_period = parts[1]  # AM or PM

        start_h, start_m = start_time.split(":")
         
        parts = event['end_time'].split(" ")
        end_time   = parts[0]  # format 'hh:mm'
        end_period = parts[1]  # AM or PM

        end_h, end_m = end_time.split(":")
        
        if start_period == 'PM' and start_h != '12':
            event['start_h'] = int(start_h) + 12
        else:
            event['start_h'] = int(start_h)

        if end_period == 'PM' and end_h != '12':
            event['end_h'] = int(end_h) + 12
        else:
            event['end_h'] = int(end_h)

        event['start_m'] = start_m
        event['end_m']   = end_m
    
    return events

def extract_event_details(all_html):
    all_events = []
    
    for html in all_html:
        soup = BeautifulSoup(html, 'html.parser')
        events = soup.find_all("div", class_="fc-time")
        
        for event in events:
            event_details = {}
            # Extract time
            event_details["time"] = event.get_text(strip=True)
            
            # Extract title and other details
            next_sibling = event.find_next_sibling(string=True)
            details = []
            while next_sibling and next_sibling.strip():
                details.append(next_sibling.strip())
                next_sibling = next_sibling.find_next_sibling(string=True)
            
            if details:
                event_details["title"] = details[0]
                event_details["details"] = details[1:]
            
            all_events.append(event_details)
        
        all_events = am_pm(all_events)
        
    return all_events

def create_ics(events, year, month, day, lesson_a_day):
    calendar = Calendar()

    count_day = 0
    count_event = 0
    more_days = 0

    for event in events:

        if count_event == lesson_a_day[count_day]:
            more_days += 1
            count_day += 1
            count_event = 0

        e = Event()
        e.name = event.get("title", "No Title")
        
        if "details" in event:
            e.description = " | ".join(event["details"])
        
        # Assuming time is in 24-hour format for simplicity, adapt as needed
        start_time = datetime(int(year), int(month), int(day) + more_days, int(event['start_h']), int(event['start_m']), tzinfo=pytz.UTC)
        end_time   = datetime(int(year), int(month), int(day) + more_days, int(event['end_h']), int(event['end_m']), tzinfo=pytz.UTC)

        e.begin = start_time
        e.end = end_time

        calendar.events.add(e)

        count_event += 1

    with open('calendar.ics', 'w') as f:
        f.writelines(calendar)
    print("ICS file created: calendar.ics")

def scrap():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto('https://services-web.cyu.fr/calendar/LdapLogin')

        time.sleep(1)

        # login
        page.fill('input#Name', 'e-mbrosset')
        page.fill('input#Password', 'yUM2)5)G')
        page.click('button[type=submit]')

        time.sleep(1)

        # Click on week button
        page.click('button.fc-agendaWeek-button.fc-button.fc-state-default')
        print("Clicked on the week button")
        time.sleep(1)

        # Click on previous button
        for _ in range(4):
            page.click('button.fc-prev-button.fc-button.fc-state-default.fc-corner-left')
            print("Clicked on the previous button")
            time.sleep(1)

        # Scraping
        divs = page.query_selector_all("div.fc-content")
        all_html = [div.inner_html() for div in divs]
        
        # Extract details from all_html
        all_events = extract_event_details(all_html)

        # Extract date
        date_element = page.query_selector("th.fc-day-header.fc-widget-header.fc-mon.fc-past")
        data_date = date_element.get_attribute("data-date")
        year, month, day = data_date.split('-')
        print(f"Year: {year}, Month: {month}, Day: {day}")

        lessons = page.query_selector_all("div.fc-event-container")
        lesson_a_day = []

        for i in range(len(lessons)):
            events = lessons[i].query_selector_all("a.fc-time-grid-event")
            
            content_count = 0

            if i == 1 or i == 3 or i == 5 or i == 7 or i == 9:
                for event in events:
                    contents = event.query_selector_all("div.fc-content")
                    
                    content_count += len(contents)
                lesson_a_day.append(content_count)
                print(f'Nombre de div.fc-content dans ce div.fc-event-container: {content_count}')







        # Create ICS file
        create_ics(all_events, year, month, day, lesson_a_day)

        time.sleep(5)
        browser.close()

scrap()
