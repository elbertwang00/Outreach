import csv

# Read companies.csv to create a mapping of company name to website
company_website_map = {}
with open('companies.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        company_name = row['Company Name'].strip()
        website = row['Website'].strip()
        # Store with normalized key (lowercase for case-insensitive matching)
        company_website_map[company_name.lower()] = website

# Read bad_prospects_companies.csv and get websites
websites = []
with open('bad_prospects_companies.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        # If Website column exists, use it; otherwise look it up
        if 'Website' in row and row['Website'].strip():
            website = row['Website'].strip()
        else:
            company_name = row['Company Name'].strip()
            # Try to find website (case-insensitive)
            website = company_website_map.get(company_name.lower(), '')
        websites.append({'Website': website})

# Write back to bad_prospects_companies.csv with only Website column
with open('bad_prospects_companies.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Website'])
    writer.writeheader()
    writer.writerows(websites)

print(f"Saved Website column only to bad_prospects_companies.csv")
print(f"Processed {len(websites)} companies")

