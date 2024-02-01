PYTHON = python
SPEC = QuestScraper.spec

all: QuestScraper.py calendar_scraper.py
	pyinstaller --onefile --windowed QuestScraper.py

clean:
	rm -rf dist build