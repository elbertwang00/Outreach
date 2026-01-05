#!/usr/bin/env python3
"""
Script to count the number of people per company from people.csv
Outputs a CSV file with company name and count, sorted by count descending.
Includes all companies from companies.csv, even if they have zero people.
"""

import csv
from collections import defaultdict

def count_people_by_company(companies_file='companies.csv', people_file='people.csv', output_file='company_people_count.csv', companies_only=False):
    """
    Count people by company name (case-insensitive) and output to CSV.
    Includes all companies from companies.csv, even if they have zero people.
    
    Args:
        companies_file: Path to the companies.csv file
        people_file: Path to the input people.csv file
        output_file: Path to the output CSV file
        companies_only: If True, only include companies that exist in companies.csv
    """
    # Dictionary to store counts and titles (key: lowercase company name, value: (original_name, count, titles, total_employees, from_companies_csv))
    company_counts = defaultdict(lambda: {'original_name': None, 'count': 0, 'total_employees': None, 'titles': set(), 'from_companies_csv': False})
    
    # First, read all companies from companies.csv and initialize them with count 0
    with open(companies_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            company_name = row.get('Company Name', '').strip()
            
            # Skip empty company names
            if not company_name:
                continue
            
            # Use lowercase as key for case-insensitive matching
            company_key = company_name.lower()
            
            # Store the original case from companies.csv
            if company_counts[company_key]['original_name'] is None:
                company_counts[company_key]['original_name'] = company_name
                company_counts[company_key]['count'] = 0
                company_counts[company_key]['titles'] = set()
                company_counts[company_key]['from_companies_csv'] = True
                
                # Get total employees count
                employees_str = row.get('# Employees', '').strip()
                try:
                    company_counts[company_key]['total_employees'] = int(employees_str) if employees_str else None
                except ValueError:
                    company_counts[company_key]['total_employees'] = None
    
    # Then, read the people.csv file and increment counts and collect titles
    with open(people_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            company_name = row.get('Company Name', '').strip()
            
            # Skip empty company names
            if not company_name:
                continue
            
            # Use lowercase as key for case-insensitive matching
            company_key = company_name.lower()
            
            # If company not in companies.csv, add it (preserve original case from people.csv)
            if company_counts[company_key]['original_name'] is None:
                company_counts[company_key]['original_name'] = company_name
            
            # Increment count
            company_counts[company_key]['count'] += 1
            
            # Add title if it exists
            title = row.get('Title', '').strip()
            if title:
                company_counts[company_key]['titles'].add(title)
    
    # Collect all unique titles across all companies
    all_unique_titles = set()
    for data in company_counts.values():
        all_unique_titles.update(data['titles'])
    
    # Convert to list of tuples and sort by count descending, then by company name
    results = []
    for data in company_counts.values():
        # If companies_only is True, skip companies that weren't in companies.csv
        if companies_only and not data['from_companies_csv']:
            continue
        
        # Convert titles set to sorted list and join with ", "
        titles_str = ", ".join(sorted(data['titles'])) if data['titles'] else ""
        
        # Calculate percentage of employees in people list
        total_employees = data['total_employees']
        if total_employees and total_employees > 0:
            percentage = (data['count'] / total_employees) * 100
            percentage_str = f"{percentage:.2f}%"
        else:
            percentage_str = "N/A"
        
        results.append((data['original_name'], data['count'], percentage_str, titles_str))
    
    # Sort by count descending, then by company name ascending (for ties)
    results.sort(key=lambda x: (-x[1], x[0]))
    
    # Write to output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Company Name', 'Number of People', 'Percentage of Employees', 'Titles'])
        writer.writerows(results)
    
    # Write unique titles to text file
    titles_output_file = output_file.replace('.csv', '_unique_titles.txt')
    with open(titles_output_file, 'w', encoding='utf-8') as f:
        for title in sorted(all_unique_titles):
            f.write(title + '\n')
    
    print(f"Successfully processed {len(results)} companies")
    print(f"Output written to {output_file}")
    print(f"Unique titles written to {titles_output_file} ({len(all_unique_titles)} unique titles)")

if __name__ == '__main__':
    count_people_by_company(companies_only=True)

