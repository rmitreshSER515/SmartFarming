# backend/scripts/check_crops.py
# Find out what crops are actually in your CSV

import pandas as pd
import os

BASE = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE, "data", "kbs_2024.csv")

print("Reading CSV file...")
df = pd.read_csv(CSV_PATH, sep=",")

print("\n" + "="*70)
print("UNIQUE CROPS IN YOUR DATA:")
print("="*70)

unique_crops = df['Crop'].dropna().unique()

for i, crop in enumerate(unique_crops, 1):
    print(f"{i}. {crop}")

print(f"\nTotal unique crops: {len(unique_crops)}")

print("\n" + "="*70)
print("SAMPLE ROWS (first 5):")
print("="*70)
print(df[['Year', 'PlotID', 'Crop']].head())

print("\n" + "="*70)
print("CROP VALUE COUNTS:")
print("="*70)
print(df['Crop'].value_counts())