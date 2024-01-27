import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
from calendar_scraper import scrape_events, scrape_blotter

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_path)

def start_blotter_scrape():
    thread = threading.Thread(target=lambda: scrape_blotter(update_progress_bar, path_entry.get(), int(max_words_spinbox.get())))
    thread.start()


def validate_input(P):
    if P.isdigit() or P == "":
        return True
    else:
        return False

def update_progress_bar(progress_percent):
    pb['value'] = progress_percent * 100
    check_button_active_conditions()

def start_event_scrape():
    thread = threading.Thread(target=lambda: scrape_events(update_progress_bar, path_entry.get(), int(days_spinbox.get()), int(max_words_spinbox.get())))
    thread.start()

def check_button_active_conditions():
    # Assuming `path` is the variable storing the specified path
    # and `pb` is the progress bar
    if not path_entry.get() or not days_spinbox.get() or not max_words_spinbox.get() or pb["value"] != 0:
        button1.config(state=tk.DISABLED)
        button2.config(state=tk.DISABLED)
    else:
        button1.config(state=tk.NORMAL)
        button2.config(state=tk.NORMAL)

# Create the main window
root = tk.Tk()
root.title("QuestScraper")



style = ttk.Style(root)
style.theme_use("clam")

# Validation command
vcmd = (root.register(validate_input), '%P')

# Folder selection frame
folder_frame = tk.Frame(root)
folder_frame.pack(pady=10)

# Create a button and entry for selecting a folder
# Output folder label
output_folder_label = tk.Label(folder_frame, text="Output Folder:")
output_folder_label.pack()

select_folder_button = ttk.Button(folder_frame, text="Select Folder", command=select_folder)
select_folder_button.pack(side=tk.LEFT, padx=5)

path_var = tk.StringVar()
path_var = tk.StringVar(value=os.getcwd())
path_entry = ttk.Entry(folder_frame, width=50, textvariable=path_var)
path_var.trace_add('write', lambda *args: check_button_active_conditions())
path_entry.pack(side=tk.LEFT, padx=5)

# Config section
config_label = tk.Label(root, text="Config", font=("Arial", 16))
config_label.pack(pady=5)

# Days input
days_label = tk.Label(root, text="Days:")
days_label.pack()
day_var = tk.StringVar(value="7")
days_spinbox = ttk.Spinbox(root, from_=0, to=1000, increment=1, validate="key", validatecommand=vcmd, textvariable=day_var)
day_var.trace_add('write', lambda *args: check_button_active_conditions())
days_spinbox.pack()

# Max words input
max_words_label = tk.Label(root, text="Max Words:")
max_words_label.pack()
words_var = tk.StringVar(value="200")
max_words_spinbox = ttk.Spinbox(root, from_=0, to=10000, increment=1, validate="key", validatecommand=vcmd, textvariable=words_var)
words_var.trace_add('write', lambda *args: check_button_active_conditions())
max_words_spinbox.pack()

button_frame = tk.Frame(root)
button_frame.pack(pady=10)
# Create two additional buttons
button1 = ttk.Button(button_frame, text="Scrape Events", command=start_event_scrape)
button1.pack(side=tk.LEFT,pady=5)

button2 = ttk.Button(button_frame, text="Scrape Blotter", command=start_blotter_scrape)
button2.pack(pady=5)


pb = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
pb.pack(pady=10)

check_button_active_conditions()
# Run the application
root.mainloop()
