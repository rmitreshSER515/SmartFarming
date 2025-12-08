# backend/scripts/add_swrl_rule.py
# Add SWRL rule directly to the ontology using owlready2

from owlready2 import *
import os

BASE = os.path.dirname(os.path.dirname(__file__))
ONTOLOGY_PATH = os.path.join(BASE, "ontology", "smart-farming.owl")

print("="*70)
print("ADDING SWRL RULE TO ONTOLOGY")
print("="*70)

# Load ontology
print(f"\nLoading ontology from: {ONTOLOGY_PATH}")
onto = get_ontology(f"file://{ONTOLOGY_PATH}").load()

print(f"✓ Loaded ontology")
print(f"  Classes: {len(list(onto.classes()))}")

# Add SWRL rule using owlready2
with onto:
    # Rule: Classify crops containing "Glycine" as LegumeCrop
    rule1 = Imp()
    rule1.set_as_rule("""
        Crop(?c), hasCropName(?c, ?name), swrlb:contains(?name, "Glycine") 
        -> LegumeCrop(?c)
    """)
    
    print("\n✓ Added Rule 1: Glycine → LegumeCrop")
    
    # Rule: Classify crops containing "Zea" as CerealCrop
    rule2 = Imp()
    rule2.set_as_rule("""
        Crop(?c), hasCropName(?c, ?name), swrlb:contains(?name, "Zea") 
        -> CerealCrop(?c)
    """)
    
    print("✓ Added Rule 2: Zea → CerealCrop")
    
    # Rule: Classify crops containing "Triticum" as CerealCrop
    rule3 = Imp()
    rule3.set_as_rule("""
        Crop(?c), hasCropName(?c, ?name), swrlb:contains(?name, "Triticum") 
        -> CerealCrop(?c)
    """)
    
    print("✓ Added Rule 3: Triticum → CerealCrop")

# Save ontology with rules
output_path = os.path.join(BASE, "ontology", "smart-farming-with-rules.owl")
onto.save(file=output_path, format="rdfxml")

print(f"\n✓ Saved ontology with SWRL rules to:")
print(f"  {output_path}")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Update test script to use: smart-farming-with-rules.owl")
print("2. Run: python scripts/test_reasoning_python.py")
print("="*70)