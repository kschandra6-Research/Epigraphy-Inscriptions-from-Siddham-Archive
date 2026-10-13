#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Siddham Texts Archive — Data Extraction & PDF Generation Pipeline
Parses all 215 TEI EpiDoc XML files (IN00001.xml - IN00215.xml),
builds structured JSON/JS datasets for the interactive web application,
and generates 215 individual downloadable easy-reading PDFs plus a Master Catalogue PDF.
"""

import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

sys.stdout.reconfigure(encoding="utf-8")

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Register Windows TrueType fonts with full Unicode / IAST / Devanagari support
FONT_DIR = r"C:\Windows\Fonts"
FONT_MAP = {
    "SegoeUI": "segoeui.ttf",
    "SegoeUIBold": "segoeuib.ttf",
    "SegoeUIItalic": "segoeuii.ttf",
    "SegoeUIBoldItalic": "segoeuiz.ttf",
    "Times": "times.ttf",
    "TimesBold": "timesbd.ttf",
    "TimesItalic": "timesi.ttf",
    "Nirmala": "Nirmala.ttf",
    "Consolas": "consola.ttf",
}

for fname, ffile in FONT_MAP.items():
    fpath = os.path.join(FONT_DIR, ffile)
    if os.path.exists(fpath):
        pdfmetrics.registerFont(TTFont(fname, fpath))

pdfmetrics.registerFontFamily(
    "SegoeUI",
    normal="SegoeUI",
    bold="SegoeUIBold",
    italic="SegoeUIItalic",
    boldItalic="SegoeUIBoldItalic" if os.path.exists(os.path.join(FONT_DIR, "segoeuiz.ttf")) else "SegoeUIBold",
)

# Curated coordinate dictionary for ancient & modern South Asian epigraphic sites
SITE_COORDS = {
    "allahabad": (25.4303, 81.8736, "Prayagraj (Allahabad), Uttar Pradesh"),
    "kauśāmbī": (25.3396, 81.3925, "Kauśāmbī, Uttar Pradesh"),
    "kosam": (25.3396, 81.3925, "Kauśāmbī (Kosam), Uttar Pradesh"),
    "eraṇ": (24.0928, 78.2683, "Eraṇ (Airikiṇa), Sagar, Madhya Pradesh"),
    "eran": (24.0928, 78.2683, "Eraṇ (Airikiṇa), Sagar, Madhya Pradesh"),
    "airikiṇa": (24.0928, 78.2683, "Eraṇ (Airikiṇa), Madhya Pradesh"),
    "nālandā": (25.1357, 85.4436, "Nālandā, Bihar"),
    "nalanda": (25.1357, 85.4436, "Nālandā, Bihar"),
    "gaya": (24.7914, 85.0002, "Gayā, Bihar"),
    "bodhgaya": (24.6961, 84.9870, "Bodhgayā, Bihar"),
    "vidiśā": (23.5251, 77.8081, "Vidiśā (Besnagar), Madhya Pradesh"),
    "vidisa": (23.5251, 77.8081, "Vidiśā, Madhya Pradesh"),
    "udayagiri": (23.5391, 77.7717, "Udayagiri Caves, Vidiśā, Madhya Pradesh"),
    "sāñcī": (23.4810, 77.7363, "Sāñcī (Kākanādaboṭa), Madhya Pradesh"),
    "sanchi": (23.4810, 77.7363, "Sāñcī, Madhya Pradesh"),
    "mathurā": (27.4924, 77.6737, "Mathurā, Uttar Pradesh"),
    "mathura": (27.4924, 77.6737, "Mathurā, Uttar Pradesh"),
    "gadhwa": (25.2219, 81.5844, "Gadhwā, Prayagraj, Uttar Pradesh"),
    "mehrauli": (28.5245, 77.1855, "Mehrauli (Qutb Complex), Delhi"),
    "basarh": (25.9858, 85.1281, "Basāṛh (Vaiśālī), Bihar"),
    "vaiśālī": (25.9858, 85.1281, "Vaiśālī, Bihar"),
    "mandasor": (24.0768, 75.0693, "Mandasor (Daśapura), Madhya Pradesh"),
    "daśapura": (24.0768, 75.0693, "Daśapura (Mandasor), Madhya Pradesh"),
    "risthal": (24.1322, 75.3490, "Risthal, Mandsaur, Madhya Pradesh"),
    "bihar kotra": (23.9510, 76.7840, "Bihar Kotra, Rajgarh, Madhya Pradesh"),
    "bilsad": (27.5580, 79.2240, "Bilsaḍ, Etah, Uttar Pradesh"),
    "dhanaidaha": (24.4260, 89.0820, "Dhanaidaha, Natore, Bangladesh"),
    "tumain": (24.6420, 77.7520, "Tumain (Tumbavana), Ashoknagar, Madhya Pradesh"),
    "tumbavana": (24.6420, 77.7520, "Tumbavana (Tumain), Madhya Pradesh"),
    "karamdanda": (26.6450, 82.1250, "Karamḍāṃḍā, Faizabad, Uttar Pradesh"),
    "karamḍāṃḍā": (26.6450, 82.1250, "Karamḍāṃḍā, Uttar Pradesh"),
    "damodarpur": (25.6350, 88.8820, "Dāmodarpur, Dinajpur, Bangladesh"),
    "dāmodarpur": (25.6350, 88.8820, "Dāmodarpur, Dinajpur, Bangladesh"),
    "mankuwar": (25.3080, 81.8250, "Maṅkuvār, Prayagraj, Uttar Pradesh"),
    "maṅkuvār": (25.3080, 81.8250, "Maṅkuvār, Prayagraj, Uttar Pradesh"),
    "junagadh": (21.5222, 70.4579, "Junāgaḍh (Girnar), Gujarat"),
    "junāgaḍh": (21.5222, 70.4579, "Junāgaḍh (Girnar), Gujarat"),
    "kahaum": (26.2750, 83.8290, "Kahaum, Deoria, Uttar Pradesh"),
    "indor": (28.1850, 78.2140, "Indor (Indrapura), Bulandshahr, Uttar Pradesh"),
    "indrapura": (28.1850, 78.2140, "Indrapura (Indor), Uttar Pradesh"),
    "bhitari": (25.5678, 83.2903, "Bhitari, Ghazipur, Uttar Pradesh"),
    "supia": (24.5810, 81.3250, "Supiā, Rewa, Madhya Pradesh"),
    "supiā": (24.5810, 81.3250, "Supiā, Rewa, Madhya Pradesh"),
    "sarnath": (25.3762, 83.0227, "Sārnāth, Varanasi, Uttar Pradesh"),
    "sārnāth": (25.3762, 83.0227, "Sārnāth, Varanasi, Uttar Pradesh"),
    "varanasi": (25.3176, 82.9739, "Vārāṇasī, Uttar Pradesh"),
    "vārāṇasī": (25.3176, 82.9739, "Vārāṇasī, Uttar Pradesh"),
    "bihar sharif": (25.1982, 85.5149, "Bihar Sharif, Nalanda, Bihar"),
    "baigram": (25.3240, 89.0120, "Baigrām, Bogra, Bangladesh"),
    "jagadispur": (24.4820, 88.6940, "Jagadīśpur, Rajshahi, Bangladesh"),
    "paharpur": (25.0311, 88.9769, "Pāhārpur (Somapura), Naogaon, Bangladesh"),
    "shankarpur": (24.2120, 81.8620, "Śaṅkarpur, Sidhi, Madhya Pradesh"),
    "gunaighar": (23.6210, 90.9850, "Guṇaighar, Comilla, Bangladesh"),
    "govindnagar": (27.5010, 77.6620, "Govindnagar, Mathurā, Uttar Pradesh"),
    "kalaikuri": (24.8120, 88.9430, "Kalaikuri-Sultanpur, Naogaon, Bangladesh"),
    "gangdhar": (23.9380, 75.6240, "Gaṅgdhār, Jhalawar, Rajasthan"),
    "gaṇgdhār": (23.9380, 75.6240, "Gaṅgdhār, Jhalawar, Rajasthan"),
    "khoh": (24.4120, 80.7680, "Khoh, Satna, Madhya Pradesh"),
    "uccakalpa": (24.2650, 80.7580, "Ucchakalpa (Unchahara), Satna, Madhya Pradesh"),
    "majhgawam": (24.9120, 80.8210, "Majhgawām, Satna, Madhya Pradesh"),
    "bhumara": (24.4510, 80.6650, "Bhumarā, Satna, Madhya Pradesh"),
    "karitalai": (24.0620, 80.6840, "Kārītalāī, Katni, Madhya Pradesh"),
    "sohawal": (24.5810, 80.7640, "Sohāwal, Satna, Madhya Pradesh"),
    "betul": (21.9012, 77.8961, "Betul, Madhya Pradesh"),
    "jabalpur": (23.1815, 79.9864, "Jabalpur, Madhya Pradesh"),
    "navagrama": (24.3850, 80.7120, "Navagrāma, Central India"),
    "katni": (23.8343, 80.3894, "Katni, Madhya Pradesh"),
    "gwalior": (26.2183, 78.1828, "Gwalior (Gopagiri), Madhya Pradesh"),
    "kura": (32.6410, 72.4120, "Kurā, Salt Range, Punjab, Pakistan"),
    "kurā": (32.6410, 72.4120, "Kurā, Salt Range, Punjab, Pakistan"),
    "schoyen": (35.5800, 68.5200, "Tālagān / Tokharistan (Schøyen Scroll)"),
    "sanjeli": (23.0580, 73.9890, "Saṇjeli, Dahod, Gujarat"),
    "gardez": (33.5974, 69.2259, "Gardez, Paktia, Afghanistan"),
    "bijayagadh": (26.9680, 77.2620, "Bijayagaḍh (Bayana), Bharatpur, Rajasthan"),
    "bijaygadh": (26.9680, 77.2620, "Bijayagaḍh (Bayana), Bharatpur, Rajasthan"),
    "tusam": (28.8750, 75.9180, "Tuṣām (Tosham), Bhiwani, Haryana"),
    "deoriya": (25.3120, 81.7850, "Deoriyā, Prayagraj, Uttar Pradesh"),
    "kasia": (26.7408, 83.8889, "Kasiā (Kuśīnagar), Uttar Pradesh"),
    "lahore": (31.5204, 74.3587, "Lahore, Punjab"),
    "susuniya": (23.3964, 86.9856, "Susuniyā Hill, Bankura, West Bengal"),
    "faridpur": (23.6070, 89.8429, "Faridpur (Vanga), Bangladesh"),
    "ghagrahati": (23.0120, 89.8210, "Ghāgrāhāṭi, Kotwalipara, Bangladesh"),
    "mallasarul": (23.4120, 87.6420, "Mallasārul, Bardhaman, West Bengal"),
    "nandapur": (25.2140, 86.2410, "Nandāpur, Munger, Bihar"),
    "kotalipada": (22.9820, 89.9910, "Koṭālipāḍā, Gopalganj, Bangladesh"),
    "badva": (25.1420, 76.3820, "Baḍvā, Baran, Rajasthan"),
    "jaunpur": (25.7464, 82.6837, "Jaunpur, Uttar Pradesh"),
    "haraha": (26.9210, 81.4120, "Harāhā, Barabanki, Uttar Pradesh"),
    "asirgadh": (21.4706, 76.2939, "Asīrgaḍh, Burhanpur, Madhya Pradesh"),
    "siroli": (30.4120, 79.2140, "Sirolī, Chamoli, Uttarakhand"),
    "sohnag": (26.2510, 83.9120, "Sohnāg, Deoria, Uttar Pradesh"),
    "kannauj": (27.0514, 79.9137, "Kannauj (Kānyakubja), Uttar Pradesh"),
    "lomasa risi": (25.0053, 85.0631, "Barābar Caves (Lomaśa Ṛṣi), Jehanabad, Bihar"),
    "vadathika": (25.0094, 85.0819, "Nāgārjunī Caves (Vadathika), Bihar"),
    "gopika": (25.0094, 85.0819, "Nāgārjunī Caves (Gopikā), Bihar"),
    "deotek": (20.4510, 79.6820, "Deoṭek, Chandrapur, Maharashtra"),
    "pune": (18.5204, 73.8567, "Puṇe, Maharashtra"),
    "jamb": (20.5710, 78.8210, "Jāmb, Wardha, Maharashtra"),
    "belora": (20.7453, 78.6022, "Belorā, Wardha, Maharashtra"),
    "cammak": (21.2410, 77.5120, "Cammak (Chammak), Amravati, Maharashtra"),
    "siwani": (22.0860, 79.5440, "Siwanī, Seoni, Madhya Pradesh"),
    "riddhapur": (21.2330, 77.8120, "Riddhapur, Amravati, Maharashtra"),
    "indore": (22.7196, 75.8577, "Indore, Madhya Pradesh"),
    "dudia": (22.0510, 78.8410, "Dudiā, Chhindwara, Madhya Pradesh"),
    "tirodi": (21.6820, 79.7210, "Tiroḍī, Balaghat, Madhya Pradesh"),
    "wadgaon": (20.2610, 78.9410, "Waḍgaon, Chandrapur, Maharashtra"),
    "pattan": (21.6210, 78.2410, "Paṭṭan, Betul, Madhya Pradesh"),
    "tigaon": (21.8120, 78.4120, "Tigaon, Chhindwara, Madhya Pradesh"),
    "balaghat": (21.8129, 80.1838, "Bālāghāṭ, Madhya Pradesh"),
    "mansar": (21.3978, 79.2611, "Mansar (Pravarapura), Nagpur, Maharashtra"),
    "mohalla": (20.5810, 80.7420, "Mohallā, Rajnandgaon, Chhattisgarh"),
    "washim": (20.1119, 77.1319, "Washim (Vatsagulma), Maharashtra"),
    "ajanta": (20.5519, 75.7033, "Ajaṇṭā Caves, Aurangabad, Maharashtra"),
    "ghatotkaca": (20.4720, 75.6120, "Ghaṭotkaca Cave (Jinjala), Maharashtra"),
    "mandhal": (20.8920, 79.4620, "Māṇḍhal, Nagpur, Maharashtra"),
    "masod": (21.1420, 78.6120, "Māsoḍ, Wardha, Maharashtra"),
    "miregaon": (21.1120, 79.8820, "Miregaon, Bhandara, Maharashtra"),
    "yavatmal": (20.3888, 78.1204, "Yavatmāl, Maharashtra"),
    "pauni": (20.7925, 79.6358, "Paunī, Bhandara, Maharashtra"),
    "mahurjhari": (21.2240, 79.0050, "Māhurjharī, Nagpur, Maharashtra"),
    "hisse-borala": (20.0820, 77.1120, "Hisse-Borālā, Washim, Maharashtra"),
    "thalner": (21.2510, 74.9410, "Thāḷner, Dhule, Maharashtra"),
    "bidar": (17.9104, 77.5199, "Bidar, Karnataka"),
    "ramtek": (21.3953, 79.3269, "Rāmṭek (Rāmagiri), Nagpur, Maharashtra"),
    "nachna": (24.3980, 80.5820, "Nachnā (Nachna-Kuthara), Panna, Madhya Pradesh"),
    "ganj": (24.4210, 80.6210, "Gañj, Panna, Madhya Pradesh"),
    "amaravati": (16.5736, 80.3575, "Amarāvatī Stūpa, Guntur, Andhra Pradesh"),
    "choti sadri": (24.3820, 74.7040, "Choṭī Sāḍrī, Pratapgarh, Rajasthan"),
    "chittorgarh": (24.8887, 74.6269, "Chittorgaḍh (Madhyamikā), Rajasthan"),
    "shahpur": (25.0410, 85.6820, "Shāhpur, Nalanda, Bihar"),
    "aphsad": (25.0640, 85.6420, "Aphsaḍ, Nawada, Bihar"),
    "mandar hill": (24.8322, 87.0414, "Mandār Hill, Banka, Bihar"),
    "mangraon": (25.3120, 83.8210, "Maṅgrāon, Buxar, Bihar"),
    "kaulesvari": (24.2740, 84.8120, "Kauleśvarī Hill, Chatra, Jharkhand"),
    "deo-baranark": (25.3120, 84.4210, "Deo-Baranārk, Bhojpur, Bihar"),
    "katra": (26.2251, 85.6407, "Katrā, Muzaffarpur, Bihar"),
    "calcutta": (22.5579, 88.3511, "Indian Museum, Kolkata, West Bengal"),
}

# Sanskrit Epigraphic Glossary for easy reading and understanding
SANSKRIT_GLOSSARY = [
    ("mahārājādhirāja", "Mahārājādhirāja", "Supreme King of Great Kings — the paramount imperial title adopted by Gupta and successor sovereigns."),
    ("mahārāja", "Mahārāja", "Great King — used by early Gupta rulers, feudatory kings, and regional monarchs."),
    ("parama-bhāgavata", "Parama-Bhāgavata", "Supreme Devotee of Bhagavān (Viṣṇu/Vāsudeva) — signature Vaiṣṇava sectarian epithet of the Gupta emperors."),
    ("parama-māheśvara", "Parama-Māheśvara", "Supreme Devotee of Maheśvara (Śiva) — Śaiva royal epithet used by Vākāṭaka, Maukhari, and Later Gupta kings."),
    ("parama-bhaṭṭāraka", "Parama-Bhaṭṭāraka", "Most Worshipful Lord — high imperial title paired with Mahārājādhirāja."),
    ("kumārāmātya", "Kumārāmātya", "Princely Counsellor / Senior Imperial Cadre Officer in Gupta and post-Gupta administration."),
    ("mahā-daṇḍanāyaka", "Mahādaṇḍanāyaka", "Chief Commander / Magistrate of the Army and Justice."),
    ("sāndhivigrahika", "Sāndhivigrahika", "Minister of Peace and War (Foreign Affairs & Royal Charters)."),
    ("uparika", "Uparika", "Provincial Governor administering a bhukti (province)."),
    ("viṣayapati", "Viṣayapati", "District Magistrate / Head of a viṣaya (district)."),
    ("bhukti", "Bhukti", "Province or administrative division (e.g., Puṇḍravardhana-bhukti, Tīra-bhukti)."),
    ("viṣaya", "Viṣaya", "District or territorial unit below a bhukti."),
    ("agrahāra", "Agrahāra", "Tax-free royal land or village grant endowed to Brāhmaṇas or religious institutions."),
    ("brahmadeya", "Brahmadeya", "Tax-exempt land gifted to Vedic Brāhmaṇa scholars."),
    ("tāmra-śāsana", "Tāmra-śāsana", "Copper-plate charter recording an official royal land grant and privileges."),
    ("akṣayanīvī", "Akṣayanīvī", "Perpetual endowment whose principal cannot be spent or revoked."),
    ("pustapāla", "Pustapāla", "Keeper of Royal Land Records and Archives."),
    ("kuṭumbin", "Kuṭumbin", "Leading householder / cultivating peasant-proprietor of a village."),
    ("dūtaka", "Dūtaka", "Royal Messenger / Executor who conveys the king's oral command for a grant."),
    ("akṣapaṭalika", "Akṣapaṭalika", "Chief Archivist and Accountant General."),
    ("pratīhāra", "Pratīhāra", "Chief Chamberlain / Guardian of the Royal Palace Gate."),
    ("senāpati", "Senāpati", "Commander-in-Chief of the Armed Forces (also title borne by Pravarasena II's officers)."),
    ("aśvamedha", "Aśvamedha", "Vedic Horse Sacrifice performed to assert paramount imperial sovereignty."),
    ("dakṣiṇāpatha", "Dakṣiṇāpatha", "The Southern Realm (Deccan and Peninsular India)."),
    ("āryāvarta", "Āryāvarta", "The Northern Heartland (Indo-Gangetic plains of North India)."),
    ("garutmad", "Garutmad-aṅka", "Bearing the Garuda emblem — the imperial seal insignia of the Gupta Empire."),
    ("kavirāja", "Kavirāja", "King of Poets — title celebrated for Samudragupta in the Allahabad Praśasti."),
    ("bodhi-satva", "Bodhisattva", "Awakening Being in Mahāyāna/mainstream Buddhist dedicatory inscriptions."),
    ("bhikṣu", "Bhikṣu", "Ordained Buddhist monk."),
    ("vihāra", "Vihāra / Mahāvihāra", "Buddhist monastery or monastic university (such as Nālandā)."),
    ("stūpa", "Stūpa", "Sacred Buddhist reliquary mound or monument."),
    ("pratītya-samutpāda", "Pratītyasamutpāda", "Dependent Origination — the core Buddhist teaching inscribed on relic scrolls and stūpas."),
    ("jayaskandhāvāra", "Jayaskandhāvāra", "Victorious Royal Camp / Mobile Imperial Headquarters from which charters were issued."),
    ("mātā-pitroḥ", "Mātāpitroḥ Puṇyāya", "For the religious merit of one's mother and father — standard dedicatory formula."),
]

# Sanskrit Poetic Metres Guide
METRE_GUIDE = {
    "anuṣṭubh": "Anuṣṭubh (Śloka) — 8 syllables per quarter-verse (pāda), 32 syllables per stanza; the classic epic & legal metre.",
    "vasantatilaka": "Vasantatilakā — 14 syllables per pāda (– – ⌣ – ⌣ ⌣ ⌣ – ⌣ ⌣ – ⌣ – –); stately lyrical & panegyric metre.",
    "śārdūlavikrīḍita": "Śārdūlavikrīḍita ('Tiger's Play') — 19 syllables per pāda; grand, majestic metre used for royal praśastis.",
    "sragdharā": "Sragdharā ('Garland-Bearer') — 21 syllables per pāda in three 7-syllable cadences; ornate courtly kāvya metre.",
    "mandākrāntā": "Mandākrāntā ('Slow-Stepping') — 17 syllables per pāda beginning with 4 heavy syllables; solemn & reflective.",
    "pṛthvī": "Pṛthvī — 17 syllables per pāda; rhythmic classical Sanskrit court metre.",
    "indravajrā": "Indravajrā ('Indra's Thunderbolt') — 11 syllables per pāda (triṣṭubh class).",
    "upendravajrā": "Upendravajrā — 11 syllables per pāda starting with a light syllable.",
    "upajāti": "Upajāti — 11 syllables per pāda blending Indravajrā and Upendravajrā cadences.",
    "vaṃśastha": "Vaṃśastha — 12 syllables per pāda (jagatī class) with alternating iambic rhythm.",
    "mālinī": "Mālinī ('Lotus-Garlanded') — 15 syllables per pāda starting with six light syllables.",
    "śikhariṇī": "Śikhariṇī — 17 syllables per pāda starting with ⌣ – – – – –.",
    "śikharinī": "Śikhariṇī — 17 syllables per pāda starting with ⌣ – – – – –.",
    "hariṇī": "Hariṇī ('Gazelle') — 17 syllables per pāda with rapid opening syllables.",
    "āryā": "Āryā — Moraic (mātrā) metre based on 4-mora feet (gaṇas), popular in Prakrit & Sanskrit epigraphy.",
    "gīti": "Gīti — Moraic metre of the Āryā family with symmetrical half-verses.",
    "drutavilambita": "Drutavilambita ('Fast and Slow') — 12 syllables per pāda.",
    "praharṣiṇī": "Praharṣiṇī ('Enrapturing') — 13 syllables per pāda.",
    "puṣpitāgrā": "Puṣpitāgrā ('Flowering Tips') — Asymmetric (ardhasamavṛtta) metre of 12 and 13 syllables.",
    "mālabhāriṇī": "Mālabhāriṇī — Asymmetric classical metre.",
    "mattamayūra": "Mattamayūra ('Intoxicated Peacock') — 13 syllables per pāda.",
    "maṇimālā": "Maṇimālā ('Jeweled Garland') — 12 syllables per pāda with caesura after 6th syllable.",
    "svāgatā": "Svāgatā ('Welcome') — 11 syllables per pāda.",
    "rucirā": "Rucirā ('Brilliant') — 13 syllables per pāda.",
}


def classify_inscription(in_id: str, title: str, mat: str, obj_type: str):
    num = int(in_id.replace("IN", ""))
    t_low = title.lower()

    # Dynasty / Historical Polity classification
    if num in (17, 18, 40, 64, 76) or (94 <= num <= 98):
        dynasty = "Aulikara Dynasty (Daśapura)"
        dynasty_color = "#D97706"  # Amber/Gold
        period = "c. 400–540 CE"
    elif num == 67 or (77 <= num <= 93):
        dynasty = "Parivrājaka & Ucchakalpa"
        dynasty_color = "#059669"  # Emerald
        period = "c. 475–535 CE"
    elif 99 <= num <= 106:
        dynasty = "Alchon Hūṇas (Toramāṇa & Mihirakula)"
        dynasty_color = "#DC2626"  # Crimson
        period = "c. 495–535 CE"
    elif 155 <= num <= 200:
        dynasty = "Vākāṭaka Empire & Feudatories"
        dynasty_color = "#7C3AED"  # Royal Purple
        period = "c. 350–500 CE"
    elif 135 <= num <= 154:
        dynasty = "Maukhari Dynasty"
        dynasty_color = "#2563EB"  # Cobalt Blue
        period = "c. 238–600 CE"
    elif 208 <= num <= 215:
        dynasty = "Later Guptas of Magadha"
        dynasty_color = "#B45309"  # Bronze
        period = "c. 650–730 CE"
    elif num in (126, 127, 128, 129, 130, 131, 132, 134):
        dynasty = "Early Bengal Sovereigns (Vaṅga / Gauḍa)"
        dynasty_color = "#0D9488"  # Teal
        period = "c. 350–600 CE"
    elif 203 <= num <= 207:
        dynasty = "Mānavya / Gauri Dynasty"
        dynasty_color = "#DB2777"  # Magenta/Rose
        period = "c. 490–520 CE"
    elif (1 <= num <= 75) or num in (109, 118, 133):
        dynasty = "Imperial Gupta Empire"
        dynasty_color = "#EA580C"  # Saffron/Vermilion
        period = "c. 335–550 CE"
    else:
        dynasty = "Regional Polities & Sacred Dedications"
        dynasty_color = "#4F46E5"  # Indigo
        period = "c. 350–600 CE"

    # Extract ruler or key figure
    ruler = "Various / Dedicatory"
    ruler_patterns = [
        ("Samudragupta", "Samudragupta"),
        ("Ramagupta", "Rāmagupta"),
        ("Candragupta II", "Candragupta II Vikramāditya"),
        ("Candra", "Candra (Candragupta II)"),
        ("Dhruvasvamini", "Queen Dhruvasvāminī"),
        ("Ghatotkacagupta", "Ghaṭotkacagupta"),
        ("Kumaragupta I", "Kumāragupta I Mahendrāditya"),
        ("Skandagupta", "Skandagupta Kramāditya"),
        ("Budhagupta", "Budhagupta"),
        ("Narasimhagupta", "Narasiṃhagupta Bālāditya"),
        ("Kumaragupta II", "Kumāragupta II"),
        ("Vainyagupta", "Vainyagupta"),
        ("Visnugupta", "Viṣṇugupta"),
        ("Prakataditya", "Prakaṭāditya"),
        ("Goparaja", "Goparāja (time of Bhānugupta)"),
        ("Naravarman", "Naravarman"),
        ("Yasodharman", "Yaśodharman (Viṣṇuvardhana)"),
        ("Prakasadharman", "Prakāśadharman"),
        ("Visnuvardhana", "Viṣṇuvardhana"),
        ("Hastin", "Mahārāja Hastin"),
        ("Samksobha", "Mahārāja Saṃkṣobha"),
        ("Jayanatha", "Mahārāja Jayanātha"),
        ("Sarvanatha", "Mahārāja Śarvanātha"),
        ("Harivarman", "Mahārāja Harivarman"),
        ("Toramana", "Toramāṇa"),
        ("Mihirakula", "Mihirakula"),
        ("Khingala", "Khiṅgāla"),
        ("Prabhavatigupta", "Queen Regent Prabhāvatīguptā"),
        ("Pravarasena II", "Pravarasena II"),
        ("Prthivisena II", "Pṛthivīṣeṇa II"),
        ("Prthvisena II", "Pṛthivīṣeṇa II"),
        ("Rudrasena II", "Rudrasena II"),
        ("Rudrasena", "Rudrasena I"),
        ("Vindhyasakti II", "Vindhyaśakti II"),
        ("Devasena", "Devasena"),
        ("Harisena", "Hariṣeṇa (Vākāṭaka)"),
        ("Varahadeva", "Minister Varāhadeva (under Hariṣeṇa)"),
        ("Ravisamba", "Raviśāmba"),
        ("Vyaghradeva", "Vyāghradeva"),
        ("Isvaravarman", "Īśvaravarman"),
        ("Suryavarman", "Sūryavarman"),
        ("Isanavarman", "Īśānavarman"),
        ("Sarvavarman", "Śarvavarman"),
        ("Avantivarman", "Avantivarman"),
        ("Anantavarman", "Anantavarman (Maukhari)"),
        ("Adityasena", "Ādityasena"),
        ("Jivitagupta II", "Jīvitagupta II"),
        ("Jivagupta", "Jīvagupta"),
        ("Dharmaditya", "Dharmāditya"),
        ("Gopacandra", "Gopacandra"),
        ("Samacaradeva", "Samācāradeva"),
        ("Vijayasena", "Vijayasena"),
        ("Candravarman", "Candravarman"),
        ("Gauri", "Mahārāja Gauri"),
        ("Mahanaman", "Mahānāman"),
    ]
    for pat, label in ruler_patterns:
        if pat.lower() in t_low:
            ruler = label
            break

    # Normalize Material Category
    m_low = mat.lower()
    if "copper" in m_low:
        mat_cat = "Copper / Bronze"
    elif "iron" in m_low:
        mat_cat = "Wrought Iron"
    elif "clay" in m_low or "terracotta" in m_low:
        mat_cat = "Terracotta / Clay"
    elif "sandstone" in m_low:
        mat_cat = "Sandstone"
    elif "stone" in m_low or "granite" in m_low or "basalt" in m_low:
        mat_cat = "Stone / Rock"
    else:
        mat_cat = "Stone / Metal"

    # Normalize Object Category
    o_low = obj_type.lower()
    if "plate" in o_low or "charter" in t_low or "grant" in t_low:
        obj_cat = "Copper Plate Charter"
    elif "scroll" in o_low:
        obj_cat = "Copper Scroll"
    elif "seal" in o_low or "seal" in t_low:
        obj_cat = "Royal / Monastic Seal"
    elif "pillar" in o_low or "column" in o_low or "pilaster" in o_low or "yupa" in t_low:
        obj_cat = "Monumental Pillar / Column"
    elif "sculpture" in o_low or "image" in o_low or "pedestal" in o_low or "linga" in o_low:
        obj_cat = "Sculpture & Image Dedication"
    elif "cave" in o_low or "rock" in o_low or "cave" in t_low:
        obj_cat = "Cave & Rock-Cut Inscription"
    else:
        obj_cat = "Stone Slab & Architectural Stela"

    return dynasty, dynasty_color, period, ruler, mat_cat, obj_cat


def resolve_coordinates(title: str, orig_place: str, provenance: str, repo: str):
    # 1. Check explicit (lat, lon) in provenance
    m = re.search(r"\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)", provenance)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        place_label = orig_place.lstrip("?") if orig_place and orig_place.lower() != "unknown" else title.split(" Inscription")[0].split(" Charter")[0]
        return lat, lon, place_label, True

    # 2. Match against SITE_COORDS in orig_place, title, provenance, repository
    search_text = f"{orig_place} | {title} | {provenance} | {repo}".lower()
    for key, (lat, lon, label) in SITE_COORDS.items():
        if key in search_text:
            return lat, lon, label, False

    return None, None, orig_place.lstrip("?") if orig_place else "South Asia", False


def clean_inline_refs(text: str) -> str:
    if not text:
        return ""
    # Clean whitespace
    s = re.sub(r"\s+", " ", text).strip()
    # Format #Author_Year:page to [Author Year: page]
    s = re.sub(r"#([A-Za-z0-9_]+):(\S+)", lambda m: f"[{m.group(1).replace('_', ' ')}: {m.group(2)}]", s)
    s = re.sub(r"#([A-Za-z0-9_]+)", lambda m: f"[{m.group(1).replace('_', ' ')}]", s)
    return s


def parse_edition_node(node, state):
    """
    Recursively walks a TEI edition node to produce:
    - diplomatic HTML tokens (with line numbers, brackets, tooltips, colours)
    - smooth reader tokens (restored words, joined across line-breaks)
    - plain text for ReportLab PDF paragraphs
    """
    tag = node.tag.split("}")[-1] if isinstance(node.tag, str) else ""

    if tag == "lb":
        n = node.attrib.get("n", "")
        brk = node.attrib.get("break", "yes")
        state["line_count"] += 1
        state["current_line"] = n
        prefix = "" if brk == "no" else " "
        state["dip_tokens"].append({"type": "lb", "n": n, "break": brk})
        if brk != "no":
            state["smooth_parts"].append(" ")
    elif tag == "pb":
        n = node.attrib.get("n", "")
        state["surfaces"].append(n)
        state["dip_tokens"].append({"type": "pb", "n": n})
        state["smooth_parts"].append(f" [{n}] ")
    elif tag == "space":
        qty = node.attrib.get("quantity", "1")
        unit = node.attrib.get("unit", "character")
        state["dip_tokens"].append({"type": "space", "qty": qty, "unit": unit})
        state["smooth_parts"].append("   ")
    elif tag == "g":
        gtype = node.attrib.get("type", "symbol")
        sym = "[ornament]" if "ornament" in gtype else "ॐ [maṅgala]"
        state["dip_tokens"].append({"type": "symbol", "symbol": sym, "gtype": gtype})
        state["smooth_parts"].append(f"{sym} ")
    elif tag == "gap":
        qty = node.attrib.get("quantity", "")
        reason = node.attrib.get("reason", "lost")
        unit = node.attrib.get("unit", "character")
        extent = node.attrib.get("extent", "")
        label = f"…{qty} {unit[:4]} {reason}…" if qty else f"…{extent or reason}…"
        state["dip_tokens"].append({"type": "gap", "label": f"[{label}]", "reason": reason, "qty": qty})
        state["smooth_parts"].append(f"[{label}]")
        state["gap_count"] += 1
    elif tag == "seg":
        met = node.attrib.get("met", "")
        inner_state = {
            "dip_tokens": [],
            "smooth_parts": [],
            "line_count": 0,
            "current_line": state["current_line"],
            "surfaces": [],
            "unclear_count": 0,
            "supplied_count": 0,
            "gap_count": 0,
            "corr_count": 0,
        }
        if node.text:
            inner_state["dip_tokens"].append({"type": "text", "text": node.text})
            inner_state["smooth_parts"].append(node.text)
        for child in node:
            parse_edition_node(child, inner_state)
            if child.tail:
                inner_state["dip_tokens"].append({"type": "text", "text": child.tail})
                inner_state["smooth_parts"].append(child.tail)
        state["gap_count"] += inner_state["gap_count"]
        # Attach metrical pattern if present
        for tok in inner_state["dip_tokens"]:
            if tok.get("type") == "gap" and met:
                tok["met"] = met
            state["dip_tokens"].append(tok)
        state["smooth_parts"].extend(inner_state["smooth_parts"])
    elif tag == "unclear":
        cert = node.attrib.get("cert", "high")
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "unclear", "text": txt, "cert": cert})
        state["smooth_parts"].append(txt)
        state["unclear_count"] += 1
    elif tag == "supplied":
        reason = node.attrib.get("reason", "lost")
        cert = node.attrib.get("cert", "high")
        txt = "".join(node.itertext())
        q = "?" if cert == "low" else ""
        state["dip_tokens"].append({"type": "supplied", "text": f"[{txt}{q}]", "raw": txt, "reason": reason, "cert": cert})
        state["smooth_parts"].append(f"[{txt}]")
        state["supplied_count"] += 1
    elif tag == "choice":
        sic_el = node.find("tei:sic", NS)
        corr_el = node.find("tei:corr", NS)
        unclear_els = node.findall("tei:unclear", NS)
        if sic_el is not None and corr_el is not None:
            sic_txt = "".join(sic_el.itertext())
            corr_txt = "".join(corr_el.itertext())
            state["dip_tokens"].append({"type": "choice_corr", "sic": sic_txt, "corr": corr_txt})
            state["smooth_parts"].append(corr_txt)
            state["corr_count"] += 1
        elif len(unclear_els) >= 2:
            opts = ["/".join("".join(u.itertext()) for u in unclear_els)]
            opt_str = opts[0]
            state["dip_tokens"].append({"type": "unclear", "text": f"({opt_str})", "cert": "low"})
            state["smooth_parts"].append(
                "".join(unclear_els[0].itertext())
            )
            state["unclear_count"] += 1
        else:
            txt = "".join(node.itertext())
            state["dip_tokens"].append({"type": "text", "text": txt})
            state["smooth_parts"].append(txt)
    elif tag == "add":
        place = node.attrib.get("place", "inline")
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "add", "text": f"(+{txt})", "place": place})
        state["smooth_parts"].append(txt)
    elif tag == "del":
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "del", "text": f"[-{txt}]"})
    elif tag == "surplus":
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "surplus", "text": f"{{{txt}}}"})
    elif tag == "sic":
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "sic", "text": f"{txt}[sic]"})
        state["smooth_parts"].append(txt)
    elif tag == "num":
        val = node.attrib.get("value", "")
        txt = "".join(node.itertext())
        state["dip_tokens"].append({"type": "num", "text": txt, "value": val})
        state["smooth_parts"].append(f" ({txt}) ")
    else:
        if node.text:
            state["dip_tokens"].append({"type": "text", "text": node.text})
            state["smooth_parts"].append(node.text)
        for child in node:
            parse_edition_node(child, state)
            if child.tail:
                state["dip_tokens"].append({"type": "text", "text": child.tail})
                state["smooth_parts"].append(child.tail)


def extract_blocks_from_div(div_el, global_state, section_label=None):
    blocks = []
    if div_el is None:
        return blocks

    for child in div_el:
        tag = child.tag.split("}")[-1] if isinstance(child.tag, str) else ""
        if tag == "div":
            sub_n = child.attrib.get("n", "")
            sub_type = child.attrib.get("subtype", child.attrib.get("type", "section"))
            lbl = f"{sub_type.title()} {sub_n}".strip()
            blocks.extend(extract_blocks_from_div(child, global_state, section_label=lbl))
        elif tag == "lg":
            met = child.attrib.get("met", "Verse")
            n = child.attrib.get("n", "")
            if met and met != "Verse":
                global_state["metres"].add(met.rstrip("?"))
            global_state["verse_count"] += 1

            padas = []
            block_tokens = []
            for l_el in child.findall(".//tei:l", NS):
                st = {
                    "dip_tokens": [],
                    "smooth_parts": [],
                    "line_count": 0,
                    "current_line": global_state["current_line"],
                    "surfaces": [],
                    "unclear_count": 0,
                    "supplied_count": 0,
                    "gap_count": 0,
                    "corr_count": 0,
                }
                parse_edition_node(l_el, st)
                global_state["line_count"] += st["line_count"]
                global_state["current_line"] = st["current_line"]
                global_state["surfaces"].extend(st["surfaces"])
                global_state["unclear_count"] += st["unclear_count"]
                global_state["supplied_count"] += st["supplied_count"]
                global_state["gap_count"] += st["gap_count"]
                global_state["corr_count"] += st["corr_count"]

                smooth_pada = re.sub(r"\s+", " ", "".join(st["smooth_parts"])).strip()
                padas.append({"smooth": smooth_pada, "tokens": st["dip_tokens"]})
                block_tokens.extend(st["dip_tokens"])
                block_tokens.append({"type": "pada_break"})

            blocks.append({
                "kind": "verse",
                "n": n,
                "met": met,
                "met_desc": METRE_GUIDE.get(met.rstrip("?").lower(), "Classical Sanskrit poetic metre."),
                "section": section_label,
                "padas": padas,
                "tokens": block_tokens,
            })
        elif tag in ("p", "ab"):
            st = {
                "dip_tokens": [],
                "smooth_parts": [],
                "line_count": 0,
                "current_line": global_state["current_line"],
                "surfaces": [],
                "unclear_count": 0,
                "supplied_count": 0,
                "gap_count": 0,
                "corr_count": 0,
            }
            parse_edition_node(child, st)
            global_state["line_count"] += st["line_count"]
            global_state["current_line"] = st["current_line"]
            global_state["surfaces"].extend(st["surfaces"])
            global_state["unclear_count"] += st["unclear_count"]
            global_state["supplied_count"] += st["supplied_count"]
            global_state["gap_count"] += st["gap_count"]
            global_state["corr_count"] += st["corr_count"]

            smooth_p = re.sub(r"\s+", " ", "".join(st["smooth_parts"])).strip()
            if smooth_p or st["dip_tokens"]:
                blocks.append({
                    "kind": "prose",
                    "section": section_label,
                    "smooth": smooth_p,
                    "tokens": st["dip_tokens"],
                })

    return blocks


def parse_xml_file(filepath: str):
    tree = ET.parse(filepath)
    root = tree.getroot()

    in_id = root.findtext(".//tei:publicationStmt/tei:idno", "", NS).strip()
    title = root.findtext(".//tei:titleStmt/tei:title", "", NS).strip()
    editor = root.findtext(".//tei:titleStmt/tei:editor", "Dániel Balogh", NS).strip()
    authority = root.findtext(".//tei:publicationStmt/tei:authority", "Siddham - The South Asia Inscriptions Database", NS).strip()

    ms_desc = root.find(".//tei:sourceDesc/tei:msDesc", NS)
    obj_id = root.findtext(".//tei:msIdentifier/tei:idno", "", NS).strip()
    repo = clean_inline_refs(root.findtext(".//tei:msIdentifier/tei:repository", "", NS))
    ms_name = clean_inline_refs(root.findtext(".//tei:msIdentifier/tei:msName", "", NS))

    support = root.find(".//tei:supportDesc/tei:support", NS)
    material = support.findtext("tei:material", "Not specified", NS).strip() if support is not None else "Not specified"
    obj_type = support.findtext("tei:objectType", "Not specified", NS).strip() if support is not None else "Not specified"

    dim_el = support.find("tei:dimensions", NS) if support is not None else None
    width = dim_el.findtext("tei:width", "", NS).strip() if dim_el is not None else ""
    height = dim_el.findtext("tei:height", "", NS).strip() if dim_el is not None else ""
    depth = dim_el.findtext("tei:depth", "", NS).strip() if dim_el is not None else ""
    weight = support.findtext("tei:measure[@type='weight']", "", NS).strip() if support is not None else ""
    support_p = clean_inline_refs(" ".join(p.text or "" for p in support.findall("tei:p", NS))) if support is not None else ""

    layout_el = root.find(".//tei:layoutDesc/tei:layout", NS)
    ldim_el = layout_el.find("tei:dimensions", NS) if layout_el is not None else None
    l_width = ldim_el.findtext("tei:width", "", NS).strip() if ldim_el is not None else ""
    l_height = ldim_el.findtext("tei:height", "", NS).strip() if ldim_el is not None else ""
    layout_p = clean_inline_refs(" ".join(p.text or "" for p in layout_el.findall("tei:p", NS))) if layout_el is not None else ""

    hand_el = root.find(".//tei:handDesc/tei:handNote", NS)
    char_height = hand_el.findtext("tei:height", "", NS).strip() if hand_el is not None else ""
    script_note = clean_inline_refs(" ".join(p.text or "" for p in hand_el.findall("tei:p", NS))) if hand_el is not None else ""

    deco_el = root.find(".//tei:decoDesc", NS)
    deco_note = clean_inline_refs(" ".join(p.text or "" for p in deco_el.findall("tei:p", NS))) if deco_el is not None else ""

    orig_place = root.findtext(".//tei:history/tei:origin/tei:origPlace", "", NS).strip()
    orig_date = root.findtext(".//tei:history/tei:origin/tei:origDate", "", NS).strip()
    prov_el = root.find(".//tei:history/tei:provenance", NS)
    provenance = clean_inline_refs(" ".join(p.text or "" for p in prov_el.findall("tei:p", NS))) if prov_el is not None else ""

    frags = root.findall(".//tei:msFrag", NS)
    frag_count = len(frags)

    dynasty, dynasty_color, period, ruler, mat_cat, obj_cat = classify_inscription(in_id, title, material, obj_type)
    lat, lon, place_label, exact_gps = resolve_coordinates(title, orig_place, provenance, repo)

    # Extract cross-references (%IN00012) across all descriptive fields
    all_desc_text = f"{support_p} {layout_p} {script_note} {deco_note} {provenance}"
    cross_refs = sorted(list(set(re.findall(r"%?(IN\d{5})", all_desc_text))))
    if in_id in cross_refs:
        cross_refs.remove(in_id)

    # Parse edition
    div_ed = root.find(".//tei:div[@type='edition']", NS)
    lang = div_ed.attrib.get(XML_LANG, "san-Latn") if div_ed is not None else "san-Latn"

    global_state = {
        "line_count": 0,
        "current_line": "1",
        "surfaces": [],
        "metres": set(),
        "verse_count": 0,
        "unclear_count": 0,
        "supplied_count": 0,
        "gap_count": 0,
        "corr_count": 0,
    }
    blocks = extract_blocks_from_div(div_ed, global_state)

    # Full plain smooth text for search & glossary matching
    full_smooth_lines = []
    for b in blocks:
        if b["kind"] == "verse":
            for p in b["padas"]:
                if p["smooth"]:
                    full_smooth_lines.append(p["smooth"])
        else:
            if b["smooth"]:
                full_smooth_lines.append(b["smooth"])
    full_smooth_text = "\n".join(full_smooth_lines)

    # Detect glossary terms present in this inscription
    detected_terms = []
    lower_smooth = full_smooth_text.lower()
    for key, term_title, definition in SANSKRIT_GLOSSARY:
        if key in lower_smooth:
            detected_terms.append({"term": term_title, "key": key, "desc": definition})

    # Construct plain-English executive summary for easy understanding
    summary_parts = [
        f"{title} ({in_id}) is an epigraphic record from the {dynasty} ({period}), associated with {ruler}."
    ]
    if obj_type and material:
        summary_parts.append(
            f"Inscribed on a {obj_type} crafted of {material}"
            + (f" (measuring {width} × {height} cm)" if width and height else "")
            + f", it is currently preserved at: {repo or 'in situ / unrecorded repository'}."
        )
    if place_label and place_label.lower() != "unknown":
        summary_parts.append(f"Its historical provenance/origin is linked to {place_label}.")
    if global_state["verse_count"] > 0:
        met_list = ", ".join(sorted(global_state["metres"]))
        summary_parts.append(
            f"The Sanskrit text spans {max(global_state['line_count'], 1)} epigraphic lines and features {global_state['verse_count']} poetic stanza(s) composed in {met_list or 'classical Sanskrit metre'}."
        )
    else:
        summary_parts.append(
            f"The Sanskrit prose text spans {max(global_state['line_count'], 1)} epigraphic lines."
        )

    dim_str = " × ".join([x for x in [width, height, depth] if x])
    if dim_str:
        dim_str += " cm"
    else:
        dim_str = "Not recorded"

    ldim_str = " × ".join([x for x in [l_width, l_height] if x])
    if ldim_str:
        ldim_str += " cm"
    else:
        ldim_str = "Not recorded"

    return {
        "id": in_id,
        "xml_file": os.path.basename(filepath),
        "pdf_file": f"pdfs/{in_id}.pdf",
        "object_id": obj_id or "—",
        "title": title,
        "editor": editor,
        "authority": authority,
        "dynasty": dynasty,
        "dynasty_color": dynasty_color,
        "period": period,
        "ruler": ruler,
        "repository": repo or "In situ / Unspecified",
        "ms_name": ms_name or title,
        "material": material,
        "material_category": mat_cat,
        "object_type": obj_type,
        "object_category": obj_cat,
        "dimensions": dim_str,
        "width": width,
        "height": height,
        "depth": depth,
        "weight": weight or "Not available",
        "layout_dimensions": ldim_str,
        "char_height": f"{char_height} cm" if char_height else "Not recorded",
        "support_desc": support_p or "No additional physical support remarks recorded.",
        "layout_desc": layout_p or "Standard epigraphic layout.",
        "script_desc": script_note or "Brahmi-derived Gupta/post-Gupta epigraphic script.",
        "deco_desc": deco_note or "None.",
        "orig_place": orig_place.lstrip("?") if orig_place else "Unknown",
        "orig_place_raw": orig_place or "Unknown",
        "orig_date": orig_date or period,
        "provenance": provenance or "Provenance details not separately recorded.",
        "lat": lat,
        "lon": lon,
        "place_label": place_label,
        "exact_gps": exact_gps,
        "frag_count": frag_count,
        "cross_refs": cross_refs,
        "lang": lang,
        "line_count": max(global_state["line_count"], 1),
        "verse_count": global_state["verse_count"],
        "metres": sorted(list(global_state["metres"])),
        "surfaces": sorted(list(set(global_state["surfaces"]))),
        "stats": {
            "unclear": global_state["unclear_count"],
            "supplied": global_state["supplied_count"],
            "gaps": global_state["gap_count"],
            "corrections": global_state["corr_count"],
        },
        "summary": " ".join(summary_parts),
        "glossary": detected_terms,
        "blocks": blocks,
        "full_text": full_smooth_text,
    }


def safe_pdf_text(text: str) -> str:
    """Escapes XML entities and wraps Devanagari runs in Nirmala font for ReportLab."""
    if not text:
        return ""
    esc = xml_escape(str(text))
    # Replace %IN00xxx with bold tag
    esc = re.sub(r"%?(IN\d{5})", r"<b>\1</b>", esc)
    # Wrap Devanagari characters in Nirmala font
    esc = re.sub(r"([\u0900-\u097F]+)", r'<font name="Nirmala">\1</font>', esc)
    return esc


def tokens_to_reportlab_markup(tokens) -> str:
    """Converts diplomatic edition tokens into colour-coded ReportLab Paragraph markup."""
    out = []
    for tok in tokens:
        t = tok["type"]
        if t == "lb":
            n = xml_escape(str(tok.get("n", "")))
            brk = tok.get("break", "yes")
            if brk == "no":
                out.append(f'<font color="#64748B" size="7.5">-[L{n}]</font>')
            else:
                out.append(f' <font color="#0284C7" size="8"><b>[L{n}]</b></font> ')
        elif t == "pb":
            n = xml_escape(str(tok.get("n", "")))
            out.append(f' <font color="#7C3AED" size="8.5"><b>|| Surface: {n} ||</b></font> ')
        elif t == "pada_break":
            out.append(' <font color="#94A3B8"><b>/</b></font> ')
        elif t == "text":
            out.append(safe_pdf_text(tok["text"]))
        elif t == "unclear":
            out.append(f'<font color="#B45309"><i>{safe_pdf_text(tok["text"])}</i></font>')
        elif t == "supplied":
            out.append(f'<font color="#047857"><b>{safe_pdf_text(tok["text"])}</b></font>')
        elif t == "gap":
            met = f' ({xml_escape(tok["met"])})' if tok.get("met") else ""
            out.append(f'<font color="#DC2626">{safe_pdf_text(tok["label"])}{met}</font>')
        elif t == "choice_corr":
            corr = safe_pdf_text(tok["corr"])
            sic = safe_pdf_text(tok["sic"])
            out.append(f'<font color="#1D4ED8"><b>{corr}</b></font><font color="#64748B" size="7.5"> (sic: {sic})</font>')
        elif t in ("add", "del", "surplus", "sic", "num", "symbol"):
            txt = tok.get("text", tok.get("symbol", ""))
            out.append(f'<font color="#7C3AED">{safe_pdf_text(txt)}</font>')
        elif t == "space":
            out.append(" &nbsp;&nbsp; ")
    res = "".join(out)
    res = re.sub(r"\s+", " ", res).strip()
    return res


def build_single_pdf(item: dict, out_path: str):
    """Generates an eye-catching, easy-to-read downloadable PDF edition for a single XML inscription."""
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.6 * cm,
        title=f"{item['id']} - {item['title']}",
        author=f"{item['editor']} ({item['authority']})",
        subject=f"Siddham Epigraphic Archive Edition - {item['dynasty']}",
    )

    styles = {
        "HeaderID": ParagraphStyle("HeaderID", fontName="SegoeUIBold", fontSize=10, leading=13, textColor=colors.HexColor("#FDE68A")),
        "HeaderTitle": ParagraphStyle("HeaderTitle", fontName="SegoeUIBold", fontSize=16, leading=20, textColor=colors.white, spaceBefore=2, spaceAfter=4),
        "HeaderSub": ParagraphStyle("HeaderSub", fontName="SegoeUI", fontSize=9.5, leading=13, textColor=colors.HexColor("#E2E8F0")),
        "SectionHeading": ParagraphStyle("SectionHeading", fontName="SegoeUIBold", fontSize=11.5, leading=15, textColor=colors.HexColor("#0F172A"), spaceBefore=10, spaceAfter=5),
        "SummaryText": ParagraphStyle("SummaryText", fontName="SegoeUI", fontSize=9.5, leading=14, textColor=colors.HexColor("#1E293B")),
        "MetaLabel": ParagraphStyle("MetaLabel", fontName="SegoeUIBold", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569")),
        "MetaValue": ParagraphStyle("MetaValue", fontName="SegoeUI", fontSize=8.8, leading=12, textColor=colors.HexColor("#0F172A")),
        "BodyNote": ParagraphStyle("BodyNote", fontName="SegoeUI", fontSize=9, leading=13.5, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "LegendBox": ParagraphStyle("LegendBox", fontName="SegoeUI", fontSize=8.2, leading=12, textColor=colors.HexColor("#334155")),
        "VerseHeader": ParagraphStyle("VerseHeader", fontName="SegoeUIBold", fontSize=9, leading=12, textColor=colors.HexColor("#7C3AED"), spaceBefore=4, spaceAfter=2),
        "SmoothText": ParagraphStyle("SmoothText", fontName="SegoeUI", fontSize=9.8, leading=14.5, textColor=colors.HexColor("#0F172A"), spaceAfter=4),
        "DipText": ParagraphStyle("DipText", fontName="SegoeUI", fontSize=9.2, leading=14.2, textColor=colors.HexColor("#1E293B"), spaceAfter=5),
        "GlossaryItem": ParagraphStyle("GlossaryItem", fontName="SegoeUI", fontSize=8.5, leading=12.5, textColor=colors.HexColor("#1E293B"), spaceAfter=2),
    }

    story = []

    # 1. Eye-catching Top Banner Table
    banner_bg = colors.HexColor("#1E1B4B")
    accent_col = colors.HexColor(item["dynasty_color"])
    header_html = (
        f'<font color="#FBBF24"><b>SIDDHAM ARCHIVE • {xml_escape(item["id"])}</b></font> '
        f'&nbsp;|&nbsp; <font color="#CBD5E1">Object: {xml_escape(item["object_id"])} • {xml_escape(item["dynasty"])} ({xml_escape(item["period"])})</font>'
    )
    sub_html = (
        f'<b>Ruler / Attribution:</b> {safe_pdf_text(item["ruler"])} &nbsp;&nbsp;•&nbsp;&nbsp; '
        f'<b>Category:</b> {safe_pdf_text(item["object_category"])} &nbsp;&nbsp;•&nbsp;&nbsp; '
        f'<b>Editor:</b> {safe_pdf_text(item["editor"])}'
    )

    banner_table = Table(
        [
            [Paragraph(header_html, styles["HeaderID"])],
            [Paragraph(safe_pdf_text(item["title"]), styles["HeaderTitle"])],
            [Paragraph(sub_html, styles["HeaderSub"])],
        ],
        colWidths=[18 * cm],
    )
    banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), banner_bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (0, 0), 10),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ("LINEBELOW", (0, -1), (-1, -1), 3.5, accent_col),
        ])
    )
    story.append(banner_table)
    story.append(Spacer(1, 8))

    # 2. Executive Summary Box for Easy Understanding
    sum_table = Table(
        [[Paragraph(f'<b>Quick Reading Overview:</b> {safe_pdf_text(item["summary"])}', styles["SummaryText"])]],
        colWidths=[18 * cm],
    )
    sum_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#F59E0B")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )
    story.append(sum_table)
    story.append(Spacer(1, 8))

    # 3. Metadata Grid (2 pairs of columns = 4 columns)
    meta_rows = [
        [
            Paragraph("Repository / Custody", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(item["repository"]), styles["MetaValue"]),
            Paragraph("Origin / Findspot", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(f"{item['place_label']} ({item['orig_place_raw']})"), styles["MetaValue"]),
        ],
        [
            Paragraph("Material & Support", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(f"{item['material']} ({item['object_type']})"), styles["MetaValue"]),
            Paragraph("Object Dimensions", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(f"{item['dimensions']} | Wt: {item['weight']}"), styles["MetaValue"]),
        ],
        [
            Paragraph("Inscribed Layout", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(f"{item['layout_dimensions']} ({item['line_count']} lines, {item['verse_count']} verses)"), styles["MetaValue"]),
            Paragraph("Char Height & Script", styles["MetaLabel"]),
            Paragraph(safe_pdf_text(f"{item['char_height']} — {item['script_desc'][:90]}"), styles["MetaValue"]),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[3.2 * cm, 5.8 * cm, 3.2 * cm, 5.8 * cm])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F1F5F9")),
            ("BACKGROUND", (1, 0), (1, -1), colors.white),
            ("BACKGROUND", (3, 0), (3, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(meta_table)

    # 4. Physical, Palaeographic & Provenance Details
    story.append(Paragraph("1. Archaeological, Physical & Historical Notes", styles["SectionHeading"]))
    story.append(Paragraph(f'<b>Physical Support:</b> {safe_pdf_text(item["support_desc"])}', styles["BodyNote"]))
    if item["layout_desc"] and item["layout_desc"] != "Standard epigraphic layout.":
        story.append(Paragraph(f'<b>Inscribed Layout:</b> {safe_pdf_text(item["layout_desc"])}', styles["BodyNote"]))
    story.append(Paragraph(f'<b>Palaeography / Script:</b> {safe_pdf_text(item["script_desc"])}', styles["BodyNote"]))
    if item["deco_desc"] and item["deco_desc"].lower() not in ("none.", "none"):
        story.append(Paragraph(f'<b>Decoration & Seals:</b> {safe_pdf_text(item["deco_desc"])}', styles["BodyNote"]))
    story.append(Paragraph(f'<b>Provenance & Discovery:</b> {safe_pdf_text(item["provenance"])}', styles["BodyNote"]))

    # 5. Glossary & Metres Box (if detected)
    if item["glossary"] or item["metres"]:
        story.append(Paragraph("2. Key Sanskrit Terms & Poetic Metres in This Inscription", styles["SectionHeading"]))
        if item["metres"]:
            m_items = []
            for m in item["metres"]:
                desc = METRE_GUIDE.get(m.lower(), "Classical Sanskrit metre.")
                m_items.append(f"• <b>{safe_pdf_text(m.title())}</b>: {safe_pdf_text(desc)}")
            story.append(Paragraph("<br/>".join(m_items), styles["GlossaryItem"]))
            story.append(Spacer(1, 4))
        if item["glossary"]:
            g_items = [
                f'• <b>{safe_pdf_text(g["term"])}</b>: {safe_pdf_text(g["desc"])}'
                for g in item["glossary"][:8]
            ]
            story.append(Paragraph("<br/>".join(g_items), styles["GlossaryItem"]))

    # 6. Epigraphic Notation Legend
    story.append(Spacer(1, 4))
    legend_html = (
        '<b>How to Read Epigraphic Symbols:</b> &nbsp; '
        '<font color="#047857"><b>[abc]</b></font> = Restored / supplied text lost or omitted on original &nbsp;|&nbsp; '
        '<font color="#B45309"><i>abc</i></font> = Partially damaged / unclear characters &nbsp;|&nbsp; '
        '<font color="#DC2626">[…6 char lost…]</font> = Illegible or broken gap (lacuna) &nbsp;|&nbsp; '
        '<font color="#0284C7"><b>[L1]</b></font> = Original inscription line number &nbsp;|&nbsp; '
        '<font color="#1D4ED8"><b>corr</b></font> (sic) = Editorial correction of scribal error'
    )
    leg_table = Table([[Paragraph(legend_html, styles["LegendBox"])]], colWidths=[18 * cm])
    leg_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(leg_table)

    # 7. Easy-Reading Smooth Edition
    story.append(Paragraph("3. Easy-Reading Smooth Edition (Restored Stanzas & Prose)", styles["SectionHeading"]))
    if not item["blocks"]:
        story.append(Paragraph("<i>No transcribed edition text recorded in this file.</i>", styles["SmoothText"]))
    else:
        last_sec = None
        for idx, b in enumerate(item["blocks"], 1):
            if b.get("section") and b["section"] != last_sec:
                last_sec = b["section"]
                story.append(Paragraph(f'<b>— {safe_pdf_text(last_sec)} —</b>', styles["VerseHeader"]))
            if b["kind"] == "verse":
                v_num = b.get("n") or str(idx)
                v_met = b.get("met") or "Verse"
                story.append(Paragraph(f'Verse {safe_pdf_text(v_num)} • Metre: <i>{safe_pdf_text(v_met)}</i>', styles["VerseHeader"]))
                pada_lines = [safe_pdf_text(p["smooth"]) for p in b["padas"] if p["smooth"]]
                if pada_lines:
                    story.append(Paragraph("<br/>".join(pada_lines), styles["SmoothText"]))
            else:
                if b["smooth"]:
                    story.append(Paragraph(safe_pdf_text(b["smooth"]), styles["SmoothText"]))

    # 8. Critical Diplomatic Edition (Line-by-Line with Colour-Coded Apparatus)
    story.append(Paragraph("4. Line-by-Line Diplomatic Edition (Critical Text & Line Numbers)", styles["SectionHeading"]))
    for idx, b in enumerate(item["blocks"], 1):
        markup = tokens_to_reportlab_markup(b["tokens"])
        if markup:
            prefix = f'<font color="#7C3AED" size="8"><b>[Verse {xml_escape(str(b.get("n") or idx))} — {xml_escape(str(b.get("met", "")))}]</b></font> ' if b["kind"] == "verse" else ""
            story.append(Paragraph(prefix + markup, styles["DipText"]))

    def add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("SegoeUI", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(1.5 * cm, 1.0 * cm, f"Siddham South Asia Inscriptions Archive • {item['id']}: {item['title'][:55]}")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Page {doc_obj.page}")
        canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
        canvas.setLineWidth(0.5)
        canvas.line(1.5 * cm, 1.35 * cm, A4[0] - 1.5 * cm, 1.35 * cm)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


def build_master_catalogue_pdf(items: list, out_path: str):
    """Generates a Master Catalogue & Guide PDF summarizing all 215 inscriptions."""
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.6 * cm,
        title="Siddham Texts Archive — Complete Master Catalogue (IN00001–IN00215)",
        author="Dániel Balogh / Siddham South Asia Inscriptions Database",
    )

    styles = {
        "Title": ParagraphStyle("Title", fontName="SegoeUIBold", fontSize=18, leading=22, textColor=colors.white),
        "Sub": ParagraphStyle("Sub", fontName="SegoeUI", fontSize=10, leading=14, textColor=colors.HexColor("#E2E8F0")),
        "H2": ParagraphStyle("H2", fontName="SegoeUIBold", fontSize=13, leading=17, textColor=colors.HexColor("#1E1B4B"), spaceBefore=12, spaceAfter=6),
        "CellHead": ParagraphStyle("CellHead", fontName="SegoeUIBold", fontSize=8.5, leading=11, textColor=colors.white),
        "Cell": ParagraphStyle("Cell", fontName="SegoeUI", fontSize=8, leading=11, textColor=colors.HexColor("#1E293B")),
        "CellBold": ParagraphStyle("CellBold", fontName="SegoeUIBold", fontSize=8, leading=11, textColor=colors.HexColor("#0F172A")),
    }

    story = []
    banner = Table(
        [
            [Paragraph("SIDDHAM SOUTH ASIA INSCRIPTIONS ARCHIVE (IN00001–IN00215)", styles["Title"])],
            [Paragraph("Complete Master Catalogue, Dynasty Classification & Epigraphic Reading Guide • 215 Inscriptions", styles["Sub"])],
        ],
        colWidths=[18.2 * cm],
    )
    banner.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1E1B4B")),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (0, 0), 12),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
            ("LINEBELOW", (0, -1), (-1, -1), 4, colors.HexColor("#F59E0B")),
        ])
    )
    story.append(banner)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Complete Directory of All 215 Inscriptions", styles["H2"]))

    rows = [[
        Paragraph("ID", styles["CellHead"]),
        Paragraph("Title & Ruler", styles["CellHead"]),
        Paragraph("Dynasty / Period", styles["CellHead"]),
        Paragraph("Material & Object", styles["CellHead"]),
        Paragraph("Origin / Repository", styles["CellHead"]),
    ]]

    for it in items:
        rows.append([
            Paragraph(f"{it['id']}<br/><font color='#64748B' size='7'>{it['object_id']}</font>", styles["CellBold"]),
            Paragraph(f"<b>{safe_pdf_text(it['title'])}</b><br/><font color='#475569'>{safe_pdf_text(it['ruler'])}</font>", styles["Cell"]),
            Paragraph(f"{safe_pdf_text(it['dynasty'])}<br/><font color='#64748B'>{safe_pdf_text(it['period'])}</font>", styles["Cell"]),
            Paragraph(f"{safe_pdf_text(it['object_type'])}<br/><font color='#64748B'>{safe_pdf_text(it['material'])}</font>", styles["Cell"]),
            Paragraph(f"<b>{safe_pdf_text(it['place_label'])}</b><br/><font color='#64748B'>{safe_pdf_text(it['repository'][:45])}</font>", styles["Cell"]),
        ])

    tbl = Table(rows, colWidths=[1.8 * cm, 5.4 * cm, 3.8 * cm, 3.2 * cm, 4.0 * cm], repeatRows=1)
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312E81")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(tbl)

    def add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("SegoeUI", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(1.4 * cm, 1.0 * cm, "Siddham Texts Archive — Master Catalogue (215 South Asian Epigraphic Records)")
        canvas.drawRightString(A4[0] - 1.4 * cm, 1.0 * cm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("pdfs", exist_ok=True)

    xml_files = sorted(glob.glob("IN*.xml"))
    print(f"Found {len(xml_files)} XML files. Parsing and generating PDFs...")

    items = []
    for idx, fpath in enumerate(xml_files, 1):
        item = parse_xml_file(fpath)
        items.append(item)
        pdf_out = os.path.join("pdfs", f"{item['id']}.pdf")
        build_single_pdf(item, pdf_out)
        if idx % 25 == 0 or idx == len(xml_files):
            print(f"  Processed {idx}/{len(xml_files)}: {item['id']} -> {pdf_out}")

    master_pdf = os.path.join("pdfs", "Siddham_Archive_Complete_Catalogue.pdf")
    build_master_catalogue_pdf(items, master_pdf)
    print(f"Generated Master Catalogue PDF: {master_pdf}")

    # Save JSON and JS bundle (so index.html works both via HTTP server and direct file:// protocol)
    archive_payload = {
        "title": "Siddham — The South Asia Inscriptions Archive",
        "subtitle": "Interactive Digital Epigraphy Portal & Downloadable PDF Library (IN00001–IN00215)",
        "total_count": len(items),
        "glossary": [{"key": k, "term": t, "desc": d} for k, t, d in SANSKRIT_GLOSSARY],
        "metre_guide": METRE_GUIDE,
        "inscriptions": items,
    }

    with open(os.path.join("data", "inscriptions.json"), "w", encoding="utf-8") as f:
        json.dump(archive_payload, f, ensure_ascii=False, indent=2)

    with open(os.path.join("data", "inscriptions.js"), "w", encoding="utf-8") as f:
        f.write("// Auto-generated Siddham Archive Dataset for offline/file:// and hosted web usage\n")
        f.write("window.SIDDHAM_ARCHIVE = ")
        json.dump(archive_payload, f, ensure_ascii=False)
        f.write(";\n")

    print("Saved data/inscriptions.json and data/inscriptions.js successfully!")


if __name__ == "__main__":
    main()
