import csv
from collections import Counter
from tkinter import filedialog

default_folder = "Lists/People"

file_path = filedialog.askopenfilename(initialdir=default_folder, filetypes=[("CSV files", "*.csv")])

with open(file_path, 'r') as f:
    reader = csv.DictReader(f)
    titles = [row['Title'] for row in reader]

title_counts = Counter(titles)
sorted_titles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)

output_path = file_path.replace('.csv', '_unique_titles.csv')
with open(output_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Count'])
    writer.writerows(sorted_titles)

