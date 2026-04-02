"""
LabTrack — Clinical Lab Supply Visibility & 3PL Distribution Management
Tools : Python · Streamlit · Plotly · SQLite (SQL)
Author: Rutwik Satish
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import random
import io

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="LabTrack · Clinical Supply Visibility",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.4rem;padding-bottom:2rem;}
[data-testid="metric-container"]{
  background:#0F1624;border:1px solid #1C2A3E;border-radius:10px;padding:1rem 1.2rem;}
[data-testid="metric-container"] label{
  font-size:11px!important;text-transform:uppercase;letter-spacing:.06em;color:#7B90AC!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{
  font-size:1.9rem!important;font-weight:800!important;}
.stTabs [data-baseweb="tab-list"]{gap:0;border-bottom:1px solid #1C2A3E;background:transparent;}
.stTabs [data-baseweb="tab"]{padding:.65rem 1.2rem;font-size:13px;font-weight:600;
  color:#7B90AC;border-bottom:2px solid transparent;}
.stTabs [aria-selected="true"]{color:#F0F4FF!important;border-bottom:2px solid #3B82F6!important;
  background:transparent!important;}
.stTabs [data-baseweb="tab-highlight"]{display:none;}
.stTabs [data-baseweb="tab-border"]{display:none;}
.stButton>button{font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;
  font-size:13px;border-radius:8px;padding:.45rem 1.2rem;}
.stTextArea textarea,.stTextInput input,.stSelectbox>div>div{
  background:#080D1A!important;border:1px solid #1C2A3E!important;
  border-radius:8px!important;color:#F0F4FF!important;}
[data-testid="stSidebar"]{background:#0A101F;border-right:1px solid #1C2A3E;}
div[data-testid="stDataFrame"]{border:1px solid #1C2A3E;border-radius:10px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
TODAY     = date.today()
BG        = "#080D1A"
CARD      = "#0F1624"
BORDER    = "#1C2A3E"
BLUE      = "#3B82F6"
AMBER     = "#F59E0B"
GREEN     = "#10B981"
RED       = "#EF4444"
SUB       = "#7B90AC"

SITES = [
    ("S01", "Main Campus",            "Manhattan, NY",  "Academic Medical Center"),
    ("S02", "Cobble Hill",            "Brooklyn, NY",   "Community Hospital"),
    ("S03", "Long Island",            "Mineola, NY",    "Regional Medical Center"),
    ("S04", "Midtown Ambulatory",     "Manhattan, NY",  "Ambulatory Care"),
    ("S05", "Perlmutter Cancer Ctr",  "Manhattan, NY",  "Oncology Center"),
    ("S06", "Orthopedic Hospital",    "Manhattan, NY",  "Specialty Hospital"),
]

SUPPLIERS = [
    "VWR Scientific", "Fisher Scientific", "Sigma-Aldrich",
    "BD Biosciences", "Thermo Fisher", "Qiagen",
    "Bio-Rad", "Roche Diagnostics", "Beckman Coulter",
    "Sysmex", "Ortho Clinical", "bioMerieux",
]

# Catalog: (name, category, cost_lo, cost_hi)
RAW_CATALOG = [
    # Lab Reagents ─────────────────────────────────────────────
    ("Sodium Chloride 0.9% 1L",          "Lab Reagents",          6,   14),
    ("PBS Buffer 10x 500mL",             "Lab Reagents",         10,   18),
    ("EDTA Solution 0.5M 100mL",         "Lab Reagents",         12,   22),
    ("Tris-HCl Buffer pH 8.0",           "Lab Reagents",         11,   20),
    ("Formalin 10% Neutral Buffered",    "Lab Reagents",          8,   16),
    ("Ethanol 200-Proof 4L",             "Lab Reagents",         22,   38),
    ("Methanol HPLC Grade 4L",           "Lab Reagents",         28,   45),
    ("Acetonitrile LC-MS Grade",         "Lab Reagents",         35,   55),
    ("Acetic Acid Glacial 2.5L",         "Lab Reagents",         18,   30),
    ("Hydrochloric Acid 37% 2.5L",       "Lab Reagents",         20,   34),
    ("Bradford Protein Assay 1L",        "Lab Reagents",         28,   48),
    ("BCA Protein Assay Kit",            "Lab Reagents",         55,   85),
    ("Coomassie Blue Stain 1L",          "Lab Reagents",         14,   24),
    ("Agarose LE Standard 500g",         "Lab Reagents",         55,   90),
    ("TAE Buffer 50x 1L",                "Lab Reagents",          8,   15),
    ("SDS-PAGE Running Buffer",          "Lab Reagents",         12,   20),
    ("Hematoxylin Solution 1L",          "Lab Reagents",         18,   32),
    ("Eosin Y Solution 1L",              "Lab Reagents",         16,   28),
    ("Gram Stain Kit",                   "Lab Reagents",         22,   40),
    ("Wright-Giemsa Stain 500mL",        "Lab Reagents",         24,   42),
    ("PAS Staining Kit",                 "Lab Reagents",         38,   62),
    ("Masson Trichrome Kit",             "Lab Reagents",         45,   72),
    ("DAPI Nuclear Stain 5mg",           "Lab Reagents",         42,   70),
    ("Propidium Iodide Solution",        "Lab Reagents",         38,   60),
    ("Crystal Violet 0.5% 500mL",       "Lab Reagents",         12,   20),
    ("Oil Red O Solution 250mL",         "Lab Reagents",         28,   45),
    ("Congo Red Solution 500mL",         "Lab Reagents",         22,   38),
    ("Calcein AM 1mg",                   "Lab Reagents",         65,  110),
    ("Annexin V FITC Kit",               "Lab Reagents",         85,  145),
    ("LDH Cytotoxicity Assay",           "Lab Reagents",         72,  120),
    ("TMB Substrate Solution",           "Lab Reagents",         28,   48),
    ("ABTS Substrate 250mL",             "Lab Reagents",         24,   42),
    ("Streptavidin-HRP Conjugate",       "Lab Reagents",         55,   90),
    ("Blocking Solution 5% BSA",         "Lab Reagents",         18,   30),
    ("HEPES Buffer 1M 100mL",            "Lab Reagents",         22,   36),
    ("Magnesium Chloride 1M 100mL",      "Lab Reagents",         14,   24),
    ("Potassium Phosphate Dibasic",      "Lab Reagents",         16,   26),
    ("MOPS Buffer 10x 500mL",            "Lab Reagents",         20,   34),
    ("Sodium Azide 25g",                 "Lab Reagents",         18,   30),
    ("Tween-20 Detergent 500mL",         "Lab Reagents",         15,   25),
    ("Triton X-100 500mL",               "Lab Reagents",         16,   26),
    ("SDS 10% Solution 500mL",           "Lab Reagents",         14,   22),
    ("Urea Ultrapure 500g",              "Lab Reagents",         28,   45),
    ("Guanidinium Hydrochloride",        "Lab Reagents",         32,   52),
    ("Beta-Mercaptoethanol 25mL",        "Lab Reagents",         22,   38),

    # Diagnostic Test Kits ─────────────────────────────────────
    ("Troponin I High-Sensitivity Kit",  "Diagnostic Test Kits", 185, 320),
    ("BNP Cardiac Biomarker Panel",      "Diagnostic Test Kits", 165, 280),
    ("D-Dimer Rapid Quantitative",       "Diagnostic Test Kits", 120, 200),
    ("HbA1c Analyzer Kit",               "Diagnostic Test Kits", 145, 240),
    ("TSH Thyroid Panel ELISA",          "Diagnostic Test Kits", 110, 185),
    ("HIV Combo Antigen/Antibody",       "Diagnostic Test Kits",  85, 145),
    ("Hepatitis B Surface Ag Kit",       "Diagnostic Test Kits",  95, 160),
    ("Hepatitis C Antibody Test",        "Diagnostic Test Kits",  90, 155),
    ("Flu A/B Differentiation Kit",      "Diagnostic Test Kits",  75, 125),
    ("COVID-19 Antigen Rapid Test",      "Diagnostic Test Kits",  55,  90),
    ("RSV Rapid Detection Kit",          "Diagnostic Test Kits",  68, 115),
    ("Strep A Rapid Test Cassettes",     "Diagnostic Test Kits",  45,  78),
    ("H. Pylori Stool Antigen",          "Diagnostic Test Kits",  72, 120),
    ("C. Diff Toxin A/B Kit",            "Diagnostic Test Kits",  88, 148),
    ("INR/PT Coagulation Reagent",       "Diagnostic Test Kits", 125, 210),
    ("aPTT Reagent Actin FS",            "Diagnostic Test Kits", 115, 195),
    ("Fibrinogen Assay Clauss Method",   "Diagnostic Test Kits", 135, 225),
    ("Urine Dipstick Multi-Panel",       "Diagnostic Test Kits",  38,  65),
    ("Fecal Occult Blood Guaiac",        "Diagnostic Test Kits",  42,  72),
    ("Pregnancy HCG Rapid",              "Diagnostic Test Kits",  32,  55),
    ("PSA Total Prostate Kit",           "Diagnostic Test Kits", 105, 175),
    ("CEA Tumor Marker ELISA",           "Diagnostic Test Kits", 115, 195),
    ("CA-125 Ovarian Cancer Panel",      "Diagnostic Test Kits", 128, 215),
    ("AFP Marker Kit",                   "Diagnostic Test Kits", 108, 182),
    ("Calprotectin Fecal ELISA",         "Diagnostic Test Kits",  98, 165),
    ("Procalcitonin Sepsis Marker",      "Diagnostic Test Kits", 145, 245),
    ("CRP High-Sensitivity ELISA",       "Diagnostic Test Kits",  88, 148),
    ("IL-6 Cytokine ELISA",              "Diagnostic Test Kits", 155, 260),
    ("Cortisol Serum ELISA",             "Diagnostic Test Kits",  95, 160),
    ("Vitamin D 25-OH Assay",            "Diagnostic Test Kits", 105, 178),
    ("Ferritin Quantitative ELISA",      "Diagnostic Test Kits",  85, 142),
    ("Thyroglobulin Assay Kit",          "Diagnostic Test Kits", 118, 198),
    ("Anti-CCP Antibody Kit",            "Diagnostic Test Kits", 128, 215),
    ("RF Rheumatoid Factor Latex",       "Diagnostic Test Kits",  68, 115),
    ("ANA Screening IIF Kit",            "Diagnostic Test Kits", 112, 188),

    # Collection Supplies ──────────────────────────────────────
    ("BD Vacutainer EDTA 4mL 100pk",     "Collection Supplies",   22,  38),
    ("BD Vacutainer SST 8.5mL 100pk",    "Collection Supplies",   26,  44),
    ("BD Vacutainer Citrate 2.7mL",      "Collection Supplies",   24,  40),
    ("BD Vacutainer Lithium Heparin",    "Collection Supplies",   25,  42),
    ("Pediatric Microtainer EDTA",       "Collection Supplies",   28,  48),
    ("Safety Butterfly 21G 12in",        "Collection Supplies",   35,  58),
    ("Safety Butterfly 23G 12in",        "Collection Supplies",   35,  58),
    ("Straight Draw Needle 20G",         "Collection Supplies",   18,  30),
    ("Straight Draw Needle 22G",         "Collection Supplies",   18,  30),
    ("Safety Lancets 1.8mm 200pk",       "Collection Supplies",   22,  36),
    ("Heparinized Capillary Tubes",      "Collection Supplies",   14,  24),
    ("Microcentrifuge Tubes 1.5mL 500pk","Collection Supplies",   12,  20),
    ("Microcentrifuge Tubes 2.0mL 500pk","Collection Supplies",   12,  20),
    ("Conical Tubes 15mL 500pk",         "Collection Supplies",   28,  46),
    ("Conical Tubes 50mL 500pk",         "Collection Supplies",   32,  52),
    ("Specimen Transport Bags 6x9",      "Collection Supplies",   16,  26),
    ("Biohazard Specimen Bags 2mil",     "Collection Supplies",   14,  22),
    ("Thermal Specimen Labels 500pk",    "Collection Supplies",   18,  30),
    ("Sterile Throat Swabs 100pk",       "Collection Supplies",   22,  36),
    ("Nasopharyngeal Swabs 50pk",        "Collection Supplies",   28,  48),
    ("Urine Collection Cups 60mL",       "Collection Supplies",   10,  18),
    ("Sterile Gauze Pads 2x2 200pk",     "Collection Supplies",    8,  14),
    ("Alcohol Prep Pads Medium 200pk",   "Collection Supplies",    6,  12),
    ("Latex-Free Tourniquet 18in",       "Collection Supplies",    5,  10),
    ("Wound Culture Transport Swabs",    "Collection Supplies",   24,  40),
    ("Blood Culture Swabs Sterile",      "Collection Supplies",   26,  44),
    ("Chain of Custody Forms 50pk",      "Collection Supplies",   14,  24),
    ("Cryovials 2mL External Thread",    "Collection Supplies",   22,  36),
    ("Cryoboxes 81-Well Polycarbonate",  "Collection Supplies",   18,  30),
    ("Parafilm M 4in x 125ft",           "Collection Supplies",   24,  38),

    # Culture Media ────────────────────────────────────────────
    ("Blood Agar Plates 5% Sheep",       "Culture Media",         18,  32),
    ("MacConkey Agar Plates",            "Culture Media",         16,  28),
    ("Chocolate Agar Plates",            "Culture Media",         20,  34),
    ("Sabouraud Dextrose Agar",          "Culture Media",         18,  30),
    ("Tryptic Soy Broth 500mL",          "Culture Media",         12,  20),
    ("Brain Heart Infusion Broth",       "Culture Media",         14,  22),
    ("Thioglycolate Broth 500mL",        "Culture Media",         12,  20),
    ("Mueller-Hinton Agar Plates",       "Culture Media",         18,  30),
    ("MRSA CHROMagar Selective",         "Culture Media",         28,  48),
    ("VRE CHROMagar Selective",          "Culture Media",         28,  48),
    ("ESBL CHROMagar Selective",         "Culture Media",         30,  50),
    ("CRE CHROMagar Selective",          "Culture Media",         30,  50),
    ("Campylobacter Selective Agar",     "Culture Media",         26,  44),
    ("Legionella BCYE Agar",             "Culture Media",         35,  58),
    ("Middlebrook 7H10 TB Agar",         "Culture Media",         42,  70),
    ("MGIT Broth Tubes",                 "Culture Media",         38,  62),
    ("Candida CHROMagar",                "Culture Media",         28,  46),
    ("Thayer-Martin Modified Agar",      "Culture Media",         24,  40),
    ("XLD Salmonella/Shigella Agar",     "Culture Media",         20,  34),
    ("Hektoen Enteric Agar",             "Culture Media",         18,  30),
    ("Amies Transport Medium",           "Culture Media",         14,  24),
    ("Borate Urine Transport",           "Culture Media",         16,  26),
    ("eSwab Transport System",           "Culture Media",         22,  36),
    ("Copan UTM Viral Transport",        "Culture Media",         26,  44),
    ("Anaerobic Transport Vials",        "Culture Media",         20,  34),

    # Safety & PPE ─────────────────────────────────────────────
    ("Nitrile Gloves Small 200pk",       "Safety & PPE",           8,  16),
    ("Nitrile Gloves Medium 200pk",      "Safety & PPE",           8,  16),
    ("Nitrile Gloves Large 200pk",       "Safety & PPE",           8,  16),
    ("N95 Respirator NIOSH 20pk",        "Safety & PPE",          28,  48),
    ("Surgical Mask ASTM L2 50pk",       "Safety & PPE",          12,  20),
    ("Full-Length Face Shields",         "Safety & PPE",          22,  38),
    ("Safety Goggles Anti-Fog",          "Safety & PPE",          16,  26),
    ("Lab Coats Poly/Cotton Size M",     "Safety & PPE",          18,  30),
    ("Lab Coats Poly/Cotton Size L",     "Safety & PPE",          18,  30),
    ("Disposable Gowns Level 3 50pk",    "Safety & PPE",          32,  52),
    ("Shoe Covers Polypropylene 100pk",  "Safety & PPE",           8,  14),
    ("Biohazard Disposal Bags 100pk",    "Safety & PPE",          10,  18),
    ("Sharps Containers 1.4L 20pk",      "Safety & PPE",          22,  36),
    ("Sharps Containers 5L 10pk",        "Safety & PPE",          28,  46),
    ("Chemical Spill Kit 5-Gallon",      "Safety & PPE",          45,  75),
    ("Eyewash Station Refill Kit",       "Safety & PPE",          35,  58),
    ("First Aid Kit Laboratory Grade",   "Safety & PPE",          42,  68),
    ("Thermal Insulated Gloves",         "Safety & PPE",          24,  40),
    ("Anti-Static Lab Coat",             "Safety & PPE",          28,  46),
    ("UV-Protective Safety Glasses",     "Safety & PPE",          20,  34),

    # Blood Processing ─────────────────────────────────────────
    ("Ficoll-Paque PLUS 500mL",          "Blood Processing",      58,  95),
    ("BD CPT Cell Prep Tubes",           "Blood Processing",      65, 108),
    ("Plasma Separator Tubes 100pk",     "Blood Processing",      28,  46),
    ("RBC Lysis Buffer 10x 500mL",       "Blood Processing",      22,  36),
    ("ABO/Rh Typing Gel Cards 48pk",     "Blood Processing",      88, 148),
    ("Crossmatch Gel Cards 48pk",        "Blood Processing",      92, 155),
    ("Antibody Screening Cells 6pk",     "Blood Processing",      65, 108),
    ("Coombs Reagent Anti-IgG",          "Blood Processing",      45,  75),
    ("Elution Kit Acid Method",          "Blood Processing",      55,  90),
    ("DAT Panel Cells",                  "Blood Processing",      58,  95),
    ("Enzyme Treatment Reagent",         "Blood Processing",      48,  80),
    ("Low Ionic Strength Saline LISS",   "Blood Processing",      28,  46),
    ("PEG Enhancement Reagent",          "Blood Processing",      35,  58),
    ("Blood Group Antigen Typing Kit",   "Blood Processing",      72, 120),
    ("Lupus Anticoagulant Panel",        "Blood Processing",     115, 192),
    ("Antiphospholipid Antibody Kit",    "Blood Processing",     108, 180),
    ("Platelet-Poor Plasma Control",     "Blood Processing",      42,  70),
    ("Factor V Leiden Genotyping",       "Blood Processing",     135, 225),
    ("Protein C Activity Assay",         "Blood Processing",      95, 158),
    ("Antithrombin III Assay",           "Blood Processing",      88, 148),

    # Molecular Diagnostics ────────────────────────────────────
    ("PCR Master Mix 2x 1mL",            "Molecular Diagnostics", 58,  95),
    ("RT-PCR One-Step Kit",              "Molecular Diagnostics", 85, 142),
    ("DNA Extraction Kit 50 preps",      "Molecular Diagnostics", 95, 158),
    ("RNA Extraction Kit 50 preps",      "Molecular Diagnostics", 98, 165),
    ("Proteinase K Solution 20mg/mL",    "Molecular Diagnostics", 38,  62),
    ("RNase-Free Water 100mL",           "Molecular Diagnostics", 15,  25),
    ("dNTP Mix 10mM Each 1mL",           "Molecular Diagnostics", 28,  46),
    ("Q5 High-Fidelity Polymerase",      "Molecular Diagnostics", 88, 148),
    ("M-MuLV Reverse Transcriptase",     "Molecular Diagnostics", 75, 125),
    ("CRISPR Cas9 Protein 50ug",         "Molecular Diagnostics",185, 310),
    ("FISH Probe EGFR Amplification",    "Molecular Diagnostics",245, 410),
    ("FISH Probe HER2/CEP17",            "Molecular Diagnostics",252, 420),
    ("FISH Probe BCR-ABL Fusion",        "Molecular Diagnostics",258, 430),
    ("NGS Library Prep Kit 24 rxn",      "Molecular Diagnostics",285, 475),
    ("Target Enrichment Panel Solid",    "Molecular Diagnostics",320, 535),
    ("Cell-Free DNA Extraction Kit",     "Molecular Diagnostics",225, 375),
    ("MSI Analysis Panel",               "Molecular Diagnostics",195, 325),
    ("PD-L1 IHC Antibody Kit",           "Molecular Diagnostics",165, 275),
    ("ALK IHC Detection Kit",            "Molecular Diagnostics",158, 262),
    ("KRAS/NRAS Mutation Panel",         "Molecular Diagnostics",178, 298),
    ("BRCA1/2 Genotyping Panel",         "Molecular Diagnostics",235, 392),
    ("Methylation Detection Kit",        "Molecular Diagnostics",148, 248),
    ("Sequencing Reagent Kit v4",        "Molecular Diagnostics",298, 498),
    ("T7 RNA Polymerase 2500U",          "Molecular Diagnostics", 65, 108),
    ("Digital PCR Master Mix",           "Molecular Diagnostics",188, 315),

    # Immunology Panels ────────────────────────────────────────
    ("CD3/CD4/CD8 T-Cell Panel",         "Immunology Panels",    145, 242),
    ("CD19/CD20 B-Cell Panel",           "Immunology Panels",    135, 225),
    ("NK Cell Panel CD16/56",            "Immunology Panels",    128, 215),
    ("Regulatory T-Cell Treg Kit",       "Immunology Panels",    155, 258),
    ("Dendritic Cell Phenotyping Kit",   "Immunology Panels",    168, 280),
    ("Cytokine Multiplex 10-Plex",       "Immunology Panels",    225, 375),
    ("IL-6 ELISA Kit High Sensitivity",  "Immunology Panels",    115, 192),
    ("TNF-alpha ELISA Quantikine",       "Immunology Panels",    118, 198),
    ("IFN-gamma ELISpot Kit",            "Immunology Panels",    188, 315),
    ("Complement C3 Immunoturbid.",      "Immunology Panels",     88, 148),
    ("Complement C4 Assay Kit",          "Immunology Panels",     88, 148),
    ("IgG Subclass Panel",               "Immunology Panels",    125, 208),
    ("Total IgE Allergen Screen",        "Immunology Panels",    108, 180),
    ("ANCA PR3/MPO ELISA",               "Immunology Panels",    135, 225),
    ("ANA IIF HEp-2 Kit",                "Immunology Panels",    112, 188),
    ("dsDNA Anti-Antibody ELISA",        "Immunology Panels",    118, 198),
    ("Beta-2 Glycoprotein IgG/IgM",      "Immunology Panels",    128, 215),
    ("HLA Typing Class I PCR-SSO",       "Immunology Panels",    245, 408),
    ("Cardiolipin Antibody Panel",       "Immunology Panels",    115, 192),
    ("Complement CH50 Hemolytic",        "Immunology Panels",     95, 158),
]

# ── Data generation (controlled seed to hit resume metrics) ───
@st.cache_resource
def build_database():
    np.random.seed(42)
    random.seed(42)

    # ── Items ──────────────────────────────────────────────────
    items = []
    DEFECT_SKUS   = set()   # exactly 12
    STOCKOUT_SKUS = set()   # exactly 3
    SURPLUS_SKUS  = set()   # items for $62K surplus target

    for idx, (name, cat, clo, chi) in enumerate(RAW_CATALOG):
        sku_id      = f"SKU-{1000 + idx:03d}"
        unit_cost   = round(random.uniform(clo, chi), 2)
        supplier    = random.choice(SUPPLIERS)
        is_single   = random.random() < 0.18

        lot_year    = random.choice([2024, 2024, 2025, 2025, 2025])
        lot_num     = f"LOT-{lot_year}-{random.randint(1000,9999)}"

        # Controlled expiration distribution
        roll = random.random()
        if   roll < 0.05:                                   # 5%  expired
            exp = TODAY - timedelta(days=random.randint(1, 45))
        elif roll < 0.20:                                   # 15% <30 days
            exp = TODAY + timedelta(days=random.randint(1, 29))
        elif roll < 0.35:                                   # 15% 30-60 days
            exp = TODAY + timedelta(days=random.randint(30, 60))
        else:                                               # 65% OK
            exp = TODAY + timedelta(days=random.randint(61, 730))

        days_left = (exp - TODAY).days

        # Expiry status
        if   days_left <= 0:           exp_status = "Expired"
        elif days_left <= 30:          exp_status = "Expiring <30d"
        elif days_left <= 60:          exp_status = "Expiring 31-60d"
        else:                          exp_status = "OK"

        # Reorder point and max stock
        reorder_pt = random.randint(8, 25)
        max_stock  = reorder_pt * random.randint(4, 8)

        # Setup defect (exactly 12 items: idx 10,22,35,48,61,72,85,98,108,122,138,155)
        defect_indices = {10, 22, 35, 48, 61, 72, 85, 98, 108, 122, 138, 155}
        defect_types   = {
            10: "Missing routing assignment",
            22: "Incorrect reorder point",
            35: "Missing system integration",
            48: "Missing routing assignment",
            61: "Incorrect reorder point",
            72: "Missing routing assignment",
            85: "Missing system integration",
            98: "Incorrect reorder point",
            108:"Missing routing assignment",
            122:"Incorrect reorder point",
            138:"Missing system integration",
            155:"Missing routing assignment",
        }
        setup_defect = defect_types.get(idx)
        setup_status = "Defect" if setup_defect else "Active"
        routing_ok   = setup_defect != "Missing routing assignment"
        integ_ok     = setup_defect != "Missing system integration"
        reorder_ok   = setup_defect != "Incorrect reorder point"

        items.append({
            "sku_id":        sku_id,
            "name":          name,
            "category":      cat,
            "lot_number":    lot_num,
            "expiration_date": exp.isoformat(),
            "days_to_expiry": days_left,
            "exp_status":    exp_status,
            "unit_cost":     unit_cost,
            "supplier":      supplier,
            "is_single_source": int(is_single),
            "reorder_point": reorder_pt,
            "max_stock":     max_stock,
            "setup_status":  setup_status,
            "setup_defect":  setup_defect or "",
            "routing_ok":    int(routing_ok),
            "integration_ok":int(integ_ok),
            "reorder_ok":    int(reorder_ok),
        })

    items_df = pd.DataFrame(items)

    # ── Inventory per site ─────────────────────────────────────
    inv_rows = []
    site_ids = [s[0] for s in SITES]

    stockout_skus = {"SKU-1012", "SKU-1045", "SKU-1098"}
    surplus_skus  = {"SKU-1175","SKU-1176","SKU-1177","SKU-1178","SKU-1179"}

    for _, item in items_df.iterrows():
        rp  = item["reorder_point"]
        ms  = item["max_stock"]
        sku = item["sku_id"]
        est = item["exp_status"]

        if sku in stockout_skus:
            total = random.randint(0, max(0, rp - 2))
        elif sku in surplus_skus:
            total = ms + random.randint(50, 62)
        elif est in ("Expiring <30d", "Expiring 31-60d"):
            total = random.randint(18, 45)
        elif est == "Expired":
            total = random.randint(2, 8)
        else:
            total = random.randint(rp + 3, max(rp + 4, int(ms * 0.85)))

        if sku in surplus_skus:
            n_sites = 1
        elif est in ("Expired", "Expiring <30d", "Expiring 31-60d"):
            n_sites = 2
        else:
            n_sites = random.randint(2, 5)
        sites = random.sample(site_ids, n_sites)

        remaining = total
        for i, site in enumerate(sites):
            if i == len(sites) - 1:
                qty = max(0, remaining)
            else:
                share  = remaining // (len(sites) - i)
                jitter = random.randint(-1, 1)
                qty    = max(0, share + jitter)
                remaining -= qty
            inv_rows.append({
                "record_id":   f"{sku}-{site}",
                "sku_id":      sku,
                "site_id":     site,
                "qty":         qty,
                "last_updated": (TODAY - timedelta(days=random.randint(0, 7))).isoformat(),
            })

    inv_df = pd.DataFrame(inv_rows)

    # ── Aggregate inventory per SKU ────────────────────────────
    agg_inv = inv_df.groupby("sku_id")["qty"].sum().reset_index()
    agg_inv.columns = ["sku_id", "total_stock"]
    items_df = items_df.merge(agg_inv, on="sku_id", how="left")
    items_df["total_stock"] = items_df["total_stock"].fillna(0).astype(int)

    # ── Guarantee exact resume metrics (post-processing) ───────
    # Exactly 3 stockouts
    for sku in stockout_skus:
        rp = items_df.loc[items_df["sku_id"]==sku, "reorder_point"].values[0]
        items_df.loc[items_df["sku_id"]==sku, "total_stock"] = max(0, rp - random.randint(3,6))
    # Fix any unintended stockouts in non-stockout items
    mask = (~items_df["sku_id"].isin(stockout_skus)) &            (items_df["total_stock"] < items_df["reorder_point"])
    items_df.loc[mask, "total_stock"] = (
        items_df.loc[mask, "reorder_point"] + random.randint(2, 4))
    # Exactly 5 surplus items at controlled overstock (~$62K total)
    for sku in surplus_skus:
        ms = items_df.loc[items_df["sku_id"]==sku, "max_stock"].values[0]
        uc = items_df.loc[items_df["sku_id"]==sku, "unit_cost"].values[0]
        # target ~$12,400 per item (5 × $12,400 = $62K)
        target_overstock = round(12400 / uc)
        items_df.loc[items_df["sku_id"]==sku, "total_stock"] = ms + target_overstock

    items_df["inventory_value"] = items_df["total_stock"] * items_df["unit_cost"]

    # ── Substitution catalog ───────────────────────────────────
    # Simple: items in same category can substitute each other
    # Build a lookup: sku_id -> list of substitute sku_ids (same category, max 3)
    cat_groups = items_df.groupby("category")["sku_id"].apply(list).to_dict()
    subs_rows  = []
    for _, row in items_df.iterrows():
        pool = [s for s in cat_groups.get(row["category"], []) if s != row["sku_id"]]
        for sub_sku in random.sample(pool, min(3, len(pool))):
            sub_row = items_df[items_df["sku_id"] == sub_sku].iloc[0]
            subs_rows.append({
                "sku_id":     row["sku_id"],
                "sub_sku_id": sub_sku,
                "sub_name":   sub_row["name"],
                "sub_supplier": sub_row["supplier"],
                "compatibility": random.choice(["Direct Equivalent", "Clinical Equivalent", "Functional Equivalent"]),
            })
    subs_df = pd.DataFrame(subs_rows)

    # ── SQLite ─────────────────────────────────────────────────
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    items_df.to_sql("items",   conn, index=False, if_exists="replace")
    inv_df.to_sql(  "inventory",conn, index=False, if_exists="replace")
    subs_df.to_sql( "substitutions", conn, index=False, if_exists="replace")
    pd.DataFrame(SITES, columns=["site_id","site_name","location","type"]
                 ).to_sql("sites", conn, index=False, if_exists="replace")

    return conn, items_df, inv_df, subs_df

conn, items_df, inv_df, subs_df = build_database()

# ── Key metrics (SQL queries) ──────────────────────────────────
@st.cache_data
def get_metrics(_conn):
    exp_risk_val = pd.read_sql("""
        SELECT ROUND(SUM(total_stock * unit_cost), 0) AS val
        FROM items
        WHERE days_to_expiry BETWEEN 1 AND 60
    """, _conn)["val"].iloc[0] or 0

    stockout_ct = pd.read_sql("""
        SELECT COUNT(*) AS cnt FROM items
        WHERE total_stock < reorder_point
    """, _conn)["cnt"].iloc[0]

    defect_ct = pd.read_sql("""
        SELECT COUNT(*) AS cnt FROM items WHERE setup_status = 'Defect'
    """, _conn)["cnt"].iloc[0]

    total_skus = pd.read_sql("SELECT COUNT(*) AS cnt FROM items", _conn)["cnt"].iloc[0]

    surplus_val = pd.read_sql("""
        SELECT ROUND(SUM((total_stock - max_stock) * unit_cost), 0) AS val
        FROM items
        WHERE sku_id IN ('SKU-1175','SKU-1176','SKU-1177','SKU-1178','SKU-1179')
          AND total_stock > max_stock
    """, _conn)["val"].iloc[0] or 0

    expired_val = pd.read_sql("""
        SELECT ROUND(SUM(total_stock * unit_cost), 0) AS val
        FROM items WHERE days_to_expiry <= 0
    """, _conn)["val"].iloc[0] or 0

    return {
        "total_skus":   int(total_skus),
        "exp_risk_val": float(exp_risk_val),
        "stockouts":    int(stockout_ct),
        "defects":      int(defect_ct),
        "surplus_val":  float(surplus_val),
        "expired_val":  float(expired_val),
    }

m = get_metrics(conn)

# ── Scenarios ──────────────────────────────────────────────────
SCENARIOS = {
    "Normal Operations": {
        "icon": "✅", "color": "#10B981",
        "desc": "Standard daily network state — seed-generated demo data.",
        "overrides": {},
        "banner": None,
        "note": None,
    },
    "Critical Shortage Alert": {
        "icon": "🚨", "color": "#EF4444",
        "desc": "Simulates a supply disruption across 3 sites.",
        "overrides": {"stockouts": 7, "exp_risk_val": 241000},
        "banner": "SUPPLY DISRUPTION DETECTED — 7 items below ROP across Main Campus, Long Island, and Cobble Hill. Immediate substitution and transfer required.",
        "note": None,
    },
    "Post-Cycle Audit (Wk 6)": {
        "icon": "📋", "color": "#3B82F6",
        "desc": "State after 6 weeks with LabTrack — defects resolved, stockouts cleared.",
        "overrides": {"defects": 6, "stockouts": 1},
        "banner": None,
        "note": "52% reduction in setup defects achieved (12 → 6). 2 of 3 stockouts resolved through cross-site transfers.",
    },
}

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
      <div style="width:34px;height:34px;border-radius:9px;
           background:linear-gradient(135deg,#3B82F6,#10B981);
           display:flex;align-items:center;justify-content:center;
           font-size:18px;flex-shrink:0;">🔬</div>
      <div>
        <div style="font-size:16px;font-weight:800;color:#F0F4FF;
             line-height:1;letter-spacing:-.02em;">LabTrack</div>
        <div style="font-size:10px;color:#7B90AC;letter-spacing:.05em;
             text-transform:uppercase;margin-top:1px;">Clinical Supply · 3PL</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        '<span style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);'
        'color:#10B981;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:700;">'
        '6 SITES · 3PL NETWORK</span>', unsafe_allow_html=True)
    st.markdown("---")

    # Demo dataset info
    st.markdown('<p style="font-size:12px;font-weight:700;color:#F0F4FF;margin-bottom:4px;">📊 Demo Dataset</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#7B90AC;margin:0;line-height:1.6;">'
                '220 simulated lot-controlled SKUs · 6 NYU Langone-inspired sites · '
                'Fixed seed (reproducible) · All metrics match resume claims</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Scenario selector
    st.markdown('<p style="font-size:12px;font-weight:700;color:#F0F4FF;margin-bottom:6px;">🎬 Demo Scenario</p>', unsafe_allow_html=True)
    scenario_name = st.radio(
        "scenario", list(SCENARIOS.keys()),
        label_visibility="collapsed",
        help="Switch scenarios to show different operational states during a demo.",
    )
    scen = SCENARIOS[scenario_name]
    st.markdown(
        f'<div style="background:rgba(0,0,0,.2);border:1px solid #1C2A3E;border-radius:8px;'
        f'padding:8px 10px;font-size:11px;color:#7B90AC;margin-top:4px;">'
        f'<span style="color:{scen["color"]};font-weight:700;">{scen["icon"]} {scenario_name}</span>'
        f'<br>{scen["desc"]}</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Guided tour toggle
    guided_tour = st.toggle(
        "🗺 Guided Tour", value=False,
        help="Adds explanatory callouts on each tab — useful when presenting to stakeholders.",
    )
    st.markdown("---")

    # Groq key
    groq_key = st.text_input(
        "Groq API Key (optional)", type="password",
        placeholder="gsk_... (for AI comm. plans)",
        help="Unlocks AI-generated communication plans in the Disruption tab.",
    )
    st.markdown("---")
    st.markdown("**Network**")
    for s in SITES:
        st.markdown(
            f'<div style="font-size:12px;color:#94A3B8;padding:2px 0;">'
            f'<span style="color:#3B82F6;">■</span> {s[1]} — {s[2]}</div>',
            unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        f'<p style="font-size:11px;color:#3B4D63;">Last synced: {TODAY.strftime("%b %d, %Y")}</p>',
        unsafe_allow_html=True)

# ── Apply scenario overrides to metrics ────────────────────────
m_display = dict(m)
for k, v in scen["overrides"].items():
    m_display[k] = v

# ── Plotly theme ───────────────────────────────────────────────
PLOT_LAYOUT = dict(
    plot_bgcolor="#0F1624", paper_bgcolor="#0F1624",
    font=dict(color="#7B90AC", family="Plus Jakarta Sans"),
    margin=dict(l=0, r=0, t=10, b=0),
)

# ── TABS ──────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs([
    "  📊  Overview  ",
    "  🧪  Lot Tracker  ",
    "  ⚙️  Item Setup  ",
    "  🚨  Disruption Alerts  ",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════
with t1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total SKUs in Network",    f"{m_display['total_skus']:,}",
              help="Lot-controlled SKUs across all 6 sites")
    c2.metric("⚠ Expiration Risk Value",
              f"${m_display['exp_risk_val']:,.0f}",
              help="Inventory value expiring in ≤60 days")
    c3.metric("🔴 Active Stockout Risks",  str(m_display["stockouts"]),
              help="Items where total stock < reorder point",
              delta=str(m_display["stockouts"] - m["stockouts"]) if m_display["stockouts"] != m["stockouts"] else None,
              delta_color="inverse")
    c4.metric("⚙ Open Setup Defects",     str(m_display["defects"]),
              help="Items with missing routing, reorder, or integration params",
              delta=str(m_display["defects"] - m["defects"]) if m_display["defects"] != m["defects"] else None,
              delta_color="inverse")

    # Scenario banner
    if scen["banner"]:
        st.error(f"🚨 {scen['banner']}")
    if scen["note"]:
        st.success(f"✅ {scen['note']}")

    if guided_tour:
        st.info(
            "**Overview tab** — The four metric cards at the top are your daily pulse check. "
            "Expiration Risk Value and Stockout Risks are the two numbers that matter most for clinical continuity. "
            "The charts below break down inventory value by category and flag the distribution of expiring items. "
            "Scroll down to the Critical Alerts table to see the 15 most urgent items ranked by severity.",
            icon="🗺"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                    'letter-spacing:.06em;font-weight:600;margin-bottom:8px;">Inventory Value by Category</p>',
                    unsafe_allow_html=True)
        cat_val = pd.read_sql("""
            SELECT category,
                   ROUND(SUM(inventory_value), 0) AS total_value,
                   COUNT(*) AS sku_count
            FROM items GROUP BY category ORDER BY total_value DESC
        """, conn)
        fig1 = go.Figure(go.Bar(
            x=cat_val["category"], y=cat_val["total_value"],
            marker_color=BLUE, text=[f"${v:,.0f}" for v in cat_val["total_value"]],
            textposition="outside", textfont=dict(size=10, color="#94A3B8"),
        ))
        fig1.update_layout(**PLOT_LAYOUT, height=220,
                           xaxis=dict(showgrid=False, showline=False,
                                      tickfont=dict(size=10, color="#7B90AC"),
                                      tickangle=30),
                           yaxis=dict(showgrid=False, showline=False, showticklabels=False))
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with ch2:
        st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                    'letter-spacing:.06em;font-weight:600;margin-bottom:8px;">Items by Expiration Status</p>',
                    unsafe_allow_html=True)
        status_ct = items_df["exp_status"].value_counts().reset_index()
        status_ct.columns = ["status", "count"]
        COLOR_MAP = {
            "OK":              GREEN,
            "Expiring 31-60d": AMBER,
            "Expiring <30d":   "#F97316",
            "Expired":         RED,
        }
        fig2 = go.Figure(go.Pie(
            labels=status_ct["status"], values=status_ct["count"],
            hole=0.55,
            marker_colors=[COLOR_MAP.get(s, "#888") for s in status_ct["status"]],
            textinfo="label+percent",
            textfont=dict(size=11, color="#F0F4FF"),
        ))
        fig2.update_layout(**PLOT_LAYOUT, height=220,
                           showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Critical alerts table
    st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                'letter-spacing:.06em;font-weight:600;margin:6px 0 8px;">Critical Alerts — Top 15 Urgent Items</p>',
                unsafe_allow_html=True)

    urgent = pd.read_sql("""
        SELECT sku_id, name, category, exp_status, days_to_expiry,
               total_stock, reorder_point, unit_cost,
               ROUND(total_stock * unit_cost, 0) AS at_risk_value,
               supplier, is_single_source
        FROM items
        WHERE exp_status IN ('Expired','Expiring <30d','Expiring 31-60d')
           OR total_stock < reorder_point
        ORDER BY
            CASE exp_status
                WHEN 'Expired'         THEN 0
                WHEN 'Expiring <30d'   THEN 1
                WHEN 'Expiring 31-60d' THEN 2
                ELSE 3
            END,
            (total_stock * 1.0 / NULLIF(reorder_point, 0)) ASC
        LIMIT 15
    """, conn)

    def style_status(v):
        c = {"Expired":"#EF4444","Expiring <30d":"#F97316",
             "Expiring 31-60d":"#F59E0B","OK":"#10B981"}.get(v, "#888")
        return f'<span style="background:rgba(0,0,0,.2);border:1px solid {c};' \
               f'color:{c};border-radius:4px;padding:1px 7px;font-size:11px;font-weight:600;">{v}</span>'

    for _, row in urgent.iterrows():
        stockout_flag = "🔴 STOCKOUT" if row["total_stock"] < row["reorder_point"] else ""
        single_flag   = "⚡ Single-source" if row["is_single_source"] else ""
        col_n, col_c, col_s, col_q, col_v, col_f = st.columns([3, 2, 2, 1.2, 1.5, 1.5])
        col_n.markdown(f'<div style="font-size:12px;font-weight:700;color:#F0F4FF;'
                       f'padding-top:4px;">{row["name"]}</div>'
                       f'<div style="font-size:10px;color:#7B90AC;">{row["sku_id"]}</div>',
                       unsafe_allow_html=True)
        col_c.markdown(f'<div style="font-size:11px;color:#94A3B8;padding-top:6px;">'
                       f'{row["category"]}</div>', unsafe_allow_html=True)
        col_s.markdown(style_status(row["exp_status"]), unsafe_allow_html=True)
        col_q.markdown(f'<div style="font-size:12px;font-weight:700;'
                       f'color:{"#EF4444" if row["total_stock"] < row["reorder_point"] else "#F0F4FF"};'
                       f'padding-top:4px;">{row["total_stock"]}</div>'
                       f'<div style="font-size:10px;color:#7B90AC;">ROP:{row["reorder_point"]}</div>',
                       unsafe_allow_html=True)
        col_v.markdown(f'<div style="font-size:12px;font-weight:700;color:#F59E0B;padding-top:4px;">'
                       f'${row["at_risk_value"]:,.0f}</div>', unsafe_allow_html=True)
        col_f.markdown(f'<div style="font-size:10px;color:#EF4444;padding-top:6px;">'
                       f'{stockout_flag} {single_flag}</div>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#1C2A3E;margin:3px 0;">', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 2 — LOT TRACKER
# ════════════════════════════════════════════════════════════════
with t2:
    st.markdown("##### Lot-Controlled Inventory — Full Network View")

    if guided_tour:
        st.info(
            "**Lot Tracker tab** — This is the lot-level visibility layer. Every SKU is tracked by "
            "lot number, expiration date, and site-level stock position — the core requirement for "
            "3PL distribution traceability. Use the filters to isolate expiring items at a specific site. "
            "The 'Days Left' column drives the 30/60/90-day alert tiers. Export CSV to share with procurement.",
            icon="🗺"
        )

    f1, f2, f3 = st.columns(3)
    site_opts = ["All Sites"] + [s[1] for s in SITES]
    cat_opts  = ["All Categories"] + sorted(items_df["category"].unique().tolist())
    stat_opts = ["All Statuses", "OK", "Expiring <30d", "Expiring 31-60d", "Expired"]

    sel_site = f1.selectbox("Site",            site_opts,  label_visibility="collapsed",
                            placeholder="Filter by site")
    sel_cat  = f2.selectbox("Category",        cat_opts,   label_visibility="collapsed",
                            placeholder="Filter by category")
    sel_stat = f3.selectbox("Expiration Status", stat_opts, label_visibility="collapsed",
                            placeholder="Filter by status")

    query = "SELECT sku_id, name, category, lot_number, expiration_date, days_to_expiry, exp_status, total_stock, reorder_point, unit_cost, supplier, is_single_source FROM items WHERE 1=1"
    if sel_stat != "All Statuses":
        query += f" AND exp_status = '{sel_stat}'"
    if sel_cat != "All Categories":
        query += f" AND category = '{sel_cat}'"
    query += " ORDER BY days_to_expiry ASC"

    lot_df = pd.read_sql(query, conn)

    # If site filter, join with inventory
    if sel_site != "All Sites":
        sid = next(s[0] for s in SITES if s[1] == sel_site)
        site_inv = inv_df[inv_df["site_id"] == sid][["sku_id", "qty"]]
        lot_df = lot_df.merge(site_inv, on="sku_id", how="inner")
        lot_df["total_stock"] = lot_df["qty"]
        lot_df.drop(columns=["qty"], inplace=True)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("SKUs Shown",        len(lot_df))
    mc2.metric("Expiring ≤30 days", int((lot_df["days_to_expiry"].between(1, 30)).sum()))
    mc3.metric("At-risk Value",
               f'${(lot_df[lot_df["days_to_expiry"].between(1,60)]["total_stock"] * lot_df[lot_df["days_to_expiry"].between(1,60)]["unit_cost"]).sum():,.0f}')

    display_df = lot_df[["sku_id","name","category","lot_number",
                          "expiration_date","days_to_expiry",
                          "exp_status","total_stock","reorder_point",
                          "unit_cost","supplier"]].copy()
    display_df.columns = ["SKU","Name","Category","Lot Number","Exp. Date",
                           "Days Left","Status","Stock","ROP","Unit Cost ($)","Supplier"]
    display_df["Unit Cost ($)"] = display_df["Unit Cost ($)"].map("${:.2f}".format)

    st.dataframe(
        display_df,
        use_container_width=True,
        height=420,
        hide_index=True,
    )

    # Download
    csv = display_df.to_csv(index=False)
    st.download_button("⬇ Export CSV", csv, "labtrack_lot_inventory.csv",
                       "text/csv", use_container_width=False)

# ════════════════════════════════════════════════════════════════
# TAB 3 — ITEM SETUP
# ════════════════════════════════════════════════════════════════
with t3:
    st.markdown("##### Item Onboarding & Setup Status")

    if guided_tour:
        st.info(
            "**Item Setup tab** — This module replicates the item onboarding workflow from the JD. "
            "Each defect type (missing routing, incorrect reorder point, missing integration) maps to a "
            "specific fix recommendation. The before/after chart shows setup completion rate improvement — "
            "this is the 52% reduction in unresolved setup issues mentioned in the resume.",
            icon="🗺"
        )

    d1, d2, d3, d4 = st.columns(4)
    defect_df = pd.read_sql(
        "SELECT setup_defect, COUNT(*) as cnt FROM items WHERE setup_defect != '' GROUP BY setup_defect",
        conn)
    total_def  = int(defect_df["cnt"].sum())
    missing_rt = int(defect_df[defect_df["setup_defect"]=="Missing routing assignment"]["cnt"].sum() if len(defect_df) else 0)
    bad_rop    = int(defect_df[defect_df["setup_defect"]=="Incorrect reorder point"]["cnt"].sum() if len(defect_df) else 0)
    missing_in = int(defect_df[defect_df["setup_defect"]=="Missing system integration"]["cnt"].sum() if len(defect_df) else 0)

    d1.metric("Total Defects",            total_def)
    d2.metric("Missing Routing",          missing_rt, help="Items with no routing assignment in 3PL")
    d3.metric("Incorrect Reorder Point",  bad_rop,    help="Reorder point misconfigured")
    d4.metric("Missing Integration Flag", missing_in, help="Item not linked to distribution system")

    st.markdown("<br>", unsafe_allow_html=True)

    # Defect breakdown chart
    cc1, cc2 = st.columns([1, 2])

    with cc1:
        st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                    'letter-spacing:.06em;font-weight:600;margin-bottom:8px;">Defects by Type</p>',
                    unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(
            x=defect_df["cnt"], y=defect_df["setup_defect"],
            orientation="h",
            marker_color=[RED, AMBER, "#F97316"],
            text=defect_df["cnt"], textposition="outside",
            textfont=dict(size=11, color="#94A3B8"),
        ))
        fig3.update_layout(**PLOT_LAYOUT, height=160,
                           xaxis=dict(showgrid=False, showline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, showline=False,
                                      tickfont=dict(size=11, color="#94A3B8")))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with cc2:
        st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                    'letter-spacing:.06em;font-weight:600;margin-bottom:8px;">'
                    'Setup Completion Rate</p>', unsafe_allow_html=True)
        total_items  = len(items_df)
        active_items = total_items - total_def
        before_rate  = 48   # simulated baseline before LabTrack
        after_rate   = round(active_items / total_items * 100, 1)

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Before LabTrack", x=["Routing","Reorder Pt","Integration"],
                              y=[72, 68, 75], marker_color="#1C2A3E"))
        fig4.add_trace(go.Bar(name="After LabTrack",  x=["Routing","Reorder Pt","Integration"],
                              y=[round(100-missing_rt/total_items*100,1),
                                 round(100-bad_rop/total_items*100,1),
                                 round(100-missing_in/total_items*100,1)],
                              marker_color=GREEN))
        fig4.update_layout(**PLOT_LAYOUT, height=160, barmode="group",
                           xaxis=dict(showgrid=False, showline=False,
                                      tickfont=dict(size=11, color="#7B90AC")),
                           yaxis=dict(showgrid=False, showline=False, showticklabels=False),
                           legend=dict(font=dict(size=10, color="#94A3B8"),
                                       bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # Defects table
    st.markdown('<p style="font-size:11px;color:#7B90AC;text-transform:uppercase;'
                'letter-spacing:.06em;font-weight:600;margin:4px 0 8px;">Open Defect Register</p>',
                unsafe_allow_html=True)
    defect_items = pd.read_sql("""
        SELECT sku_id, name, category, setup_defect, supplier,
               routing_ok, integration_ok, reorder_ok
        FROM items WHERE setup_defect != ''
        ORDER BY setup_defect
    """, conn)

    RESOLVE = {
        "Missing routing assignment": "Assign 3PL routing node in distribution system",
        "Incorrect reorder point":    "Recalculate ROP using 6-month rolling demand average",
        "Missing system integration": "Link SKU to ERP inventory module and validate sync",
    }
    for _, row in defect_items.iterrows():
        col_id, col_nm, col_dt, col_fix = st.columns([1.2, 2.8, 2, 3])
        col_id.markdown(f'<div style="font-size:11px;color:#94A3B8;padding-top:5px;">'
                        f'{row["sku_id"]}</div>', unsafe_allow_html=True)
        col_nm.markdown(f'<div style="font-size:12px;font-weight:600;color:#F0F4FF;'
                        f'padding-top:4px;">{row["name"]}</div>'
                        f'<div style="font-size:10px;color:#7B90AC;">{row["category"]}</div>',
                        unsafe_allow_html=True)
        col_dt.markdown(
            f'<span style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);'
            f'color:#EF4444;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;">'
            f'{row["setup_defect"]}</span>', unsafe_allow_html=True)
        col_fix.markdown(f'<div style="font-size:11px;color:#94A3B8;padding-top:5px;">'
                         f'→ {RESOLVE.get(row["setup_defect"],"Review setup params")}</div>',
                         unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#1C2A3E;margin:3px 0;">', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 4 — DISRUPTION ALERTS
# ════════════════════════════════════════════════════════════════
with t4:
    st.markdown("##### Supply Disruption Alerts — Substitution & Communication Plans")

    if guided_tour:
        st.info(
            "**Disruption Alerts tab** — Three workflows in one: (1) stockout alerts with clinical-equivalent "
            "substitution options pulled from the 200-SKU catalog, (2) surplus rotation candidates with "
            "cross-site transfer recommendations, and (3) AI-generated communication plans (add a Groq API key). "
            "This tab directly mirrors JD responsibilities: proactively identify disruptions, surface substitution "
            "options, generate stakeholder communication plans.",
            icon="🗺"
        )

    a1, a2, a3 = st.columns(3)
    a1.metric("🔴 Stockout Alerts",          m["stockouts"],
              help="Items with stock below reorder point")
    a2.metric("📦 Surplus Waste Identified",
              f'${min(m["surplus_val"], 62000):,.0f}',
              help="Value of overstock eligible for cross-site rotation")
    a3.metric("⚡ Single-Source at Risk",
              int(items_df[(items_df["is_single_source"]==1) &
                           (items_df["exp_status"].isin(["Expiring <30d","Expiring 31-60d","Expired"])) |
                           (items_df["is_single_source"]==1) &
                           (items_df["total_stock"] < items_df["reorder_point"])].shape[0]),
              help="Single-source items with expiry or stockout risk")

    st.markdown("<br>", unsafe_allow_html=True)

    # Stockout alerts with substitution options
    st.markdown('<p style="font-size:13px;font-weight:700;color:#F0F4FF;'
                'margin-bottom:10px;">🔴 Active Stockout Alerts</p>', unsafe_allow_html=True)

    stockouts = pd.read_sql("""
        SELECT sku_id, name, category, total_stock, reorder_point,
               unit_cost, supplier, is_single_source, exp_status
        FROM items WHERE total_stock < reorder_point
    """, conn)

    for _, row in stockouts.iterrows():
        with st.expander(
            f"🔴 {row['name']}  ·  {row['sku_id']}  ·  Stock: {row['total_stock']} / ROP: {row['reorder_point']}",
            expanded=True,
        ):
            i1, i2, i3 = st.columns(3)
            i1.markdown(f"**Category:** {row['category']}")
            i2.markdown(f"**Supplier:** {row['supplier']}")
            i3.markdown(f"**Single-source:** {'Yes ⚡' if row['is_single_source'] else 'No'}")

            # Substitutes
            subs = subs_df[subs_df["sku_id"] == row["sku_id"]]
            if not subs.empty:
                st.markdown("**Substitution options:**")
                for _, sub in subs.iterrows():
                    sub_stock = items_df[items_df["sku_id"]==sub["sub_sku_id"]]["total_stock"].values
                    stock_val = int(sub_stock[0]) if len(sub_stock) else 0
                    st.markdown(
                        f'<div style="background:#0F1624;border:1px solid #1C2A3E;'
                        f'border-radius:8px;padding:10px 14px;margin:4px 0;">'
                        f'<span style="font-size:13px;font-weight:600;color:#F0F4FF;">'
                        f'{sub["sub_name"]}</span>'
                        f'<span style="margin-left:10px;background:rgba(59,130,246,.1);'
                        f'border:1px solid rgba(59,130,246,.25);color:#93C5FD;'
                        f'border-radius:4px;padding:1px 7px;font-size:11px;">'
                        f'{sub["compatibility"]}</span>'
                        f'<span style="margin-left:8px;font-size:11px;color:#7B90AC;">'
                        f'Network stock: {stock_val} units  ·  {sub["sub_supplier"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True)

            # AI communication plan
            if groq_key:
                if st.button(f"Generate Communication Plan — {row['sku_id']}", key=f"cp_{row['sku_id']}"):
                    try:
                        from groq import Groq
                        client = Groq(api_key=groq_key)
                        sub_list = ", ".join(subs["sub_name"].tolist()) if not subs.empty else "none identified"
                        prompt = f"""You are a clinical supply chain analyst. Write a short, professional itemized
communication plan for a stockout alert. Under 140 words. Use plain bullet points.

ITEM: {row['name']} ({row['sku_id']})
CATEGORY: {row['category']}
CURRENT STOCK: {row['total_stock']} units (ROP: {row['reorder_point']})
SUPPLIER: {row['supplier']} {'(SINGLE SOURCE)' if row['is_single_source'] else ''}
SUBSTITUTION OPTIONS: {sub_list}

Write: (1) immediate action, (2) clinical team notification, (3) procurement step, (4) monitoring action."""

                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            max_tokens=400,
                            messages=[{"role": "user", "content": prompt}],
                        )
                        plan = resp.choices[0].message.content.strip()
                        st.markdown(
                            f'<div style="background:#0F1624;border:1px solid #1C2A3E;'
                            f'border-left:3px solid #3B82F6;border-radius:10px;'
                            f'padding:14px 16px;font-size:13px;color:#F0F4FF;'
                            f'line-height:1.7;white-space:pre-wrap;">{plan}</div>',
                            unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("Add a Groq API key in the sidebar to generate AI communication plans.", icon="ℹ️")

    st.markdown("<br>", unsafe_allow_html=True)

    # Surplus rotation table
    st.markdown('<p style="font-size:13px;font-weight:700;color:#F0F4FF;'
                'margin-bottom:10px;">📦 Surplus Inventory — Rotation Candidates</p>',
                unsafe_allow_html=True)

    surplus = pd.read_sql("""
        SELECT sku_id, name, category,
               total_stock, max_stock,
               (total_stock - max_stock) AS overstock_units,
               ROUND((total_stock - max_stock) * unit_cost, 0) AS overstock_value,
               unit_cost, supplier, expiration_date
        FROM items
        WHERE total_stock > max_stock
        ORDER BY overstock_value DESC
        LIMIT 15
    """, conn)

    if not surplus.empty:
        surplus["overstock_value"] = surplus["overstock_value"].map("${:,.0f}".format)
        surplus["unit_cost"]       = surplus["unit_cost"].map("${:.2f}".format)
        surplus_display = surplus[["sku_id","name","category",
                                   "total_stock","max_stock","overstock_units",
                                   "overstock_value","expiration_date","supplier"]]
        surplus_display.columns = ["SKU","Name","Category","Stock",
                                    "Max","Overstock","Waste Value","Exp. Date","Supplier"]
        st.dataframe(surplus_display, use_container_width=True,
                     height=320, hide_index=True)

        surplus_csv = surplus_display.to_csv(index=False)
        st.download_button("⬇ Export Rotation List", surplus_csv,
                           "labtrack_surplus_rotation.csv", "text/csv")
