import csv
import os
from collections import Counter
from tkinter import filedialog

default_folder = "Lists/People"

file_path = filedialog.askopenfilename(initialdir=default_folder, filetypes=[("CSV files", "*.csv")])

with open(file_path, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    titles = [row['jobTitle'] for row in rows]
    companies = [row['companyName'] for row in rows]

title_counts = Counter(titles)
sorted_titles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)

company_counts = Counter(companies)
sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)

base_name = os.path.splitext(os.path.basename(file_path))[0]
output_dir = "Outputs"
os.makedirs(output_dir, exist_ok=True)

titles_path = os.path.join(output_dir, f"{base_name} (titles).csv")
with open(titles_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['jobTitle', 'count', 'newJobTitle'])
    writer.writerows([title, count, ''] for title, count in sorted_titles)

companies_path = os.path.join(output_dir, f"{base_name} (companies).csv")
with open(companies_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['companyName', 'count', 'newCompanyName'])
    writer.writerows([company, count, ''] for company, count in sorted_companies)