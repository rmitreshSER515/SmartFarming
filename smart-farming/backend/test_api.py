#!/usr/bin/env python3
"""
Quick test of Flask API endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_endpoint(name, endpoint):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"Response keys: {list(data.keys())}")
            
            # Show some data
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                    if value and len(value) > 0:
                        print(f"    First item: {value[0]}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {url}")
    except Exception as e:
        print(f"✗ Error: {e}")

# Test all endpoints
print("Starting API tests...")
time.sleep(1)

endpoints = [
    ("List Plots", "/api/plots"),
    ("Legume Crops", "/api/crops/legumes"),
    ("Cereal Crops", "/api/crops/cereals"),
    ("Needs Fertilizer", "/api/recommendations/needs-fertilizer"),
    ("Postpone Fertilizer", "/api/recommendations/postpone-fertilizer"),
    ("High Pest Risk", "/api/recommendations/high-pest-risk"),
    ("Next Crop Recommendations", "/api/recommendations/next-crop"),
]

for name, endpoint in endpoints:
    test_endpoint(name, endpoint)

# Test specific plot
print(f"\n{'='*60}")
print("Testing: Specific Plot (T1_R1/2015)")
print(f"{'='*60}")
test_endpoint("Plot Summary T1_R1/2015", "/api/plots/T1_R1/year/2015")

print("\n" + "="*60)
print("Tests complete!")
print("="*60)
