# backend/scripts/test_reasoning_python.py
# Test SWRL reasoning directly in Python (faster than Protégé)

from owlready2 import *
import os
import time

BASE = os.path.dirname(os.path.dirname(__file__))
ONTOLOGY_PATH = os.path.join(BASE, "ontology", "smart-farming-with-rules.owl")

# Test with different instance files
test_files = [
    "instances_tiny.owl",
    "instances_small.owl", 
    "instances_medium.owl",
]

print("="*70)
print("TESTING SWRL REASONING WITH OWLREADY2")
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
        
        # Check crops have hasCropName
        crops_with_names = [c for c in crops if hasattr(c, 'hasCropName') and c.hasCropName]
        print(f"  ✓ {len(crops_with_names)} crops have hasCropName property")
        
        if crops_with_names:
            print(f"  Sample: {crops_with_names[0].name} → {crops_with_names[0].hasCropName[0]}")
        
        # Count before reasoning
        legumes_before = len(list(onto.LegumeCrop.instances()))
        cereals_before = len(list(onto.CerealCrop.instances()))
        
        print(f"\nBefore reasoning:")
        print(f"  LegumeCrops: {legumes_before}")
        print(f"  CerealCrops: {cereals_before}")
        
        # Run reasoner with timer
        print(f"\nRunning Pellet reasoner...")
        start_time = time.time()
        
        with onto:
            sync_reasoner_pellet(world, infer_property_values=True)
        
        elapsed = time.time() - start_time
        print(f"  ✓ Reasoning completed in {elapsed:.2f} seconds")
        
        # Count after reasoning
        legumes_after = len(list(onto.LegumeCrop.instances()))
        cereals_after = len(list(onto.CerealCrop.instances()))
        
        print(f"\nAfter reasoning:")
        print(f"  LegumeCrops: {legumes_after} (+{legumes_after - legumes_before})")
        print(f"  CerealCrops: {cereals_after} (+{cereals_after - cereals_before})")
        
        # Show which crops were classified
        print(f"\nClassified crops:")
        for crop in onto.LegumeCrop.instances():
            if hasattr(crop, 'hasCropName') and crop.hasCropName:
                print(f"  ✓ {crop.name} ({crop.hasCropName[0]}) → LegumeCrop")
        
        for crop in onto.CerealCrop.instances():
            if hasattr(crop, 'hasCropName') and crop.hasCropName:
                print(f"  ✓ {crop.name} ({crop.hasCropName[0]}) → CerealCrop")
        
        # SUCCESS CHECK
        if legumes_after > legumes_before or cereals_after > cereals_before:
            print(f"\n{'='*70}")
            print(f"✓✓✓ SUCCESS! SWRL rule worked! ✓✓✓")
            print(f"{'='*70}")
        else:
            print(f"\n✗ No new classifications - rule may not have fired")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")

print("="*70)
print("TESTING COMPLETE")
print("="*70)
print("\nIf reasoning worked in Python but not Protégé:")
print("→ Protégé may have configuration issues")
print("→ Use Python backend instead (faster anyway!)")