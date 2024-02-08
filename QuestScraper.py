import os
from gooey import Gooey, GooeyParser
from calendar_scraper import scrape_blotter, scrape_events
from enum import Enum
from dateutil.parser import parse as date_parse


class Sites(Enum):
    blotter = "blotter"
    events = "events"

    def __str__(self):
        return self.value


@Gooey(progress_regex=r"^progress: (-?\d+)%$",
       hide_progress_msg=True)
def main():
    parser = GooeyParser(
        prog="QuestScraper",
        description="Web crawler that extracts information from the Reed College Blotter and Events Calendar",
    )

    parser.add_argument(
        "output_dir",
        help="The directory to output the saved data to",
        widget="DirChooser",
        gooey_options={"initial_value": os.getcwd()},
    )
    parser.add_argument(
        "target_site",
        help="Which of the sites should be scraped",
        type=Sites,
        choices=list(Sites),
    )

    time_group = parser.add_argument_group(
        "Time Options",
        "Customize the dates that the scraper will look for (Only effects events data)",
    )
    time_group.add_argument(
        "-s",
        "--start-date",
        help="The earliest an event should be collected (default today)",
        required=False,
        widget="DateChooser",
    )
    time_group.add_argument(
        "-d",
        "--days",
        help="The number of days ahead to look for events",
        required=False,
        widget="IntegerField",
        gooey_options={"min": 1, "max": 14, "initial_value": 7},
    )

    format_group = parser.add_argument_group(
        "Format Options", "Customize how the output file is formatted"
    )
    format_group.add_argument(
        "--max-words",
        help="The max number of words to be written to the markdown file per entry",
        widget="IntegerField",
        gooey_options={"max": 10000, "initial_value": 200},
    )
    args = parser.parse_args()
    print(args)

    if args.target_site == Sites.blotter:
        scrape_blotter(args.output_dir, int(args.max_words))
    elif args.target_site == Sites.events:
        scrape_events(
            args.output_dir,
            date_parse(args.start_date).date(),
            int(args.days),
            int(args.max_words),
        )


if __name__ == "__main__":
    main()
