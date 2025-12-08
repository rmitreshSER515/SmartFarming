# backend/scripts/test_python_classification.py
# Classify crops using Python logic instead of SWRL
# This is BETTER than SWRL for your use case!

from owlready2 import *
import os
import time

BASE = os.path.dirname(os.path.dirname(__file__))
ONTOLOGY_PATH = os.path.join(BASE, "ontology", "smart-farming.owl")

test_files = [
    "instances_tiny.owl",
    "instances_small.owl", 
    "instances_medium.owl",
]

print("="*70)
print("PYTHON-BASED CROP CLASSIFICATION (No SWRL)")
print("="*70)

for test_file in test_files:
    instance_path = os.path.join(BASE, "ontology", test_file)
    
    if not os.path.exists(instance_path):
        print(f"\n✗ {test_file} not found - skipping")
        continue
    
    print(f"\n{'='*70}")
    print(f"Testing: {test_file}")
    print(f"{'='*70}")
    
    try:
        # Create new world
        world = World()
        
        # Load ontology
        print("Loading ontology...")
        onto = world.get_ontology(f"file://{ONTOLOGY_PATH}").load()
        
        # Load instances
        print(f"Loading instances from {test_file}...")
        world.get_ontology(f"file://{instance_path}").load()
        
        # Check what we loaded
        crops = list(onto.Crop.instances())
        print(f"  ✓ Loaded {len(crops)} crops")
        
        # Count before classification
        legumes_before = len(list(onto.LegumeCrop.instances()))
        cereals_before = len(list(onto.CerealCrop.instances()))
        
        print(f"\nBefore classification:")
        print(f"  LegumeCrops: {legumes_before}")
        print(f"  CerealCrops: {cereals_before}")
        
        # APPLY PYTHON RULES - No SWRL needed!
        print(f"\nApplying Python classification rules...")
        start_time = time.time()
        
        classified_count = 0
        
        for crop in crops:
            if not hasattr(crop, 'hasCropName') or not crop.hasCropName:
                continue
            
            crop_name = crop.hasCropName[0]
            
            # Rule 1: Glycine → LegumeCrop
            if "Glycine" in crop_name:
                crop.is_a.append(onto.LegumeCrop)
                classified_count += 1
                print(f"  ✓ {crop.name} ({crop_name}) → LegumeCrop")
            
            # Rule 2: Zea → CerealCrop
            elif "Zea" in crop_name:
                crop.is_a.append(onto.CerealCrop)
                classified_count += 1
                print(f"  ✓ {crop.name} ({crop_name}) → CerealCrop")
            
            # Rule 3: Triticum → CerealCrop
            elif "Triticum" in crop_name:
                crop.is_a.append(onto.CerealCrop)
                classified_count += 1
                print(f"  ✓ {crop.name} ({crop_name}) → CerealCrop")
        
        elapsed = time.time() - start_time
        print(f"\n  ✓ Classification completed in {elapsed:.4f} seconds")
        print(f"  ✓ Classified {classified_count} crops")
        
        # Count after classification
        legumes_after = len(list(onto.LegumeCrop.instances()))
        cereals_after = len(list(onto.CerealCrop.instances()))
        
        print(f"\nAfter classification:")
        print(f"  LegumeCrops: {legumes_after} (+{legumes_after - legumes_before})")
        print(f"  CerealCrops: {cereals_after} (+{cereals_after - cereals_before})")
        
        # SUCCESS CHECK
        if legumes_after > legumes_before or cereals_after > cereals_after:
            print(f"\n{'='*70}")
            print(f"✓✓✓ SUCCESS! Python classification worked! ✓✓✓")
            print(f"{'='*70}")
        else:
            print(f"\n✗ No new classifications")
        
        # Verify individual crops
        print(f"\nVerification - Legume Crops:")
        for crop in onto.LegumeCrop.instances():
            name = crop.hasCropName[0] if hasattr(crop, 'hasCropName') and crop.hasCropName else "Unknown"
            print(f"  • {crop.name}: {name}")
        
        print(f"\nVerification - Cereal Crops:")
        for crop in onto.CerealCrop.instances():
            name = crop.hasCropName[0] if hasattr(crop, 'hasCropName') and crop.hasCropName else "Unknown"
            print(f"  • {crop.name}: {name}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")

print("="*70)
print("TESTING COMPLETE")
print("="*70)
print("\nKEY INSIGHT:")
print("→ Python rules are FASTER and MORE FLEXIBLE than SWRL")
print("→ No need for complex reasoner configuration")
print("→ Easy to debug and extend")
print("→ Perfect for your smart farming use cases!")
print("="*70)