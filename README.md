# Smart Farming Knowledge Graph & Reasoning System

A complete semantic reasoning system for **Crop Rotation**, **Fertilizer Application**, and **Pest Risk Assessment** using:

- **OWL 2 Ontology**
- **SWRL Rules for reasoning**
- **SWRLAPI for automated rule execution**
- **TTL knowledge graph export**
- **Flask REST API** for retrieving recommendations

This project loads crop yield, weather, pest, and field data; applies reasoning rules; generates fertilizer and pest recommendations; and exposes them through APIs.

---

# What This Project Does

### Builds a Smart Farming Ontology  
Defines classes and properties for:
- Plots
- Crops
- Yield Records
- Weather Summaries
- Pest Events
- Recommendations

### Applies SWRL Rules  
Rules compute:
- Fertilizer recommendations based on weather  
- Crop rotation suggestions  
- Pest risk

### Generates a Fully Inferred TTL  
This inferred knowledge graph contains:
- New recommendation individuals  
- Linked plots, years, crops  
- Justification text for each recommendation  

### Provides Flask API Endpoints  
These let you query:
- Available plots / years  
- Raw yield records  
- Fertilizer recommendations  
- Pest recommendations

---

# How to Run the Project

## 1. Install Python Environment
```bash
cd backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

## 2. Navigate to the Frontend Folder
```bash
cd frontend

npm install

npm start

The frontend communicates with the backend API running at:

http://localhost:5001
```

## 3. API Usage Guide - These are the set of API's we have used for implementation
1. GET /api/plots
2. GET /api/plots/<plot_id>/year/<int:year>
3. GET /api/recommendations/needs-fertilizer
4. GET /api/crops/legumes
5. GET /api/crops/cereals
6. GET /api/recommendations/postpone-fertilizer
7. GET /api/recommendations/high-pest-risk
8. GET /api/recommendations/next-crop



