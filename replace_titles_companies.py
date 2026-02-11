import pandas as pd
from pathlib import Path
from tkinter import filedialog, Tk

repo_root = Path(__file__).parent
root = Tk()
root.withdraw()

replacement_path = Path(filedialog.askopenfilename(initialdir=repo_root / "Inputs", title="Select job title replacement CSV", filetypes=[("CSV files", "*.csv")]))
company_path = Path(filedialog.askopenfilename(initialdir=repo_root / "Inputs", title="Select company name replacement CSV", filetypes=[("CSV files", "*.csv")]))
people_path = Path(filedialog.askopenfilename(initialdir=repo_root / "Lists" / "People", title="Select prospects CSV", filetypes=[("CSV files", "*.csv")]))

replacements = pd.read_csv(replacement_path)
companies = pd.read_csv(company_path)
prospects = pd.read_csv(people_path)

title_map = dict(zip(replacements['jobTitle'], replacements['newJobTitle']))
company_map = dict(zip(companies['companyName'], companies['newCompanyName']))

mapped_titles = prospects['jobTitle'].map(title_map)
prospects = prospects[~((prospects['jobTitle'].isin(title_map.keys())) & (mapped_titles.isna() | (mapped_titles == '')))]
prospects['cleanJobTitle'] = prospects['jobTitle'].map(title_map).fillna(prospects['jobTitle'])

mapped_companies = prospects['companyName'].map(company_map)
prospects = prospects[~((prospects['companyName'].isin(company_map.keys())) & (mapped_companies.isna() | (mapped_companies == '')))]
prospects['cleanCompanyName'] = prospects['companyName'].map(company_map).fillna(prospects['companyName'])

output_path = people_path.parent / f"{people_path.stem} (CLEANED).csv"
prospects.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")

