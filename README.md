# 🏛️ Siddham — South Asia Inscriptions Archive (IN00001–IN00215)

[![Live Demo](https://img.shields.io/badge/Live%20Portal-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://kschandra6-research.github.io/Epigraphy-Inscriptions-from-Siddham-Archive/)
[![Inscriptions](https://img.shields.io/badge/Corpus-215%20Inscriptions-amber?style=for-the-badge)](https://kschandra6-research.github.io/Epigraphy-Inscriptions-from-Siddham-Archive/)
[![Historical Span](https://img.shields.io/badge/Chronology-c.%20238%E2%80%93730%20CE-blue?style=for-the-badge)]()
[![TEI EpiDoc](https://img.shields.io/badge/Standards-TEI%20EpiDoc%20XML-orange?style=for-the-badge)](https://epidoc.stoa.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-11%2B-red?style=for-the-badge&logo=openjdk)](https://openjdk.org/)
[![Leaflet](https://img.shields.io/badge/Maps-Leaflet.js-green?style=for-the-badge&logo=leaflet)](https://leafletjs.com/)

> **An interactive digital epigraphy portal, multi-mode classical Sanskrit reader, geographic GIS visualizer, and publication-ready PDF library for 215 ancient South Asian inscriptions.**

---

## 🌟 Live Demo & Web Portal

🔗 **Explore the Live Archive:**  
**[https://kschandra6-research.github.io/Epigraphy-Inscriptions-from-Siddham-Archive/](https://kschandra6-research.github.io/Epigraphy-Inscriptions-from-Siddham-Archive/)**

*Works completely offline and across all modern desktop, tablet, and mobile browsers.*

---

## 📖 Overview

The **Siddham South Asia Inscriptions Archive** is an open-access digital humanities project and interactive web application designed to make ancient Indian epigraphs accessible, readable, and searchable for epigraphists, historians, Sanskrit scholars, students, and heritage enthusiasts.

Built upon 215 critically edited TEI EpiDoc XML editions from the **ERC Siddham Epigraphic Corpus** (*Siddham: The South Asia Inscriptions Database*, edited by **Dániel Balogh et al.**), this archive transforms raw scholarly XML markups into:
- An **interactive multi-mode epigraphic reader** featuring live **IAST ↔ Devanagari (देवनागरी)** transliteration.
- **Critical diplomatic and smooth easy-reading views** preserving Leiden epigraphic bracket conventions.
- An **interactive Leaflet GIS map** plotting ancient findspots and provenance coordinates across South Asia.
- **Visual analytics and distributions** across dynasties, media supports, object categories, and Sanskrit metres (*chandas*).
- A **Side-by-Side Inscription Comparator** for cross-examining royal praśastis and copper-plate grants.
- An **epigraphic glossary and Sanskrit metres guide** linked directly to the corpus explorer.
- **216 downloadable publication-quality PDFs** (215 individual formatted inscription monographs + 1 Complete Master Catalogue).

---

## 🏛️ Historical Corpus & Dynastic Scope

The archive spans five centuries of early classical and early medieval South Asian epigraphy (c. **238–730 CE**), covering **10 major dynasties and regional polities**:

| Dynasty / Historical Polity | Chronology | Key Inscriptions & Highlights |
|---|---|---|
| **Imperial Gupta Empire** | c. 335–550 CE | Allahabad Pillar Praśasti of Samudragupta (`IN00001`), Eran Boar & Pillar inscriptions, Bhitari Pillar of Skandagupta, Mathurā & Sāñcī dedications, royal land grants, seals of Nālandā & Vaiśālī |
| **Vākāṭaka Empire & Feudatories** | c. 350–500 CE | Copper plates of Pravarasena II (Chammak, Siwan, Tirodi), Riddhapur plates of Prabhāvatīguptā, Ajaṇṭā Cave 16 & 17 inscriptions, Ghaṭotkaca Cave, Mandhal plates |
| **Aulikara Dynasty of Daśapura** | c. 400–540 CE | Mandasor Pillar of Yaśodharman (`IN00094`), Mandasor Silk Weavers' Guild Inscription of Kumāragupta I & Bandhuvarman, Risthal Inscription |
| **Parivrājaka & Ucchakalpa Mahārājas** | c. 475–535 CE | Khoh copper plates of Hastin and Śarvanātha, Bhumarā boundary pillar of Hastin and Śarvanātha, Majhgawām copper plates |
| **Alchon Hūṇas** | c. 495–535 CE | Eran Stone Boar Inscription of Toramāṇa (`IN00099`), Gwalior Stone Inscription of Mihirakula (`IN00100`), Kura Inscription |
| **Maukhari Dynasty** | c. 238–600 CE | Barabar & Nagarjuni Hill Cave inscriptions of Anantavarman, Badva Yūpa inscriptions, Harāhā Inscription of Īśānavarman, Asīrgaḍh seal |
| **Later Guptas of Magadha** | c. 650–730 CE | Aphsaḍ Stone Inscription of Ādityasena (`IN00208`), Deo-Baranārk Inscription of Jīvitagupta II, Mandār Hill rock inscriptions |
| **Early Bengal Sovereigns (Vaṅga / Gauḍa)** | c. 350–600 CE | Susunia Rock Inscription of Candravarman, Faridpur copper plates of Gopacandra, Dharmāditya, and Samācāradeva, Gunaighar plate |
| **Mānavya / Gauri Dynasty** | c. 490–520 CE | Choṭī Sāḍrī Inscription of Ghorī (Gauri) ruler Mānagaurī, Chittorgaḍh inscriptions |
| **Regional Polities & Sacred Dedications** | c. 350–600 CE | Epigraphs from Kosam, Govindnagar, Kahaum Jain column, Nachna Kuthara, Amarāvatī, and Western India |

---

## ⚡ Core Features

### 1. 📜 Multi-Mode Epigraphic Reader
- **Easy-Reading Smooth View**: Continuous grammatical text formatted for readability, resolving difficult ligatures and word-divisions while preserving the poetic meter.
- **Critical Diplomatic View**: Exact line-by-line (`[L1]`, `[L2]`, etc.) scholarly representation respecting physical surface breaks and Leiden epigraphic bracket conventions.
- **Poetic Verses Only View**: Automatically isolates metered stanzas (*ślokas*), displaying quarter-verses (*pādas*) with metrical annotations.
- **Dual-Script Display Engine**: Instant side-by-side or singular view switching between **IAST (Roman transliteration)** and native **Devanagari (देवनागरी)** script.
- **Interactive Metadata Drawer**: Displays physical support attributes, dimensions, findspot, current repository (e.g., Indian Museum Kolkata, British Museum, ASI site museums), ruler, date, and inline cross-references (`%IN00xxx`).
- **Keyboard Navigation**: Browse through inscriptions effortlessly using keyboard arrows (`←` Previous, `→` Next, `Esc` to close).

### 2. 🔍 Smart Diacritic-Insensitive Search & Faceted Filtering
- **Unicode-Normalized Full-Text Search**: Type `samudragupta`, `eran`, `mandasor`, or `vakataka` to match diacritic-rich Sanskrit text (`Samudragupta`, `Eraṇ`, `Mandasor / Daśapura`, `Vākāṭaka`).
- **Multi-Dimensional Filters**: Filter simultaneously by:
  - **Dynasty / Polity** (10 categories with color coding)
  - **Object Form** (Pillars, Copper Plates, Rock Surfaces, Cave Walls, Stone Slabs, Seals & Sealings, Pedestals)
  - **Material Support** (Stone, Copper, Bronze, Clay, Terracotta, Iron, Gold)
  - **Classical Metre** (*Chandas*)
  - **Bookmarked Records** (stored in browser `localStorage`)
- **Dual View Layouts**: Switch between a visual **Cards Grid View** and a compact **Data Table View**.
- **📥 CSV Dataset Export**: Download currently filtered search results with metadata in one click.

### 3. 🗺️ Interactive Geographic Map (Leaflet GIS)
- Plotted coordinates for ancient sites across India, Bangladesh, and Pakistan (e.g., Prayagraj, Eraṇ, Mandasor, Nālandā, Vārāṇasī, Ajaṇṭā, Junāgaḍh, Dāmodarpur, Mahurjhari).
- Dynasty-coded map markers with interactive popups providing site names, ancient designations, ruler details, and direct one-click links into the Reader.

### 4. 📊 Visual Analytics & Epigraphic Statistics
- Instant dynamic charts visualizing:
  - Dynasty & Polity distribution.
  - Material support breakdown (Stone vs. Copper Plates vs. Seals).
  - Object category typology.
  - Frequency distribution of Classical Sanskrit metres across the corpus.

### 5. ⚖️ Side-by-Side Inscription Comparator
- Load any two inscriptions simultaneously (e.g., Allahabad Pillar `IN00001` vs. Mandasor Pillar `IN00094`, or contemporaneous Vākāṭaka land grants) to compare genealogical formulas, orthography, scribal conventions, and royal epithets.

### 6. 📘 Sanskrit Epigraphic Glossary & Chandas Guide
- **Royal & Administrative Glossary**: Over 30 key epigraphic terms defined with historical context (*Mahārājādhirāja*, *Paramabhaṭṭāraka*, *Sāndhivigrahika*, *Kumārāmātya*, *Uparika*, *Viṣayapati*, *Agrahāra*, *Tāmra-śāsana*, *Akṣayanīvī*, *Pustapāla*, *Dūtaka*, etc.). Clicking any glossary term filters the archive instantly.
- **Poetic Metres (*Chandas*) Guide**: Comprehensive metrical guide explaining 24+ Sanskrit metres used in royal *praśastis* (*Anuṣṭubh*, *Śārdūlavikrīḍita*, *Mandākrāntā*, *Sragdharā*, *Vasantatilakā*, *Āryā*, *Pṛthvī*, *Mālinī*, etc.) with syllable counts and caesura (*yati*) patterns.

### 7. 🖨️ PDF Library & Print-Ready Monographs
- **215 Inscription PDFs** (`pdfs/IN00001.pdf` through `pdfs/IN00215.pdf`) generated via ReportLab with Unicode font rendering (IAST diacritics and Devanagari).
- **Master Catalogue PDF** (`pdfs/Siddham_Archive_Complete_Catalogue.pdf`): A complete tabular reference manual containing full catalogue metadata for all 215 records.

---

## 🗂️ Repository Structure

```plaintext
Epigraphy-Inscriptions-from-Siddham-Archive/
│
├── index.html                   # Main single-page web application & user interface
├── styles.css                   # Custom typography, responsive design & themes
├── app.js                       # Client engine: transliterator, search, map, analytics, comparator
│
├── data/
│   ├── inscriptions.js          # Pre-compiled standalone dataset (enables offline & file:// execution)
│   └── inscriptions.json        # Complete structured JSON dataset with editions & metadata
│
├── pdfs/                        # 216 Publication PDFs (Tracked via Git LFS)
│   ├── IN00001.pdf              # Allahabad Pillar Inscription of Samudragupta
│   ├── IN00002.pdf ...          # Individual monographs for each inscription
│   ├── IN00215.pdf
│   └── Siddham_Archive_Complete_Catalogue.pdf # Master archive catalogue
│
├── build_archive.py             # Python data pipeline: XML parser, geo-resolver, JSON/JS & PDF builder
├── server.py                    # Lightweight Python 3 HTTP server (with CORS support)
├── SiddhamArchiveServer.java    # Standalone zero-dependency Java 11+ HTTP server
│
├── .gitattributes               # Git LFS configuration for PDF assets
└── README.md                    # Project documentation & reference manual
```

---

## 🚀 Getting Started & Local Setup

### Option 1: Direct In-Browser (No Server Required)
Because `data/inscriptions.js` bundles the pre-compiled archive data into the global scope:
1. Clone or download this repository.
2. Double-click `index.html` or open it directly in any modern browser (`file:///.../index.html`).
3. All features—search, transliteration, analytics, glossary, and reading modes—work seamlessly offline.

---

### Option 2: Run with Python 3 Server
Use the included `server.py` to serve the application locally:
```bash
# Clone the repository
git clone https://github.com/kschandra6-Research/Epigraphy-Inscriptions-from-Siddham-Archive.git
cd Epigraphy-Inscriptions-from-Siddham-Archive

# Start the Python server
python server.py
```
*The server will start on `http://localhost:8080/index.html` and automatically open your default browser.*

---

### Option 3: Run with Java 11+ Server
If you prefer running in a Java environment with zero external dependencies:
```bash
# Compile and run in one step (Java 11+)
java SiddhamArchiveServer.java
```
*The Java server will host the archive at `http://localhost:8085/index.html`.*

---

## 🛠️ Data Pipeline & PDF Generation (`build_archive.py`)

The repository includes `build_archive.py`, an automated data extraction and typography pipeline that:
1. Ingests 215 TEI EpiDoc XML files (`IN00001.xml` to `IN00215.xml`).
2. Extracts metadata (titles, rulers, dynasties, dates, origination findspots, repositories, object types, and dimensions).
3. Parses `<div type="edition">` nodes, separating prose paragraphs (`<p>`), stanzas (`<lg>`), quarter-verses (`<l>`), and editorial apparatus (`<unclear>`, `<supplied>`, `<gap>`, `<corr>`, `<choice>`).
4. Generates smoothed easy-reading texts and diplomatic line-by-line arrays.
5. Resolves geographical coordinates against a curated gazetteer of South Asian epigraphic sites.
6. Serializes clean datasets to `data/inscriptions.json` and `data/inscriptions.js`.
7. Builds 215 individual PDFs and a comprehensive Master Catalogue PDF using **ReportLab** with Windows TrueType Unicode font families (`Segoe UI`, `Nirmala UI`, `Times New Roman`).

### Running the Pipeline:
```bash
# Install requirements
pip install reportlab

# Run the build script
python build_archive.py
```

---

## 📐 Epigraphic Conventions (Leiden System)

The critical diplomatic reader adheres to standard international epigraphic (Leiden+) conventions:

| Symbol / Style | Meaning | Example |
|---|---|---|
| `[abc]` | **Supplied / Restored**: Characters lost due to damage or omission on stone/plate, restored by the editor. | `[mahārājā]` |
| *`abc`* *(Italics)* | **Unclear / Damaged**: Characters partially effaced or damaged on the original surface, read with reasonable certainty. | *`gupta`* |
| `[…6 char lost…]` | **Lacuna / Gap**: Damaged portions where characters cannot be read with certainty. | `[…8 char lost…]` |
| `[L1]`, `[L2]` | **Line Number**: Original physical line beginnings on the inscribed surface. | `[L4]` |
| `corr (sic)` | **Editorial Correction**: Correction made by the editor where the original scribe made an error. | `dūtakaḥ` |
| `// 1 //` | **Verse Number**: End of an epigraphic Sanskrit stanza (*śloka* / *chandas*). | `॥ १ ॥` |

---

## 📚 Academic Attribution & Citations

### Conceptualization & Platform Development
- **Design, Curation & Engineering**: **K. S. Chandra** (2026), Department of Ancient Indian History, Culture and Archaeology, Rashtrasant Tukadoji Maharaj Nagpur University.

### Source Corpus & Editorial Authority
- **Original Inscription Editions**: **ERC Siddham Epigraphic Corpus** (*Siddham: The South Asia Inscriptions Database*).
- **Principal Editor**: **Dániel Balogh**, with contributions from international epigraphists and researchers under the European Research Council (ERC) *Beyond Boundaries* project.
- **Data Source Repository**: Hosted via the Siddham Network and archived under Open Access repositories (Zenodo).

### Suggested Citation Format
If you utilize this web portal, datasets, or generated PDFs in academic publications, research papers, or digital humanities projects, please cite:

```bibtex
@misc{chandra2026siddham,
  author       = {Chandra, K. S.},
  title        = {{Siddham --- South Asia Inscriptions Archive (IN00001--IN00215): Interactive Digital Epigraphy Portal, Multi-Mode Sanskrit Reader, and Geographic Visualizer}},
  year         = {2026},
  publisher    = {GitHub},
  howpublished = {\url{https://kschandra6-research.github.io/Epigraphy-Inscriptions-from-Siddham-Archive/}},
  note         = {Based on the ERC Siddham Epigraphic Corpus edited by Dániel Balogh et al.}
}
```

---

## 📄 License & Open Access

- **Epigraphic Texts & Editions**: Open-access scholarly heritage data provided under standard academic fair use and open research sharing from the **Siddham Asia Inscriptions Database**.
- **Application Code & Tools**: Released under the [MIT License](https://opensource.org/licenses/MIT).

---

<div align="center">
  <sub>🏛️ Preserving and presenting South Asian classical heritage through modern digital epigraphy.</sub>
</div>
