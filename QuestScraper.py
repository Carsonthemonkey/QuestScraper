from gooey import Gooey, GooeyParser


@Gooey
def main():
    parser = GooeyParser(
        prog="QuestScraper",
        description="Web crawler that extracts information from the Reed College Blotter and Events Calendar",
    )

    parser.add_argument(
        "Output Directory",
        help="The directory to output the saved data to",
        widget="DirChooser",
    )
    parser.add_argument(
        "Target Site",
        help="Which of the sites should be scraped",
        choices=["events", "blotter"],
    )

    time_group = parser.add_argument_group(
        "Time Options", "Customize the dates that the scraper will look for"
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


if __name__ == "__main__":
    main()
