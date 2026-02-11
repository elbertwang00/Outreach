import pandas as pd
from pathlib import Path
from tkinter import filedialog, Tk

repo_root = Path(__file__).parent
root = Tk()
root.withdraw()

# Choose replacement CSV
replacement_path = Path(filedialog.askopenfilename(initialdir=repo_root / "Inputs", title="Select replacement CSV", filetypes=[("CSV files", "*.csv")]))

# Choose prospects CSV
people_path = Path(filedialog.askopenfilename(initialdir=repo_root / "Lists" / "People", title="Select prospects CSV", filetypes=[("CSV files", "*.csv")]))

# Load CSVs
replacements = pd.read_csv(replacement_path)
prospects = pd.read_csv(people_path)

# Create mapping dict
title_map = dict(zip(replacements['Old Title'], replacements['New Title']))

# Delete rows where Old Title exists but New Title is empty
mapped = prospects['Title'].map(title_map)
prospects = prospects[~((prospects['Title'].isin(title_map.keys())) & (mapped.isna() | (mapped == '')))]

# Replace titles
prospects['Title'] = prospects['Title'].map(title_map).fillna(prospects['Title'])

# Save
output_path = people_path.parent / f"{people_path.stem} (titles replaced).csv"
prospects.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")

