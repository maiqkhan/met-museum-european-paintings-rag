# 🎨 RAG Application for The Met European Paintings Collection  

## 📌 Project Overview  
This project is a **Retrieval-Augmented Generation (RAG) application** built for the **European Paintings Collection** at the **Metropolitan Museum of Art, New York**.  
The goal of the application is to allow users to **ask natural language questions** about paintings and receive **context-rich answers** sourced from the museum’s knowledge base.  

---

## 🎯 Problem Description  
Art museums host **massive collections of artworks**, but navigating and retrieving **specific, contextual information** can be overwhelming.  
Currently, searching through large datasets requires manual effort, keyword searches, or browsing through static web pages.  

**Problem:**  
- Visitors cannot ask **natural language questions** about artworks and get tailored, accurate responses.  
- Existing search methods often return too much or too little information.  
- There’s a gap in providing **interactive, AI-powered access** to museum collections.  

**Solution (this project):**  
- Use **RAG (Retrieval-Augmented Generation)** to combine **structured museum data** with **LLM-powered reasoning**.  
- Enable users to query paintings using everyday language (e.g., *"Who painted Jerusalem from the Mount of Olives?"* or *"Show me paintings by French artists in the 19th century"*).  
- Provide responses that are both **informative** and **directly linked** to the original dataset.  


---

## 🗂️ Dataset Description  
The dataset is derived from the **Metropolitan Museum of Art’s Open Access API**, focusing on the **European Paintings Department**.  

Each artwork contains rich metadata, including:  
- **Object ID & Accession Details** (e.g., `objectID`, `accessionNumber`)  
- **Images** (high-resolution + web-friendly versions)  
- **Constituents** (artists, roles, nationality, lifespan, links to Wikidata/ULAN)  
- **Department & Classification** (e.g., “European Paintings”)  
- **Artwork Details** (title, medium, dimensions, date, culture, period)  
- **Provenance & Credit Line** (e.g., donor information)  
- **Tags & Linked Resources** (Getty AAT terms, Wikidata tags)  
- **Gallery Information** (where the painting is displayed in the museum)  

### Example Record  
Here’s a simplified example:  

```json
{
  "objectID": 436418,
  "title": "Jerusalem from the Mount of Olives",
  "artistDisplayName": "Charles-Théodore Frère",
  "artistNationality": "French",
  "objectDate": "by 1880",
  "medium": "Oil on canvas",
  "dimensions": "29 1/2 x 43 1/2 in. (74.9 x 110.5 cm)",
  "primaryImage": "https://images.metmuseum.org/CRDImages/ep/original/DT2000.jpg",
  "repository": "Metropolitan Museum of Art, New York, NY",
  "tags": ["Tents", "Men", "Camels", "Deserts", "Hills", "Orientalist"],
  "objectURL": "https://www.metmuseum.org/art/collection/search/436418"
}
```

### ⚙️ What the Application Does

- Load & Process Data: Collects and stores painting metadata from The Met’s Open Access API.

- Embed & Index Data: Converts artwork metadata into embeddings for efficient semantic search.

- Natural Language Querying: Allows users to type in questions instead of keywords.

- Contextual Responses: Uses RAG to retrieve relevant metadata and generate human-friendly answers.

- Link to Sources: Provides references back to the official museum records.

- Image Support: Displays artwork images alongside textual responses.

### Example Use Cases

"Who painted Jerusalem from the Mount of Olives?"
    → Answer: Charles-Théodore Frère (French, 1814–1888)

"Show me 19th-century French paintings in the collection."
→ Answer: Returns a list of paintings matching criteria, with artist names, dates, and images.

"Where can I find this painting in the museum?"
→ Answer: Gallery 804, Floor 2, with a link to the interactive gallery map.


### 🚀 Future Opportunities

- Museum Guide Integration: Could power an on-site mobile app for museum visitors.

- Education Tools: Useful for art history students to query collections interactively.

- Expansion Beyond European Paintings: Scale to all museum departments.

- Multilingual Support: Allow questions and responses in multiple languages.

## ⚙️ Setup Instructions  - Update
1. Clone Repository
git clone https://github.com/maiqkhan/met-museum-european-paintings-rag.git
cd met-museum-european-paintings-rag

2. Install Dependencies
pip install -r requirements.txt

3. Configure API Keys

Create a .env file with your keys (if using OpenAI or other LLM providers).

OPENAI_API_KEY=your_api_key_here

4. Run the Application
streamlit run app.py

5. Ask Questions

Open the app in your browser and start asking questions about the Met’s European Paintings.

## 🖼️ Visuals & Examples  - Update
App Interface Screenshot

(Insert screenshot of query + response here)

Example Query Demo

(Insert GIF showing a user typing “Who painted Jerusalem from the Mount of Olives?” and the app responding with the painting details + image)

## 🎥 App Preview Video - Update

( Upload a short screen recording of your app in action.)

## 📂 Documentation Structure - Update

README.md → Project overview

setup.md → Detailed installation/setup instructions

usage.md → How to use the app with examples

contributing.md → Guidelines for contributors

### 🔄 Maintenance

The project will be updated as new features are added, datasets are expanded, or the API is updated. Always check the latest commit history for changes.

## Ingestion

## Evaluation

### Retrieval

### Rag Flow

## Monitoring

## Ingestion

