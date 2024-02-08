import os
import warnings
from datetime import date, timedelta, datetime
import re
import requests
from dateutil.parser import parse as date_parse
from bs4 import BeautifulSoup
from bs4.element import Tag
import json

BASE_EVENTS_URL = 'https://events.reed.edu/'
EVENT_CALENDAR_URL = BASE_EVENTS_URL + "calendar"
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

def save_json_data(json_data: dict, save_path: str, filename: str):
    """Saves the scrape data in JSON format"""
    with open(f'{save_path}/{filename}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_data, indent=4))
    
def fetch_event_description(url):
    soup = get_page_source(url)
    try:
        description = soup.find(class_="em-about_description").get_text().strip() 
        return description
    except AttributeError as e:
       raise AttributeError(f"page '{url}' has no description") from e


def get_relevant_event_cards(soup, start_day: date, day_num: int):
    events = soup.find(id="event_results")

    cutoff_date = start_day + timedelta(days=day_num)
    # relevant_groups = []
    dates = events.find_all("h2")
    card_groups = events.find_all("div", class_="em-card-group")
    cards = []
    for event_date, card_group in zip(dates, card_groups):
        event_dt = date_parse(event_date.contents[0])
        if event_dt.date() < start_day:
            continue
        if event_dt.date() > cutoff_date:
            return cards
        # relevant_groups.append(card_group)
        full_cards = card_group.find_all(class_='em-card')
        cards.extend([card.contents[3] for card in full_cards]) #Why is it 3 again? seems unusual TODO: make this more readable and robust
    
    # If loop concludes before returning, we did not hit the date limit. We need to collect cards on the next page
    try:
        next_page_link = soup.find(attrs={'aria-label': 'Next page'}, class_='em-pagination-item').attrs['href']
    except AttributeError:
        warnings.warn("Could not find next page of events. May be missing", RuntimeWarning)
        return cards
    
    print('fetching next events page')
    next_page_src = get_page_source(BASE_EVENTS_URL + next_page_link)
    cards.extend(get_relevant_event_cards(next_page_src, start_day, day_num))
    return cards


    # Parse each cards in the relavent groups
    # for group in relevant_groups:
    #     full_cards = group.find_all(class_="em-card")
    #     cards.extend([card.contents[3] for card in full_cards])
    # return cards


def parse_card(card: Tag):
    event_title = card.h3.a.text.strip()
    event_description = fetch_event_description(card.h3.a.attrs["href"])

    tags = card.find_all("p")
    date_tag = tags[0]
    location_tag = tags[1] if len(tags) > 1 else None

    date_time_split_index = re.search(r"\d{4}", date_tag.text).end()
    event_date = date_tag.text[:date_time_split_index].strip()
    event_time = date_tag.text[date_time_split_index:].strip()
    event_location = location_tag.text.strip() if location_tag is not None else None
    return {
        "title": event_title,
        "date": str(date_parse(event_date)),
        "time": event_time,
        "location": event_location,
        "description": event_description,
    }


def scrape_events(save_path: str, start_day: date, day_num: int, max_words: int):
    cards = get_relevant_event_cards(get_page_source(EVENT_CALENDAR_URL), start_day, day_num)

    event_data = []
    for i, card in enumerate(cards):
        event_data.append(parse_card(card))
        print(f'progress: {int(100 * i / len(cards))}%')

    save_json_data(event_data, save_path, f'{str(date.today())}-event-scrape')

    with open(f"{save_path}/{str(date.today())}-events-readable.md", "w", encoding="utf-8") as f:
        prev_date = None
        written_descriptions = []
        for event in event_data:
            f.write(f"# {date_parse(event['date']).strftime('%A, %B %d, %Y')}" if event['date'] != prev_date else "")
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
    assert main_content is not None, "Could not find main content on blotter page"
    try:
        date_range = main_content.find('p', class_='lead').text
    except AttributeError:
        warnings.warn('No date range found for blotter page', RuntimeWarning)

    paragraphs = main_content.find_all('p')[8:]
    def filter_paragraphs(paragraph):
        return len(paragraph.find_all('span')) >= 2 and 'VOID REPORT' not in paragraph.text
    
    paragraphs = list(filter(filter_paragraphs, paragraphs))

    cases = []
    for i in range(0, len(paragraphs), 2):
        spans = paragraphs[i].find_all('span')
        if not spans:
            warnings.warn("Blotter paragraph seems to be empty", RuntimeWarning)
            continue
        case = {}
        try:
            case['case_number'] = spans[1].text.strip()
            case_date = spans[3].text.strip()
            time = spans[5].text.strip()
            case['date'] = str(date_parse(case_date))[:11] + time # TODO: make this less messy
            case['description'] = spans[7].text.strip()
            case['location'] = spans[9].text.strip()
            case['notes'] = paragraphs[i + 1].find_all('span')[1].text.strip()
        except (AttributeError, KeyError) as e:
            warnings.warn(f"Missing case data for case. Data collected:\n {case}\n Error: {e}", RuntimeWarning)
        cases.append(case)
    return (date_range, cases)

def scrape_blotter(save_path: str, max_words):
    source = get_page_source(BLOTTER_URL)
    date_range, cases = parse_blotter(source)
    
    save_json_data(cases, save_path, f'{str(date.today())}-blotter-scrape')
    
    with open(f'{save_path}/{str(date.today())}-blotter-readable.md', 'w', encoding='utf-8') as f:
        f.write(f'## {date_range}\n\n')
        for case in cases:
            case_datetime = datetime.strptime(case['date'], '%Y-%m-%d %H:%M')
            readable_date = case_datetime.strftime('%A, %B %d, %Y')
            f.write(f'## {readable_date} \n\n')
            f.write(f'**{case['case_number']}; {case_datetime.strftime('%H:%M')}; {case['description']}; {case['location']}**\n\n')
            if len(case['notes']) > max_words:
                word_num = 0
                f.write('"Notes: ')
                for sentence in case['notes'].split('.'):
                    if word_num > max_words:
                        break
                    f.write(sentence)
                    word_num += len(sentence)
            else:
                f.write(case['notes'])
            f.write('\n\n')
    
if __name__ == "__main__":
    # scrape_events(os.getcwd(),date.today(), 7,  200)
    scrape_blotter(os.getcwd(), 200)
    # scrape_events(lambda _: _, os.getcwd(), 7, 200)