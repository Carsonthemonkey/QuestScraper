import os
from datetime import date, timedelta, datetime
from tqdm import tqdm
import re
import requests
from dateutil.parser import parse as date_parse
from bs4 import BeautifulSoup
from bs4.element import Tag
import json

EVENTS_URL = "https://events.reed.edu/calendar"
BLOTTER_URL = 'https://www.reed.edu/community_safety/blotters/the-blotter.html'

def get_page_source(url):
    """
    Retrieves the page source of the given URL.

    Args:
        url (str): The URL of the page to retrieve.

    Returns:
        str: The page source as a string.
    """
    response = requests.get(url, timeout=15)
    source = response.text
    return BeautifulSoup(source, features='html.parser')


def fetch_description(url):
    soup = get_page_source(url)
    try:
        description = soup.find(class_="em-about_description").get_text().strip() 
        return description
    except AttributeError as e:
    #    print(soup.find(class_="em-about_description").p.prettify())
       raise AttributeError(f"page '{url}' has no description") from e


def get_relevant_event_cards(soup, start_day: date, day_num: int):
    events = soup.find(id="event_results")

    cutoff_date = start_day + timedelta(days=day_num)
    assert isinstance(cutoff_date, date)
    relevant_groups = []
    dates = events.find_all("h2")
    cards = events.find_all("div", class_="em-card-group")
    for event_date, card_group in zip(dates, cards):
        event_dt = date_parse(event_date.contents[0])
        print(type(event_dt.date()))
        if event_dt.date() > cutoff_date:
            break
        relevant_groups.append(card_group)

    # Parse each cards in the relavent groups
    cards = []
    for group in relevant_groups:
        full_cards = group.find_all(class_="em-card")
        cards.extend([card.contents[3] for card in full_cards])
    return cards


def parse_card(card: Tag):
    event_title = card.h3.a.text.strip()
    print(card.p)
    event_description = fetch_description(card.h3.a.attrs["href"])

    tags = card.find_all("p")
    date_tag = tags[0]
    location_tag = tags[1] if len(tags) > 1 else None

    date_time_split_index = re.search(r"\d{4}", date_tag.text).end()
    event_date = date_tag.text[:date_time_split_index].strip()
    event_time = date_tag.text[date_time_split_index:].strip()
    event_location = location_tag.text.strip() if location_tag is not None else None
    return {
        "title": event_title,
        "date": event_date,
        "time": event_time,
        "location": event_location,
        "description": event_description,
    }


def scrape_events(save_path: str, days, max_words):
    cards = get_relevant_event_cards(get_page_source(EVENTS_URL), date.today(), days)
    event_data = []
    for i, card in enumerate(cards):
        event_data.append(parse_card(card))
    with open(f"{save_path}/{str(date.today())}-event-scrape.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(event_data, indent=4))

    with open(f"{save_path}/{str(date.today())}-events-readable.md", "w", encoding="utf-8") as f:
        prev_date = None
        written_descriptions = []
        for event in event_data:
            f.write(f"# {event['date']}" if event['date'] != prev_date else "")
            f.write('\n')
            f.write(f"**{event['title']} ({event['time']} @ {event['location']})**\n\n")
            if event['description'] not in written_descriptions:
                written_descriptions.append(event['description'])
                if len(event['description'].split(' ')) > max_words:
                    sentences = event['description'].split('.')
                    current_length = 0
                    for sentence in sentences:
                        if current_length > max_words:
                            break
                        f.write(sentence)   
                        current_length += len(sentence)
                else:
                    f.write(event['description'])
            f.write('\n')
            f.write('\n---\n')
            prev_date = event['date']
    print(f"saved files to {os.getcwd()}")


# Blotter Scraping

def parse_blotter(soup):
    main_content = soup.find(id='mainContent')
    date_range = main_content.find('p', class_='lead').text

    paragraphs = main_content.find_all('p')[8:]
    paragraphs = list(filter(lambda x: 'VOID REPORT' not in x.text, paragraphs))
    # for p in paragraphs:
    #     print(p.prettify())
    cases = []
    for i in range(0, len(paragraphs), 2):
        spans = paragraphs[i].find_all('span')
        if not spans:
            break
        num = spans[1].text.strip()
        case_date = spans[3].text.strip()
        time = spans[5].text.strip()
        description = spans[7].text.strip()
        location = spans[9].text.strip()

        notes = paragraphs[i + 1].find_all('span')[1].text.strip()
        cases.append({
            'case_number': num,
            'date': str(date_parse(case_date))[:11] + time, # messy but whatever
            'description': description,
            'location': location,
            'notes': notes
        })
    return (date_range, cases)

def scrape_blotter(save_path: str, max_words):
    source = get_page_source(BLOTTER_URL)
    date_range, cases = parse_blotter(source)
    
    with open(f'{save_path}/{str(date.today())}-blotter-scrape.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(cases, indent=4))
    
    with open(f'{save_path}/{str(date.today())}-blotter-readable.md', 'w', encoding='utf-8') as f:
        f.write(f'## {date_range}\n\n')
        for case in cases:
            readable_date = datetime.strptime(case['date'], '%Y-%m-%d %H:%M').strftime('%A, %B %d, %Y')
            f.write(f'## {readable_date} \n\n')
            f.write(f'**{case['case_number']}; {case['description']}; {case['location']}**\n\n')
            if len(case['notes']) > max_words:
                word_num = 0
                f.write('"Notes: ')
                for sentence in case['notes'].split('.'):
                    if word_num > max_words:
                        break
                    f.write(sentence)
                    word_num += len(sentence)
                f.write('"\n\n')
            else:
                f.write(f'"Notes: {case['notes']}"\n\n')
    
if __name__ == "__main__":
    scrape_events(os.getcwd(), 7,  200)

    # scrape_events(lambda _: _, os.getcwd(), 7, 200)