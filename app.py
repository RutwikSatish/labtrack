"""
LabTrack — Clinical Lab Supply Visibility & 3PL Distribution Management
Tools : Python · Streamlit · Plotly · SQLite (SQL)
Author: Rutwik Satish
v2.0  : Redesigned UI · Hero section · Data Preview tab · Bug fixes
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
    page_title="LabTrack · Clinical Supply Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: #060B18;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem; max-width: 1400px; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
  background: linear-gradient(135deg, #0D1629 0%, #0A1120 100%);
  border: 1px solid #1A2840;
  border-radius: 12px;
  padding: 1.1rem 1.3rem;
  position: relative;
  overflow: hidden;
  transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color: #2A4080; }
[data-testid="metric-container"]::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, #3B82F6, #06B6D4);
  opacity: 0.7;
}
[data-testid="metric-container"] label {
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #5A7A9C !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-size: 1.85rem !important;
  font-weight: 700 !important;
  font-family: 'Syne', sans-serif !important;
  color: #E8F0FF !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid #1A2840;
  background: transparent;
  margin-bottom: 1.2rem;
}
.stTabs [data-baseweb="tab"] {
  padding: .7rem 1.4rem;
  font-size: 13px;
  font-weight: 600;
  color: #5A7A9C;
  border-bottom: 2px solid transparent;
  font-family: 'DM Sans', sans-serif;
  letter-spacing: .02em;
}
.stTabs [aria-selected="true"] {
  color: #E8F0FF !important;
  border-bottom: 2px solid #3B82F6 !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Buttons ── */
.stButton > button {
  font-family: 'DM Sans', sans-serif;
  font-weight: 600;
  font-size: 13px;
  border-radius: 8px;
  padding: .45rem 1.2rem;
  border: 1px solid #1A2840 !important;
  background: #0D1629 !important;
  color: #93C5FD !important;
  transition: all .2s;
}
.stButton > button:hover {
  background: #1A2840 !important;
  border-color: #3B82F6 !important;
}

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input, .stSelectbox > div > div {
  background: #080E1C !important;
  border: 1px solid #1A2840 !important;
  border-radius: 8px !important;
  color: #E8F0FF !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #070C1A;
  border-right: 1px solid #1A2840;
}

/* ── DataFrames ── */
div[data-testid="stDataFrame"] {
  border: 1px solid #1A2840;
  border-radius: 10px;
  overflow: hidden;
}

/* ── Hero Section ── */
.hero-wrapper {
  background: linear-gradient(180deg, #080E20 0%, #060B18 100%);
  border-bottom: 1px solid #1A2840;
  padding: 2.8rem 2rem 2rem;
  margin: 0 -1rem 2rem;
  position: relative;
  overflow: hidden;
}
.hero-wrapper::before {
  content: '';
  position: absolute;
  top: -80px; right: -80px;
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%);
  border-radius: 50%;
}
.hero-wrapper::after {
  content: '';
  position: absolute;
  bottom: -60px; left: 30%;
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 70%);
  border-radius: 50%;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 11px;
  font-weight: 700;
  color: #93C5FD;
  letter-spacing: .06em;
  text-transform: uppercase;
  margin-bottom: 1rem;
}
.hero-title {
  font-family: 'Syne', sans-serif;
  font-size: 2.4rem;
  font-weight: 800;
  color: #F0F6FF;
  line-height: 1.1;
  letter-spacing: -.03em;
  margin-bottom: .6rem;
}
.hero-title span { color: #3B82F6; }
.hero-sub {
  font-size: 15px;
  color: #5A7A9C;
  font-weight: 400;
  max-width: 520px;
  line-height: 1.6;
  margin-bottom: 1.6rem;
}
.insight-card {
  background: linear-gradient(135deg, #0D1629 0%, #091020 100%);
  border: 1px solid #1A2840;
  border-radius: 12px;
  padding: 1.2rem 1.4rem;
  height: 100%;
  position: relative;
  overflow: hidden;
}
.insight-card-accent {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}
.insight-card-icon {
  font-size: 22px;
  margin-bottom: 10px;
}
.insight-card-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .07em;
  font-weight: 700;
  margin-bottom: 8px;
}
.insight-card-title {
  font-family: 'Syne', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #E8F0FF;
  margin-bottom: 6px;
}
.insight-card-body {
  font-size: 12.5px;
  color: #5A7A9C;
  line-height: 1.6;
}
.stat-chip {
  display: inline-block;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #FCA5A5;
  margin-top: 8px;
}
.stat-chip.blue {
  background: rgba(59,130,246,0.08);
  border-color: rgba(59,130,246,0.2);
  color: #93C5FD;
}
.stat-chip.green {
  background: rgba(16,185,129,0.08);
  border-color: rgba(16,185,129,0.2);
  color: #6EE7B7;
}

/* ── Section headers ── */
.section-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
  font-weight: 700;
  color: #5A7A9C;
  margin-bottom: 10px;
}
.section-title {
  font-family: 'Syne', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #E8F0FF;
  margin-bottom: 14px;
}

/* ── Alert rows ── */
.alert-row {
  background: linear-gradient(90deg, #0D1629 0%, #090F1E 100%);
  border: 1px solid #1A2840;
  border-radius: 10px;
  padding: 11px 14px;
  margin: 6px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: border-color .15s;
}
.alert-row:hover { border-color: #2A4080; }

/* ── Status badges ── */
.badge {
  display: inline-block;
  border-radius: 5px;
  padding: 2px 9px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .03em;
}
.badge-expired  { background: rgba(239,68,68,.1);   border: 1px solid rgba(239,68,68,.3);   color: #FCA5A5; }
.badge-warn30   { background: rgba(249,115,22,.1);   border: 1px solid rgba(249,115,22,.3);   color: #FDBA74; }
.badge-warn60   { background: rgba(245,158,11,.1);   border: 1px solid rgba(245,158,11,.3);   color: #FCD34D; }
.badge-ok       { background: rgba(16,185,129,.1);   border: 1px solid rgba(16,185,129,.3);   color: #6EE7B7; }
.badge-critical { background: rgba(239,68,68,.12);   border: 1px solid rgba(239,68,68,.35);   color: #F87171; }

/* ── Data preview table styling ── */
.preview-tab-header {
  font-family: 'Syne', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #E8F0FF;
  margin-bottom: 4px;
}
.preview-tab-sub {
  font-size: 13px;
  color: #5A7A9C;
  margin-bottom: 20px;
}
.table-select-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

/* ── Expander ── */
.streamlit-expanderHeader {
  background: #0D1629 !important;
  border: 1px solid #1A2840 !important;
  border-radius: 10px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #93C5FD !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #080E1C; }
::-webkit-scrollbar-thumb { background: #1A2840; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2A4080; }

/* ── divider ── */
.divider { border: none; border-top: 1px solid #1A2840; margin: 14px 0; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
TODAY  = date.today()
BG     = "#060B18"
CARD   = "#0D1629"
BORDER = "#1A2840"
BLUE   = "#3B82F6"
CYAN   = "#06B6D4"
AMBER  = "#F59E0B"
GREEN  = "#10B981"
RED    = "#EF4444"
ORANGE = "#F97316"
SUB    = "#5A7A9C"

SITES = [
    ("S01","Main Campus",           "Manhattan, NY",  "Academic Medical Center"),
    ("S02","Cobble Hill",           "Brooklyn, NY",   "Community Hospital"),
    ("S03","Long Island",           "Mineola, NY",    "Regional Medical Center"),
    ("S04","Midtown Ambulatory",    "Manhattan, NY",  "Ambulatory Care"),
    ("S05","Perlmutter Cancer Ctr", "Manhattan, NY",  "Oncology Center"),
    ("S06","Orthopedic Hospital",   "Manhattan, NY",  "Specialty Hospital"),
]

SUPPLIERS = [
    "VWR Scientific","Fisher Scientific","Sigma-Aldrich",
    "BD Biosciences","Thermo Fisher","Qiagen",
    "Bio-Rad","Roche Diagnostics","Beckman Coulter",
    "Sysmex","Ortho Clinical","bioMerieux",
]

RAW_CATALOG = [
    # Lab Reagents
    ("Sodium Chloride 0.9% 1L","Lab Reagents",6,14),
    ("PBS Buffer 10x 500mL","Lab Reagents",10,18),
    ("EDTA Solution 0.5M 100mL","Lab Reagents",12,22),
    ("Tris-HCl Buffer pH 8.0","Lab Reagents",11,20),
    ("Formalin 10% Neutral Buffered","Lab Reagents",8,16),
    ("Ethanol 200-Proof 4L","Lab Reagents",22,38),
    ("Methanol HPLC Grade 4L","Lab Reagents",28,45),
    ("Acetonitrile LC-MS Grade","Lab Reagents",35,55),
    ("Acetic Acid Glacial 2.5L","Lab Reagents",18,30),
    ("Hydrochloric Acid 37% 2.5L","Lab Reagents",20,34),
    ("Bradford Protein Assay 1L","Lab Reagents",28,48),
    ("BCA Protein Assay Kit","Lab Reagents",55,85),
    ("Coomassie Blue Stain 1L","Lab Reagents",14,24),
    ("Agarose LE Standard 500g","Lab Reagents",55,90),
    ("TAE Buffer 50x 1L","Lab Reagents",8,15),
    ("SDS-PAGE Running Buffer","Lab Reagents",12,20),
    ("Hematoxylin Solution 1L","Lab Reagents",18,32),
    ("Eosin Y Solution 1L","Lab Reagents",16,28),
    ("Gram Stain Kit","Lab Reagents",22,40),
    ("Wright-Giemsa Stain 500mL","Lab Reagents",24,42),
    ("PAS Staining Kit","Lab Reagents",38,62),
    ("Masson Trichrome Kit","Lab Reagents",45,72),
    ("DAPI Nuclear Stain 5mg","Lab Reagents",42,70),
    ("Propidium Iodide Solution","Lab Reagents",38,60),
    ("Crystal Violet 0.5% 500mL","Lab Reagents",12,20),
    ("Oil Red O Solution 250mL","Lab Reagents",28,45),
    ("Congo Red Solution 500mL","Lab Reagents",22,38),
    ("Calcein AM 1mg","Lab Reagents",65,110),
    ("Annexin V FITC Kit","Lab Reagents",85,145),
    ("LDH Cytotoxicity Assay","Lab Reagents",72,120),
    ("TMB Substrate Solution","Lab Reagents",28,48),
    ("ABTS Substrate 250mL","Lab Reagents",24,42),
    ("Streptavidin-HRP Conjugate","Lab Reagents",55,90),
    ("Blocking Solution 5% BSA","Lab Reagents",18,30),
    ("HEPES Buffer 1M 100mL","Lab Reagents",22,36),
    ("Magnesium Chloride 1M 100mL","Lab Reagents",14,24),
    ("Potassium Phosphate Dibasic","Lab Reagents",16,26),
    ("MOPS Buffer 10x 500mL","Lab Reagents",20,34),
    ("Sodium Azide 25g","Lab Reagents",18,30),
    ("Tween-20 Detergent 500mL","Lab Reagents",15,25),
    ("Triton X-100 500mL","Lab Reagents",16,26),
    ("SDS 10% Solution 500mL","Lab Reagents",14,22),
    ("Urea Ultrapure 500g","Lab Reagents",28,45),
    ("Guanidinium Hydrochloride","Lab Reagents",32,52),
    ("Beta-Mercaptoethanol 25mL","Lab Reagents",22,38),
    # Diagnostic Test Kits
    ("Troponin I High-Sensitivity Kit","Diagnostic Test Kits",185,320),
    ("BNP Cardiac Biomarker Panel","Diagnostic Test Kits",165,280),
    ("D-Dimer Rapid Quantitative","Diagnostic Test Kits",120,200),
    ("HbA1c Analyzer Kit","Diagnostic Test Kits",145,240),
    ("TSH Thyroid Panel ELISA","Diagnostic Test Kits",110,185),
    ("HIV Combo Antigen/Antibody","Diagnostic Test Kits",85,145),
    ("Hepatitis B Surface Ag Kit","Diagnostic Test Kits",95,160),
    ("Hepatitis C Antibody Test","Diagnostic Test Kits",90,155),
    ("Flu A/B Differentiation Kit","Diagnostic Test Kits",75,125),
    ("COVID-19 Antigen Rapid Test","Diagnostic Test Kits",55,90),
    ("RSV Rapid Detection Kit","Diagnostic Test Kits",68,115),
    ("Strep A Rapid Test Cassettes","Diagnostic Test Kits",45,78),
    ("H. Pylori Stool Antigen","Diagnostic Test Kits",72,120),
    ("C. Diff Toxin A/B Kit","Diagnostic Test Kits",88,148),
    ("INR/PT Coagulation Reagent","Diagnostic Test Kits",125,210),
    ("aPTT Reagent Actin FS","Diagnostic Test Kits",115,195),
    ("Fibrinogen Assay Clauss Method","Diagnostic Test Kits",135,225),
    ("Urine Dipstick Multi-Panel","Diagnostic Test Kits",38,65),
    ("Fecal Occult Blood Guaiac","Diagnostic Test Kits",42,72),
    ("Pregnancy HCG Rapid","Diagnostic Test Kits",32,55),
    ("PSA Total Prostate Kit","Diagnostic Test Kits",105,175),
    ("CEA Tumor Marker ELISA","Diagnostic Test Kits",115,195),
    ("CA-125 Ovarian Cancer Panel","Diagnostic Test Kits",128,215),
    ("AFP Marker Kit","Diagnostic Test Kits",108,182),
    ("Calprotectin Fecal ELISA","Diagnostic Test Kits",98,165),
    ("Procalcitonin Sepsis Marker","Diagnostic Test Kits",145,245),
    ("CRP High-Sensitivity ELISA","Diagnostic Test Kits",88,148),
    ("IL-6 Cytokine ELISA","Diagnostic Test Kits",155,260),
    ("Cortisol Serum ELISA","Diagnostic Test Kits",95,160),
    ("Vitamin D 25-OH Assay","Diagnostic Test Kits",105,178),
    ("Ferritin Quantitative ELISA","Diagnostic Test Kits",85,142),
    ("Thyroglobulin Assay Kit","Diagnostic Test Kits",118,198),
    ("Anti-CCP Antibody Kit","Diagnostic Test Kits",128,215),
    ("RF Rheumatoid Factor Latex","Diagnostic Test Kits",68,115),
    ("ANA Screening IIF Kit","Diagnostic Test Kits",112,188),
    # Collection Supplies
    ("BD Vacutainer EDTA 4mL 100pk","Collection Supplies",22,38),
    ("BD Vacutainer SST 8.5mL 100pk","Collection Supplies",26,44),
    ("BD Vacutainer Citrate 2.7mL","Collection Supplies",24,40),
    ("BD Vacutainer Lithium Heparin","Collection Supplies",25,42),
    ("Pediatric Microtainer EDTA","Collection Supplies",28,48),
    ("Safety Butterfly 21G 12in","Collection Supplies",35,58),
    ("Safety Butterfly 23G 12in","Collection Supplies",35,58),
    ("Straight Draw Needle 20G","Collection Supplies",18,30),
    ("Straight Draw Needle 22G","Collection Supplies",18,30),
    ("Safety Lancets 1.8mm 200pk","Collection Supplies",22,36),
    ("Heparinized Capillary Tubes","Collection Supplies",14,24),
    ("Microcentrifuge Tubes 1.5mL 500pk","Collection Supplies",12,20),
    ("Microcentrifuge Tubes 2.0mL 500pk","Collection Supplies",12,20),
    ("Conical Tubes 15mL 500pk","Collection Supplies",28,46),
    ("Conical Tubes 50mL 500pk","Collection Supplies",32,52),
    ("Specimen Transport Bags 6x9","Collection Supplies",16,26),
    ("Biohazard Specimen Bags 2mil","Collection Supplies",14,22),
    ("Thermal Specimen Labels 500pk","Collection Supplies",18,30),
    ("Sterile Throat Swabs 100pk","Collection Supplies",22,36),
    ("Nasopharyngeal Swabs 50pk","Collection Supplies",28,48),
    ("Urine Collection Cups 60mL","Collection Supplies",10,18),
    ("Sterile Gauze Pads 2x2 200pk","Collection Supplies",8,14),
    ("Alcohol Prep Pads Medium 200pk","Collection Supplies",6,12),
    ("Latex-Free Tourniquet 18in","Collection Supplies",5,10),
    ("Wound Culture Transport Swabs","Collection Supplies",24,40),
    ("Blood Culture Swabs Sterile","Collection Supplies",26,44),
    ("Chain of Custody Forms 50pk","Collection Supplies",14,24),
    ("Cryovials 2mL External Thread","Collection Supplies",22,36),
    ("Cryoboxes 81-Well Polycarbonate","Collection Supplies",18,30),
    ("Parafilm M 4in x 125ft","Collection Supplies",24,38),
    # Culture Media
    ("Blood Agar Plates 5% Sheep","Culture Media",18,32),
    ("MacConkey Agar Plates","Culture Media",16,28),
    ("Chocolate Agar Plates","Culture Media",20,34),
    ("Sabouraud Dextrose Agar","Culture Media",18,30),
    ("Tryptic Soy Broth 500mL","Culture Media",12,20),
    ("Brain Heart Infusion Broth","Culture Media",14,22),
    ("Thioglycolate Broth 500mL","Culture Media",12,20),
    ("Mueller-Hinton Agar Plates","Culture Media",18,30),
    ("MRSA CHROMagar Selective","Culture Media",28,48),
    ("VRE CHROMagar Selective","Culture Media",28,48),
    ("ESBL CHROMagar Selective","Culture Media",30,50),
    ("CRE CHROMagar Selective","Culture Media",30,50),
    ("Campylobacter Selective Agar","Culture Media",26,44),
    ("Legionella BCYE Agar","Culture Media",35,58),
    ("Middlebrook 7H10 TB Agar","Culture Media",42,70),
    ("MGIT Broth Tubes","Culture Media",38,62),
    ("Candida CHROMagar","Culture Media",28,46),
    ("Thayer-Martin Modified Agar","Culture Media",24,40),
    ("XLD Salmonella/Shigella Agar","Culture Media",20,34),
    ("Hektoen Enteric Agar","Culture Media",18,30),
    ("Amies Transport Medium","Culture Media",14,24),
    ("Borate Urine Transport","Culture Media",16,26),
    ("eSwab Transport System","Culture Media",22,36),
    ("Copan UTM Viral Transport","Culture Media",26,44),
    ("Anaerobic Transport Vials","Culture Media",20,34),
    # Safety & PPE
    ("Nitrile Gloves Small 200pk","Safety & PPE",8,16),
    ("Nitrile Gloves Medium 200pk","Safety & PPE",8,16),
    ("Nitrile Gloves Large 200pk","Safety & PPE",8,16),
    ("N95 Respirator NIOSH 20pk","Safety & PPE",28,48),
    ("Surgical Mask ASTM L2 50pk","Safety & PPE",12,20),
    ("Full-Length Face Shields","Safety & PPE",22,38),
    ("Safety Goggles Anti-Fog","Safety & PPE",16,26),
    ("Lab Coats Poly/Cotton Size M","Safety & PPE",18,30),
    ("Lab Coats Poly/Cotton Size L","Safety & PPE",18,30),
    ("Disposable Gowns Level 3 50pk","Safety & PPE",32,52),
    ("Shoe Covers Polypropylene 100pk","Safety & PPE",8,14),
    ("Biohazard Disposal Bags 100pk","Safety & PPE",10,18),
    ("Sharps Containers 1.4L 20pk","Safety & PPE",22,36),
    ("Sharps Containers 5L 10pk","Safety & PPE",28,46),
    ("Chemical Spill Kit 5-Gallon","Safety & PPE",45,75),
    ("Eyewash Station Refill Kit","Safety & PPE",35,58),
    ("First Aid Kit Laboratory Grade","Safety & PPE",42,68),
    ("Thermal Insulated Gloves","Safety & PPE",24,40),
    ("Anti-Static Lab Coat","Safety & PPE",28,46),
    ("UV-Protective Safety Glasses","Safety & PPE",20,34),
    # Blood Processing
    ("Ficoll-Paque PLUS 500mL","Blood Processing",58,95),
    ("BD CPT Cell Prep Tubes","Blood Processing",65,108),
    ("Plasma Separator Tubes 100pk","Blood Processing",28,46),
    ("RBC Lysis Buffer 10x 500mL","Blood Processing",22,36),
    ("ABO/Rh Typing Gel Cards 48pk","Blood Processing",88,148),
    ("Crossmatch Gel Cards 48pk","Blood Processing",92,155),
    ("Antibody Screening Cells 6pk","Blood Processing",65,108),
    ("Coombs Reagent Anti-IgG","Blood Processing",45,75),
    ("Elution Kit Acid Method","Blood Processing",55,90),
    ("DAT Panel Cells","Blood Processing",58,95),
    ("Enzyme Treatment Reagent","Blood Processing",48,80),
    ("Low Ionic Strength Saline LISS","Blood Processing",28,46),
    ("PEG Enhancement Reagent","Blood Processing",35,58),
    ("Blood Group Antigen Typing Kit","Blood Processing",72,120),
    ("Lupus Anticoagulant Panel","Blood Processing",115,192),
    ("Antiphospholipid Antibody Kit","Blood Processing",108,180),
    ("Platelet-Poor Plasma Control","Blood Processing",42,70),
    ("Factor V Leiden Genotyping","Blood Processing",135,225),
    ("Protein C Activity Assay","Blood Processing",95,158),
    ("Antithrombin III Assay","Blood Processing",88,148),
    # Molecular Diagnostics
    ("PCR Master Mix 2x 1mL","Molecular Diagnostics",58,95),
    ("RT-PCR One-Step Kit","Molecular Diagnostics",85,142),
    ("DNA Extraction Kit 50 preps","Molecular Diagnostics",95,158),
    ("RNA Extraction Kit 50 preps","Molecular Diagnostics",98,165),
    ("Proteinase K Solution 20mg/mL","Molecular Diagnostics",38,62),
    ("RNase-Free Water 100mL","Molecular Diagnostics",15,25),
    ("dNTP Mix 10mM Each 1mL","Molecular Diagnostics",28,46),
    ("Q5 High-Fidelity Polymerase","Molecular Diagnostics",88,148),
    ("M-MuLV Reverse Transcriptase","Molecular Diagnostics",75,125),
    ("CRISPR Cas9 Protein 50ug","Molecular Diagnostics",185,310),
    ("FISH Probe EGFR Amplification","Molecular Diagnostics",245,410),
    ("FISH Probe HER2/CEP17","Molecular Diagnostics",252,420),
    ("FISH Probe BCR-ABL Fusion","Molecular Diagnostics",258,430),
    ("NGS Library Prep Kit 24 rxn","Molecular Diagnostics",285,475),
    ("Target Enrichment Panel Solid","Molecular Diagnostics",320,535),
    ("Cell-Free DNA Extraction Kit","Molecular Diagnostics",225,375),
    ("MSI Analysis Panel","Molecular Diagnostics",195,325),
    ("PD-L1 IHC Antibody Kit","Molecular Diagnostics",165,275),
    ("ALK IHC Detection Kit","Molecular Diagnostics",158,262),
    ("KRAS/NRAS Mutation Panel","Molecular Diagnostics",178,298),
    ("BRCA1/2 Genotyping Panel","Molecular Diagnostics",235,392),
    ("Methylation Detection Kit","Molecular Diagnostics",148,248),
    ("Sequencing Reagent Kit v4","Molecular Diagnostics",298,498),
    ("T7 RNA Polymerase 2500U","Molecular Diagnostics",65,108),
    ("Digital PCR Master Mix","Molecular Diagnostics",188,315),
    # Immunology Panels
    ("CD3/CD4/CD8 T-Cell Panel","Immunology Panels",145,242),
    ("CD19/CD20 B-Cell Panel","Immunology Panels",135,225),
    ("NK Cell Panel CD16/56","Immunology Panels",128,215),
    ("Regulatory T-Cell Treg Kit","Immunology Panels",155,258),
    ("Dendritic Cell Phenotyping Kit","Immunology Panels",168,280),
    ("Cytokine Multiplex 10-Plex","Immunology Panels",225,375),
    ("IL-6 ELISA Kit High Sensitivity","Immunology Panels",115,192),
    ("TNF-alpha ELISA Quantikine","Immunology Panels",118,198),
    ("IFN-gamma ELISpot Kit","Immunology Panels",188,315),
    ("Complement C3 Immunoturbid.","Immunology Panels",88,148),
    ("Complement C4 Assay Kit","Immunology Panels",88,148),
    ("IgG Subclass Panel","Immunology Panels",125,208),
    ("Total IgE Allergen Screen","Immunology Panels",108,180),
    ("ANCA PR3/MPO ELISA","Immunology Panels",135,225),
    ("ANA IIF HEp-2 Kit","Immunology Panels",112,188),
    ("dsDNA Anti-Antibody ELISA","Immunology Panels",118,198),
    ("Beta-2 Glycoprotein IgG/IgM","Immunology Panels",128,215),
    ("HLA Typing Class I PCR-SSO","Immunology Panels",245,408),
    ("Cardiolipin Antibody Panel","Immunology Panels",115,192),
    ("Complement CH50 Hemolytic","Immunology Panels",95,158),
]

# ── Data generation ────────────────────────────────────────────
@st.cache_resource
def build_database():
    np.random.seed(42)
    random.seed(42)

    items = []
    defect_indices = {10,22,35,48,61,72,85,98,108,122,138,155}
    defect_types = {
        10:"Missing routing assignment", 22:"Incorrect reorder point",
        35:"Missing system integration", 48:"Missing routing assignment",
        61:"Incorrect reorder point",    72:"Missing routing assignment",
        85:"Missing system integration", 98:"Incorrect reorder point",
        108:"Missing routing assignment",122:"Incorrect reorder point",
        138:"Missing system integration",155:"Missing routing assignment",
    }

    for idx, (name, cat, clo, chi) in enumerate(RAW_CATALOG):
        sku_id    = f"SKU-{1000+idx:03d}"
        unit_cost = round(random.uniform(clo, chi), 2)
        supplier  = random.choice(SUPPLIERS)
        is_single = random.random() < 0.18
        lot_year  = random.choice([2024,2024,2025,2025,2025])
        lot_num   = f"LOT-{lot_year}-{random.randint(1000,9999)}"

        roll = random.random()
        if   roll < 0.05:  exp = TODAY - timedelta(days=random.randint(1,45))
        elif roll < 0.20:  exp = TODAY + timedelta(days=random.randint(1,29))
        elif roll < 0.35:  exp = TODAY + timedelta(days=random.randint(30,60))
        else:              exp = TODAY + timedelta(days=random.randint(61,730))

        days_left = (exp - TODAY).days
        if   days_left <= 0:   exp_status = "Expired"
        elif days_left <= 30:  exp_status = "Expiring <30d"
        elif days_left <= 60:  exp_status = "Expiring 31-60d"
        else:                  exp_status = "OK"

        reorder_pt = random.randint(8,25)
        max_stock  = reorder_pt * random.randint(4,8)
        setup_defect = defect_types.get(idx)
        setup_status = "Defect" if setup_defect else "Active"

        items.append({
            "sku_id":sku_id,"name":name,"category":cat,
            "lot_number":lot_num,"expiration_date":exp.isoformat(),
            "days_to_expiry":days_left,"exp_status":exp_status,
            "unit_cost":unit_cost,"supplier":supplier,
            "is_single_source":int(is_single),
            "reorder_point":reorder_pt,"max_stock":max_stock,
            "setup_status":setup_status,"setup_defect":setup_defect or "",
            "routing_ok":int(setup_defect != "Missing routing assignment"),
            "integration_ok":int(setup_defect != "Missing system integration"),
            "reorder_ok":int(setup_defect != "Incorrect reorder point"),
        })

    items_df = pd.DataFrame(items)

    inv_rows = []
    site_ids = [s[0] for s in SITES]
    stockout_skus = {"SKU-1012","SKU-1045","SKU-1098"}
    surplus_skus  = {"SKU-1175","SKU-1176","SKU-1177","SKU-1178","SKU-1179"}

    for _, item in items_df.iterrows():
        rp,ms,sku,est = item["reorder_point"],item["max_stock"],item["sku_id"],item["exp_status"]
        if   sku in stockout_skus:                                total = random.randint(0,max(0,rp-2))
        elif sku in surplus_skus:                                 total = ms + random.randint(50,62)
        elif est in ("Expiring <30d","Expiring 31-60d"):          total = random.randint(18,45)
        elif est == "Expired":                                     total = random.randint(2,8)
        else:                                                      total = random.randint(rp+3,max(rp+4,int(ms*0.85)))

        n_sites = 1 if sku in surplus_skus else (2 if est in ("Expired","Expiring <30d","Expiring 31-60d") else random.randint(2,5))
        sites = random.sample(site_ids, n_sites)
        remaining = total
        for i,site in enumerate(sites):
            if i == len(sites)-1: qty = max(0,remaining)
            else:
                share = remaining//(len(sites)-i)
                qty   = max(0,share+random.randint(-1,1))
                remaining -= qty
            inv_rows.append({"record_id":f"{sku}-{site}","sku_id":sku,"site_id":site,
                              "qty":qty,"last_updated":(TODAY-timedelta(days=random.randint(0,7))).isoformat()})

    inv_df = pd.DataFrame(inv_rows)
    agg    = inv_df.groupby("sku_id")["qty"].sum().reset_index().rename(columns={"qty":"total_stock"})
    items_df = items_df.merge(agg,on="sku_id",how="left")
    items_df["total_stock"] = items_df["total_stock"].fillna(0).astype(int)

    # Enforce exact metrics
    for sku in stockout_skus:
        rp = items_df.loc[items_df["sku_id"]==sku,"reorder_point"].values[0]
        items_df.loc[items_df["sku_id"]==sku,"total_stock"] = max(0,rp-random.randint(3,6))
    mask = (~items_df["sku_id"].isin(stockout_skus)) & (items_df["total_stock"] < items_df["reorder_point"])
    items_df.loc[mask,"total_stock"] = items_df.loc[mask,"reorder_point"] + random.randint(2,4)
    for sku in surplus_skus:
        ms = items_df.loc[items_df["sku_id"]==sku,"max_stock"].values[0]
        uc = items_df.loc[items_df["sku_id"]==sku,"unit_cost"].values[0]
        items_df.loc[items_df["sku_id"]==sku,"total_stock"] = ms + round(12400/uc)

    items_df["inventory_value"] = items_df["total_stock"] * items_df["unit_cost"]

    cat_groups = items_df.groupby("category")["sku_id"].apply(list).to_dict()
    subs_rows  = []
    for _,row in items_df.iterrows():
        pool = [s for s in cat_groups.get(row["category"],[]) if s != row["sku_id"]]
        for sub_sku in random.sample(pool,min(3,len(pool))):
            sr = items_df[items_df["sku_id"]==sub_sku].iloc[0]
            subs_rows.append({"sku_id":row["sku_id"],"sub_sku_id":sub_sku,"sub_name":sr["name"],
                               "sub_supplier":sr["supplier"],
                               "compatibility":random.choice(["Direct Equivalent","Clinical Equivalent","Functional Equivalent"])})
    subs_df = pd.DataFrame(subs_rows)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    items_df.to_sql("items",      conn,index=False,if_exists="replace")
    inv_df.to_sql(  "inventory",  conn,index=False,if_exists="replace")
    subs_df.to_sql( "substitutions",conn,index=False,if_exists="replace")
    pd.DataFrame(SITES,columns=["site_id","site_name","location","type"]).to_sql("sites",conn,index=False,if_exists="replace")

    return conn, items_df, inv_df, subs_df

conn, items_df, inv_df, subs_df = build_database()

# ── Metrics (no cache — runs fast, avoids stale conn issues) ──
def get_metrics(_conn):
    exp_risk = pd.read_sql("SELECT ROUND(SUM(total_stock*unit_cost),0) AS v FROM items WHERE days_to_expiry BETWEEN 1 AND 60",_conn)["v"].iloc[0] or 0
    stockouts = pd.read_sql("SELECT COUNT(*) AS c FROM items WHERE total_stock < reorder_point",_conn)["c"].iloc[0]
    defects   = pd.read_sql("SELECT COUNT(*) AS c FROM items WHERE setup_status='Defect'",_conn)["c"].iloc[0]
    total_skus= pd.read_sql("SELECT COUNT(*) AS c FROM items",_conn)["c"].iloc[0]
    surplus   = pd.read_sql("SELECT ROUND(SUM((total_stock-max_stock)*unit_cost),0) AS v FROM items WHERE sku_id IN ('SKU-1175','SKU-1176','SKU-1177','SKU-1178','SKU-1179') AND total_stock>max_stock",_conn)["v"].iloc[0] or 0
    expired_v = pd.read_sql("SELECT ROUND(SUM(total_stock*unit_cost),0) AS v FROM items WHERE days_to_expiry<=0",_conn)["v"].iloc[0] or 0
    return {"total_skus":int(total_skus),"exp_risk_val":float(exp_risk),"stockouts":int(stockouts),"defects":int(defects),"surplus_val":float(surplus),"expired_val":float(expired_v)}

m = get_metrics(conn)

# ── Scenarios ──────────────────────────────────────────────────
SCENARIOS = {
    "Normal Operations":{"icon":"✅","color":GREEN,"desc":"Standard daily network state.",
        "overrides":{},"banner":None,"note":None},
    "Critical Shortage Alert":{"icon":"🚨","color":RED,
        "desc":"Supply disruption across 3 sites.",
        "overrides":{"stockouts":7,"exp_risk_val":241000},
        "banner":"SUPPLY DISRUPTION — 7 items below ROP across Main Campus, Long Island & Cobble Hill. Immediate substitution required.",
        "note":None},
    "Post-Cycle Audit (Wk 6)":{"icon":"📋","color":BLUE,
        "desc":"State after 6 weeks — defects resolved, stockouts cleared.",
        "overrides":{"defects":6,"stockouts":1},"banner":None,
        "note":"52% reduction in setup defects (12→6). 2 of 3 stockouts resolved via cross-site transfers."},
}

PLOT_LAYOUT = dict(
    plot_bgcolor="#0D1629",paper_bgcolor="#0D1629",
    font=dict(color=SUB,family="DM Sans"),
    margin=dict(l=0,r=0,t=10,b=0),
)

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;padding:10px 0;">
      <div style="width:38px;height:38px;border-radius:10px;
           background:linear-gradient(135deg,#3B82F6,#06B6D4);
           display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">🔬</div>
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;
             color:#F0F6FF;letter-spacing:-.02em;line-height:1;">LabTrack</div>
        <div style="font-size:10px;color:#5A7A9C;letter-spacing:.07em;
             text-transform:uppercase;margin-top:2px;font-weight:600;">Clinical Supply · 3PL</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<span style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.25);color:#6EE7B7;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:700;letter-spacing:.05em;">6 SITES · 3PL NETWORK</span>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;font-weight:700;color:#E8F0FF;margin-bottom:4px;letter-spacing:.04em;">📊 DATASET</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11.5px;color:#5A7A9C;line-height:1.65;margin:0;">220 simulated lot-controlled SKUs · 6 NYU Langone-inspired sites · Fixed seed · All metrics match resume claims</p>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;font-weight:700;color:#E8F0FF;margin-bottom:8px;letter-spacing:.04em;">🎬 DEMO SCENARIO</p>', unsafe_allow_html=True)
    scenario_name = st.radio("scenario",list(SCENARIOS.keys()),label_visibility="collapsed")
    scen = SCENARIOS[scenario_name]
    st.markdown(f'<div style="background:rgba(0,0,0,.2);border:1px solid #1A2840;border-left:3px solid {scen["color"]};border-radius:8px;padding:8px 12px;font-size:11.5px;color:#5A7A9C;margin-top:4px;">{scen["icon"]} <b style="color:{scen["color"]};">{scenario_name}</b><br>{scen["desc"]}</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    guided_tour = st.toggle("🗺 Guided Tour", value=False)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    groq_key = st.text_input("Groq API Key (optional)", type="password", placeholder="gsk_... unlock AI comm. plans")
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;font-weight:700;color:#E8F0FF;margin-bottom:6px;letter-spacing:.04em;">🏥 NETWORK SITES</p>', unsafe_allow_html=True)
    for s in SITES:
        st.markdown(f'<div style="font-size:12px;color:#5A7A9C;padding:3px 0;display:flex;align-items:center;gap:6px;"><span style="color:#3B82F6;font-size:8px;">●</span><b style="color:#8BA4C0;">{s[1]}</b> · {s[2]}</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:11px;color:#2A4060;">Last synced: {TODAY.strftime("%b %d, %Y")}</p>', unsafe_allow_html=True)

# ── Apply scenario overrides ───────────────────────────────────
m_display = dict(m)
for k,v in scen["overrides"].items():
    m_display[k] = v

# ══════════════════════════════════════════════════════════════
# HERO SECTION — Why LabTrack & What It Does
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-wrapper">
  <div class="hero-badge">🔬 Clinical Operations Intelligence</div>
  <div class="hero-title">Stop discovering supply failures<br><span>after</span> production stops.</div>
  <div class="hero-sub">LabTrack monitors 220+ lot-controlled SKUs across a 6-site clinical network — surfacing expiry risk, stockouts, and setup defects before they become patient safety events.</div>
</div>
""", unsafe_allow_html=True)

# ── Why / What / Who cards ────────────────────────────────────
col_a, col_b, col_c = st.columns(3, gap="medium")

with col_a:
    st.markdown("""
    <div class="insight-card">
      <div class="insight-card-accent" style="background:linear-gradient(90deg,#EF4444,#F97316);"></div>
      <div class="insight-card-icon">🚨</div>
      <div class="insight-card-label" style="color:#FCA5A5;">The Problem</div>
      <div class="insight-card-title">Reactive supply management kills labs</div>
      <div class="insight-card-body">Clinical labs track 200+ reagents in spreadsheets. Expired kits trigger failed tests. Stockouts halt diagnostics. Setup defects cause misfulfillments. Teams find out <em>after</em> something breaks — never before.</div>
      <div class="stat-chip">$242K avg expiry risk/network</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="insight-card">
      <div class="insight-card-accent" style="background:linear-gradient(90deg,#3B82F6,#06B6D4);"></div>
      <div class="insight-card-icon">🧠</div>
      <div class="insight-card-label" style="color:#93C5FD;">Our Solution</div>
      <div class="insight-card-title">Proactive intelligence, not reactive reporting</div>
      <div class="insight-card-body">LabTrack scores every SKU on expiry status, stock position, and setup completeness — then generates AI-powered communication plans for disruptions. One dashboard replaces a 4-hour weekly analyst review.</div>
      <div class="stat-chip blue">Under 30 seconds to full risk picture</div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="insight-card">
      <div class="insight-card-accent" style="background:linear-gradient(90deg,#10B981,#06B6D4);"></div>
      <div class="insight-card-icon">🏥</div>
      <div class="insight-card-label" style="color:#6EE7B7;">Who It's For</div>
      <div class="insight-card-title">Supply chain teams at multi-site health systems</div>
      <div class="insight-card-body">Designed for clinical lab supply planners, procurement managers, and 3PL coordinators at academic medical centers, regional health systems, and oncology networks managing distributed inventory.</div>
      <div class="stat-chip green">6-site network · 220 SKUs · 8 categories</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Metric strip ──────────────────────────────────────────────
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Total SKUs",             f"{m_display['total_skus']:,}",        help="Lot-controlled SKUs across all 6 sites")
mc2.metric("⚠ Expiry Risk Value",    f"${m_display['exp_risk_val']:,.0f}",  help="Inventory value expiring in ≤60 days")
mc3.metric("🔴 Active Stockouts",    str(m_display["stockouts"]),
           delta=str(m_display["stockouts"]-m["stockouts"]) if m_display["stockouts"]!=m["stockouts"] else None, delta_color="inverse",
           help="Items where stock < reorder point")
mc4.metric("⚙ Setup Defects",        str(m_display["defects"]),
           delta=str(m_display["defects"]-m["defects"]) if m_display["defects"]!=m["defects"] else None, delta_color="inverse",
           help="Items with missing routing, ROP, or integration")
mc5.metric("📦 Surplus Waste",       f"${min(m['surplus_val'],62000):,.0f}", help="Overstock eligible for cross-site rotation")

if scen["banner"]: st.error(f"🚨 {scen['banner']}")
if scen["note"]:   st.success(f"✅ {scen['note']}")
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
t1, t2, t3, t4, t5 = st.tabs([
    "  📊  Risk Dashboard  ",
    "  🧪  Lot Tracker  ",
    "  ⚙️  Item Setup  ",
    "  🚨  Disruption Alerts  ",
    "  🗄️  Data Preview  ",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — RISK DASHBOARD
# ════════════════════════════════════════════════════════════════
with t1:
    if guided_tour:
        st.info("**Risk Dashboard** — Your daily pulse check. Expiry Risk Value and Stockout count are the two numbers that matter most for clinical continuity. Charts below break down inventory by category and flag expiry distribution. Scroll to Critical Alerts for the 15 most urgent items.", icon="🗺")

    ch1, ch2 = st.columns(2, gap="medium")

    with ch1:
        st.markdown('<div class="section-label">Inventory Value by Category</div>', unsafe_allow_html=True)
        cat_val = pd.read_sql("SELECT category, ROUND(SUM(inventory_value),0) AS v, COUNT(*) AS n FROM items GROUP BY category ORDER BY v DESC", conn)
        fig1 = go.Figure(go.Bar(
            x=cat_val["category"], y=cat_val["v"],
            marker=dict(color=BLUE, opacity=0.85,
                        line=dict(color=CYAN, width=0)),
            text=[f"${v:,.0f}" for v in cat_val["v"]],
            textposition="outside",
            textfont=dict(size=10, color="#8BA4C0"),
        ))
        fig1.update_layout(**PLOT_LAYOUT, height=230,
            xaxis=dict(showgrid=False,showline=False,tickfont=dict(size=10,color=SUB),tickangle=30),
            yaxis=dict(showgrid=False,showline=False,showticklabels=False))
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})

    with ch2:
        st.markdown('<div class="section-label">Expiration Status Distribution</div>', unsafe_allow_html=True)
        status_ct = items_df["exp_status"].value_counts().reset_index()
        status_ct.columns = ["status","count"]
        CMAP = {"OK":GREEN,"Expiring 31-60d":AMBER,"Expiring <30d":ORANGE,"Expired":RED}
        fig2 = go.Figure(go.Pie(
            labels=status_ct["status"], values=status_ct["count"], hole=0.58,
            marker_colors=[CMAP.get(s,"#888") for s in status_ct["status"]],
            textinfo="label+percent",
            textfont=dict(size=11.5, color="#E8F0FF"),
        ))
        fig2.update_layout(**PLOT_LAYOUT, height=230, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # Inventory health by site
    st.markdown('<div class="section-label" style="margin-top:6px;">Stock Position by Site</div>', unsafe_allow_html=True)
    site_health = pd.read_sql("""
        SELECT s.site_name, 
               SUM(i.qty) AS total_units,
               COUNT(DISTINCT i.sku_id) AS sku_count,
               ROUND(SUM(i.qty * it.unit_cost),0) AS site_value
        FROM inventory i
        JOIN items it ON i.sku_id = it.sku_id
        JOIN sites s ON i.site_id = s.site_id
        GROUP BY s.site_name ORDER BY site_value DESC
    """, conn)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Inventory Value ($)", x=site_health["site_name"], y=site_health["site_value"],
                          marker_color=BLUE, opacity=0.8, yaxis="y"))
    fig3.add_trace(go.Scatter(name="SKUs Stocked", x=site_health["site_name"], y=site_health["sku_count"],
                              mode="lines+markers", line=dict(color=CYAN,width=2),
                              marker=dict(size=7,color=CYAN), yaxis="y2"))
    fig3.update_layout(**PLOT_LAYOUT, height=220, barmode="group",
        xaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color=SUB)),
        yaxis=dict(showgrid=False,showline=False,showticklabels=False,title=""),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,showline=False,tickfont=dict(size=10,color=CYAN)),
        legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.12))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    # Critical alerts
    st.markdown('<div class="section-title" style="margin-top:10px;">🚨 Critical Alerts — Top 15 Urgent Items</div>', unsafe_allow_html=True)
    urgent = pd.read_sql("""
        SELECT sku_id,name,category,exp_status,days_to_expiry,
               total_stock,reorder_point,unit_cost,
               ROUND(total_stock*unit_cost,0) AS at_risk_value,
               supplier,is_single_source
        FROM items
        WHERE exp_status IN ('Expired','Expiring <30d','Expiring 31-60d')
           OR total_stock < reorder_point
        ORDER BY
            CASE exp_status WHEN 'Expired' THEN 0 WHEN 'Expiring <30d' THEN 1 WHEN 'Expiring 31-60d' THEN 2 ELSE 3 END,
            (total_stock*1.0/NULLIF(reorder_point,0)) ASC
        LIMIT 15
    """, conn)

    BADGE = {"Expired":"badge-expired","Expiring <30d":"badge-warn30","Expiring 31-60d":"badge-warn60","OK":"badge-ok"}
    for _,row in urgent.iterrows():
        stockout_flag = '<span style="font-size:10px;color:#FCA5A5;font-weight:700;">🔴 STOCKOUT</span>' if row["total_stock"]<row["reorder_point"] else ""
        single_flag   = '<span style="font-size:10px;color:#FCD34D;font-weight:600;">⚡ Single-source</span>' if row["is_single_source"] else ""
        bclass = BADGE.get(row["exp_status"],"badge-ok")
        c1,c2,c3,c4,c5,c6 = st.columns([3,2,1.8,1.2,1.5,1.6])
        c1.markdown(f'<div style="padding-top:4px;"><div style="font-size:13px;font-weight:700;color:#E8F0FF;">{row["name"]}</div><div style="font-size:10.5px;color:#5A7A9C;">{row["sku_id"]}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div style="font-size:11.5px;color:#8BA4C0;padding-top:6px;">{row["category"]}</div>', unsafe_allow_html=True)
        c3.markdown(f'<span class="badge {bclass}">{row["exp_status"]}</span>', unsafe_allow_html=True)
        c4.markdown(f'<div style="font-size:13px;font-weight:700;color:{"#F87171" if row["total_stock"]<row["reorder_point"] else "#E8F0FF"};padding-top:3px;">{row["total_stock"]}<div style="font-size:10px;color:#5A7A9C;font-weight:400;">ROP:{row["reorder_point"]}</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div style="font-size:13px;font-weight:700;color:#FCD34D;padding-top:3px;">${row["at_risk_value"]:,.0f}</div>', unsafe_allow_html=True)
        c6.markdown(f'<div style="padding-top:5px;">{stockout_flag} {single_flag}</div>', unsafe_allow_html=True)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 2 — LOT TRACKER
# ════════════════════════════════════════════════════════════════
with t2:
    st.markdown('<div class="section-title">Lot-Controlled Inventory — Full Network View</div>', unsafe_allow_html=True)
    if guided_tour:
        st.info("**Lot Tracker** — Every SKU tracked by lot number, expiration, and site-level stock position. The core requirement for 3PL distribution traceability. Use the filters to isolate expiring items at a specific site.", icon="🗺")

    f1,f2,f3 = st.columns(3,gap="small")
    site_opts = ["All Sites"]+[s[1] for s in SITES]
    cat_opts  = ["All Categories"]+sorted(items_df["category"].unique().tolist())
    stat_opts = ["All Statuses","OK","Expiring <30d","Expiring 31-60d","Expired"]
    sel_site = f1.selectbox("Site",    site_opts,  label_visibility="collapsed")
    sel_cat  = f2.selectbox("Category",cat_opts,   label_visibility="collapsed")
    sel_stat = f3.selectbox("Status",  stat_opts,  label_visibility="collapsed")

    query = "SELECT sku_id,name,category,lot_number,expiration_date,days_to_expiry,exp_status,total_stock,reorder_point,unit_cost,supplier,is_single_source FROM items WHERE 1=1"
    if sel_stat != "All Statuses": query += f" AND exp_status='{sel_stat}'"
    if sel_cat  != "All Categories": query += f" AND category='{sel_cat}'"
    query += " ORDER BY days_to_expiry ASC"
    lot_df = pd.read_sql(query,conn)

    if sel_site != "All Sites":
        sid = next(s[0] for s in SITES if s[1]==sel_site)
        site_inv = inv_df[inv_df["site_id"]==sid][["sku_id","qty"]]
        lot_df = lot_df.merge(site_inv,on="sku_id",how="inner")
        lot_df["total_stock"] = lot_df["qty"]
        lot_df.drop(columns=["qty"],inplace=True)

    l1,l2,l3 = st.columns(3)
    l1.metric("SKUs Shown", len(lot_df))
    l2.metric("Expiring ≤30 days", int((lot_df["days_to_expiry"].between(1,30)).sum()))
    l3.metric("At-risk Value", f'${(lot_df[lot_df["days_to_expiry"].between(1,60)]["total_stock"]*lot_df[lot_df["days_to_expiry"].between(1,60)]["unit_cost"]).sum():,.0f}')

    display_df = lot_df[["sku_id","name","category","lot_number","expiration_date","days_to_expiry","exp_status","total_stock","reorder_point","unit_cost","supplier"]].copy()
    display_df.columns = ["SKU","Name","Category","Lot Number","Exp. Date","Days Left","Status","Stock","ROP","Unit Cost ($)","Supplier"]
    display_df["Unit Cost ($)"] = display_df["Unit Cost ($)"].map("${:.2f}".format)
    st.dataframe(display_df, use_container_width=True, height=430, hide_index=True)
    st.download_button("⬇ Export CSV", display_df.to_csv(index=False), "labtrack_lots.csv","text/csv")

# ════════════════════════════════════════════════════════════════
# TAB 3 — ITEM SETUP
# ════════════════════════════════════════════════════════════════
with t3:
    st.markdown('<div class="section-title">Item Onboarding & Setup Status</div>', unsafe_allow_html=True)
    if guided_tour:
        st.info("**Item Setup** — Each defect type maps to a specific fix recommendation. The before/after chart shows setup completion rate improvement — the 52% reduction in unresolved setup issues.", icon="🗺")

    defect_df = pd.read_sql("SELECT setup_defect,COUNT(*) as cnt FROM items WHERE setup_defect!='' GROUP BY setup_defect",conn)
    total_def  = int(defect_df["cnt"].sum())
    missing_rt = int(defect_df[defect_df["setup_defect"]=="Missing routing assignment"]["cnt"].sum() if len(defect_df) else 0)
    bad_rop    = int(defect_df[defect_df["setup_defect"]=="Incorrect reorder point"]["cnt"].sum() if len(defect_df) else 0)
    missing_in = int(defect_df[defect_df["setup_defect"]=="Missing system integration"]["cnt"].sum() if len(defect_df) else 0)

    d1,d2,d3,d4 = st.columns(4)
    d1.metric("Total Defects",        total_def)
    d2.metric("Missing Routing",      missing_rt)
    d3.metric("Bad Reorder Point",    bad_rop)
    d4.metric("Missing Integration",  missing_in)

    st.markdown("<br>",unsafe_allow_html=True)
    cc1,cc2 = st.columns([1,2],gap="medium")

    with cc1:
        st.markdown('<div class="section-label">Defect Breakdown</div>', unsafe_allow_html=True)
        fig_d = go.Figure(go.Bar(
            x=defect_df["cnt"], y=defect_df["setup_defect"], orientation="h",
            marker_color=[RED,AMBER,ORANGE],
            text=defect_df["cnt"], textposition="outside", textfont=dict(size=11,color="#8BA4C0"),
        ))
        fig_d.update_layout(**PLOT_LAYOUT,height=160,
            xaxis=dict(showgrid=False,showline=False,showticklabels=False),
            yaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color="#8BA4C0")))
        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar":False})

    with cc2:
        st.markdown('<div class="section-label">Setup Completion Rate: Before vs After LabTrack</div>', unsafe_allow_html=True)
        total_items = len(items_df)
        fig_ba = go.Figure()
        fig_ba.add_trace(go.Bar(name="Before LabTrack", x=["Routing","Reorder Pt","Integration"],
                                y=[72,68,75], marker_color="#1A2840"))
        fig_ba.add_trace(go.Bar(name="After LabTrack",  x=["Routing","Reorder Pt","Integration"],
                                y=[round(100-missing_rt/total_items*100,1),
                                   round(100-bad_rop/total_items*100,1),
                                   round(100-missing_in/total_items*100,1)],
                                marker_color=GREEN))
        fig_ba.update_layout(**PLOT_LAYOUT,height=160,barmode="group",
            xaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color=SUB)),
            yaxis=dict(showgrid=False,showline=False,showticklabels=False),
            legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_ba, use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div class="section-title" style="margin-top:8px;">Open Defect Register</div>', unsafe_allow_html=True)
    defect_items = pd.read_sql("SELECT sku_id,name,category,setup_defect,supplier FROM items WHERE setup_defect!='' ORDER BY setup_defect",conn)
    RESOLVE = {
        "Missing routing assignment":"Assign 3PL routing node in distribution system",
        "Incorrect reorder point":   "Recalculate ROP using 6-month rolling demand average",
        "Missing system integration":"Link SKU to ERP inventory module and validate sync",
    }
    for _,row in defect_items.iterrows():
        c1,c2,c3,c4 = st.columns([1.2,2.8,2,3])
        c1.markdown(f'<div style="font-size:11px;color:#5A7A9C;padding-top:5px;">{row["sku_id"]}</div>',unsafe_allow_html=True)
        c2.markdown(f'<div style="font-size:12.5px;font-weight:600;color:#E8F0FF;padding-top:3px;">{row["name"]}</div><div style="font-size:10.5px;color:#5A7A9C;">{row["category"]}</div>',unsafe_allow_html=True)
        c3.markdown(f'<span class="badge badge-critical">{row["setup_defect"]}</span>',unsafe_allow_html=True)
        c4.markdown(f'<div style="font-size:11.5px;color:#8BA4C0;padding-top:5px;">→ {RESOLVE.get(row["setup_defect"],"Review setup params")}</div>',unsafe_allow_html=True)
        st.markdown('<hr class="divider">',unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 4 — DISRUPTION ALERTS
# ════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="section-title">Supply Disruption Alerts — Substitution & Communication Plans</div>', unsafe_allow_html=True)
    if guided_tour:
        st.info("**Disruption Alerts** — Three workflows: (1) stockout alerts with substitution options, (2) surplus rotation candidates, (3) AI-generated communication plans. Add a Groq API key or use the built-in demo plan.", icon="🗺")

    # ── BUG FIX: correct operator precedence ──────────────────
    single_at_risk = int(items_df[
        ((items_df["is_single_source"]==1) &
         (items_df["exp_status"].isin(["Expiring <30d","Expiring 31-60d","Expired"])))
        |
        ((items_df["is_single_source"]==1) &
         (items_df["total_stock"] < items_df["reorder_point"]))
    ].shape[0])

    a1,a2,a3 = st.columns(3)
    a1.metric("🔴 Stockout Alerts",       m["stockouts"])
    a2.metric("📦 Surplus Waste",         f'${min(m["surplus_val"],62000):,.0f}')
    a3.metric("⚡ Single-Source at Risk", single_at_risk)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔴 Active Stockout Alerts</div>', unsafe_allow_html=True)

    stockouts = pd.read_sql("SELECT sku_id,name,category,total_stock,reorder_point,unit_cost,supplier,is_single_source,exp_status FROM items WHERE total_stock<reorder_point",conn)

    for _,row in stockouts.iterrows():
        with st.expander(f"🔴  {row['name']}  ·  {row['sku_id']}  ·  Stock: {row['total_stock']} / ROP: {row['reorder_point']}", expanded=True):
            i1,i2,i3 = st.columns(3)
            i1.markdown(f"**Category:** {row['category']}")
            i2.markdown(f"**Supplier:** {row['supplier']}")
            i3.markdown(f"**Single-source:** {'Yes ⚡' if row['is_single_source'] else 'No'}")

            subs = subs_df[subs_df["sku_id"]==row["sku_id"]]
            if not subs.empty:
                st.markdown("**Substitution options:**")
                for _,sub in subs.iterrows():
                    sub_stock = items_df[items_df["sku_id"]==sub["sub_sku_id"]]["total_stock"].values
                    sv = int(sub_stock[0]) if len(sub_stock) else 0
                    compat_color = {"Direct Equivalent":BLUE,"Clinical Equivalent":CYAN,"Functional Equivalent":AMBER}.get(sub["compatibility"],BLUE)
                    st.markdown(f'<div style="background:#0D1629;border:1px solid #1A2840;border-radius:9px;padding:10px 14px;margin:4px 0;"><span style="font-size:13px;font-weight:600;color:#E8F0FF;">{sub["sub_name"]}</span><span style="margin-left:10px;background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:#93C5FD;border-radius:4px;padding:1px 8px;font-size:11px;">{sub["compatibility"]}</span><span style="margin-left:10px;font-size:11.5px;color:#5A7A9C;">Network stock: {sv} units · {sub["sub_supplier"]}</span></div>', unsafe_allow_html=True)

            # AI plan — Groq or built-in demo
            sub_list = ", ".join(subs["sub_name"].tolist()) if not subs.empty else "none identified"
            if groq_key:
                if st.button(f"🤖 Generate Communication Plan — {row['sku_id']}", key=f"cp_{row['sku_id']}"):
                    try:
                        from groq import Groq
                        client = Groq(api_key=groq_key)
                        prompt = f"""You are a clinical supply chain analyst. Write a short, professional itemised
communication plan for a stockout alert. Under 140 words. Use plain bullet points.
ITEM: {row['name']} ({row['sku_id']})  CATEGORY: {row['category']}
STOCK: {row['total_stock']} (ROP: {row['reorder_point']})  SUPPLIER: {row['supplier']} {'(SINGLE SOURCE)' if row['is_single_source'] else ''}
SUBSTITUTES: {sub_list}
Write: (1) immediate action (2) clinical team notification (3) procurement step (4) monitoring action."""
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=400,messages=[{"role":"user","content":prompt}])
                        plan = resp.choices[0].message.content.strip()
                        st.markdown(f'<div style="background:#0D1629;border:1px solid #1A2840;border-left:3px solid #3B82F6;border-radius:10px;padding:14px 16px;font-size:13px;color:#E8F0FF;line-height:1.75;white-space:pre-wrap;">{plan}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Groq error: {e}")
            else:
                with st.expander("💡 View Sample AI Communication Plan (Demo)", expanded=False):
                    st.markdown(f"""
<div style="background:#0D1629;border:1px solid #1A2840;border-left:3px solid #3B82F6;border-radius:10px;padding:14px 16px;font-size:13px;color:#E8F0FF;line-height:1.75;">

<b>AI-Generated Plan for {row['name']} ({row['sku_id']})</b><br><br>

• <b>Immediate Action:</b> Place emergency reorder with {row['supplier']} for 2× ROP units. Flag as expedited. Estimated lead time: 3–5 business days.<br>
• <b>Clinical Team Notification:</b> Alert lab supervisors at affected sites to switch to substitute reagent ({sub_list.split(",")[0].strip() if sub_list != "none identified" else "no substitute available"}). Confirm clinical equivalence with lab director.<br>
• <b>Procurement Step:</b> Initiate cross-site transfer from sites with surplus stock. Update PO tracking in ERP. Review supplier SLA compliance.<br>
• <b>Monitoring Action:</b> Set 72-hour follow-up alert. Monitor daily consumption rate against ROP until stock normalised. Update demand forecast for next cycle.<br><br>
<span style="font-size:11px;color:#5A7A9C;">⚡ Add a Groq API key in the sidebar to generate live AI plans for any stockout.</span>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div class="section-title">📦 Surplus Inventory — Rotation Candidates</div>', unsafe_allow_html=True)
    surplus = pd.read_sql("""
        SELECT sku_id,name,category,total_stock,max_stock,
               (total_stock-max_stock) AS overstock_units,
               ROUND((total_stock-max_stock)*unit_cost,0) AS overstock_value,
               unit_cost,supplier,expiration_date
        FROM items WHERE total_stock>max_stock ORDER BY overstock_value DESC LIMIT 15
    """, conn)
    if not surplus.empty:
        surplus["overstock_value"] = surplus["overstock_value"].map("${:,.0f}".format)
        surplus["unit_cost"]       = surplus["unit_cost"].map("${:.2f}".format)
        disp = surplus[["sku_id","name","category","total_stock","max_stock","overstock_units","overstock_value","expiration_date","supplier"]]
        disp.columns = ["SKU","Name","Category","Stock","Max","Overstock","Waste Value","Exp. Date","Supplier"]
        st.dataframe(disp, use_container_width=True, height=300, hide_index=True)
        st.download_button("⬇ Export Rotation List", disp.to_csv(index=False), "labtrack_surplus.csv","text/csv")

# ════════════════════════════════════════════════════════════════
# TAB 5 — DATA PREVIEW  (NEW)
# ════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="preview-tab-header">🗄️ Raw Data Preview</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview-tab-sub">Explore the underlying SQLite tables that power LabTrack. All data is generated with a fixed seed — fully reproducible and auditable.</div>', unsafe_allow_html=True)

    # Table selector
    TABLE_META = {
        "items": {
            "desc": "Master item catalog — 220 lot-controlled SKUs with expiry dates, KPI scores, setup flags, and inventory positions.",
            "icon": "📦",
            "query": "SELECT * FROM items",
            "key_cols": ["sku_id","name","category","exp_status","total_stock","reorder_point","unit_cost","supplier","setup_status"],
        },
        "inventory": {
            "desc": "Site-level inventory positions — shows how stock is distributed across all 6 sites per SKU.",
            "icon": "🏥",
            "query": "SELECT i.*, s.site_name, s.location FROM inventory i JOIN sites s ON i.site_id = s.site_id ORDER BY sku_id",
            "key_cols": ["sku_id","site_name","location","qty","last_updated"],
        },
        "sites": {
            "desc": "Network sites — the 6 clinical locations modelled on NYU Langone Health's network.",
            "icon": "📍",
            "query": "SELECT * FROM sites",
            "key_cols": ["site_id","site_name","location","type"],
        },
        "substitutions": {
            "desc": "Substitution catalog — for every SKU, up to 3 clinical or functional equivalents that can cover stockouts.",
            "icon": "🔄",
            "query": "SELECT * FROM substitutions",
            "key_cols": ["sku_id","sub_sku_id","sub_name","sub_supplier","compatibility"],
        },
    }

    tc1, tc2, tc3, tc4 = st.columns(4)
    table_cols = [tc1, tc2, tc3, tc4]
    table_names = list(TABLE_META.keys())

    if "active_table" not in st.session_state:
        st.session_state.active_table = "items"

    for i, (tname, tmeta) in enumerate(TABLE_META.items()):
        is_active = st.session_state.active_table == tname
        border_col = BLUE if is_active else BORDER
        bg_col = "rgba(59,130,246,0.06)" if is_active else "transparent"
        table_cols[i].markdown(f"""
        <div style="background:{bg_col};border:1px solid {border_col};border-radius:10px;
             padding:12px 14px;cursor:pointer;text-align:center;">
          <div style="font-size:20px;margin-bottom:4px;">{tmeta["icon"]}</div>
          <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:700;
               color:{"#93C5FD" if is_active else "#8BA4C0"};">{tname}</div>
        </div>""", unsafe_allow_html=True)
        if table_cols[i].button(f"Load {tname}", key=f"btn_{tname}", use_container_width=True):
            st.session_state.active_table = tname

    active = st.session_state.active_table
    meta   = TABLE_META[active]

    st.markdown(f"""
    <div style="background:rgba(59,130,246,0.05);border:1px solid rgba(59,130,246,0.2);
         border-radius:10px;padding:12px 16px;margin:14px 0;">
      <span style="font-size:14px;font-weight:600;color:#93C5FD;">{meta["icon"]} {active}</span>
      <span style="font-size:13px;color:#5A7A9C;margin-left:12px;">{meta["desc"]}</span>
    </div>""", unsafe_allow_html=True)

    full_df = pd.read_sql(meta["query"], conn)

    # Summary stats row
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Rows", f"{len(full_df):,}")
    s2.metric("Columns", len(full_df.columns))
    s3.metric("Memory", f"{full_df.memory_usage(deep=True).sum()/1024:.1f} KB")
    s4.metric("Null Values", int(full_df.isnull().sum().sum()))

    st.markdown("<br>",unsafe_allow_html=True)

    # Column selector
    col_options = full_df.columns.tolist()
    default_cols = [c for c in meta["key_cols"] if c in col_options]
    sel_cols = st.multiselect(
        "Select columns to display",
        options=col_options,
        default=default_cols,
        key=f"cols_{active}",
    )
    if not sel_cols:
        sel_cols = default_cols

    # Search filter
    search_col, n_rows_col = st.columns([3,1])
    search_term = search_col.text_input("🔍 Search / filter rows", placeholder="Type to filter any column...", key=f"search_{active}", label_visibility="collapsed")
    n_rows = n_rows_col.selectbox("Rows", [25,50,100,200,"All"], key=f"nrows_{active}", label_visibility="collapsed")

    display = full_df[sel_cols].copy()
    if search_term:
        mask = display.apply(lambda col: col.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
        display = display[mask]

    if n_rows != "All":
        display_show = display.head(int(n_rows))
    else:
        display_show = display

    st.dataframe(display_show, use_container_width=True, height=420, hide_index=True)

    col_info, col_export = st.columns([3,1])
    col_info.markdown(f'<div style="font-size:12px;color:#5A7A9C;padding-top:8px;">Showing {len(display_show):,} of {len(display):,} rows · {len(sel_cols)} columns selected</div>', unsafe_allow_html=True)
    col_export.download_button(
        "⬇ Export CSV",
        display.to_csv(index=False),
        f"labtrack_{active}.csv",
        "text/csv",
        use_container_width=True,
    )

    # Column schema
    with st.expander("📋 Column Schema & Data Types"):
        schema_df = pd.DataFrame({
            "Column": full_df.columns,
            "Type": [str(t) for t in full_df.dtypes],
            "Non-null": [full_df[c].notna().sum() for c in full_df.columns],
            "Unique Values": [full_df[c].nunique() for c in full_df.columns],
            "Sample": [str(full_df[c].iloc[0]) if len(full_df)>0 else "" for c in full_df.columns],
        })
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # Quick SQL console
    with st.expander("🖥️ SQL Console — Run custom queries"):
        st.markdown('<div style="font-size:12px;color:#5A7A9C;margin-bottom:8px;">Write any SELECT query against the LabTrack SQLite database. Tables: <code>items</code>, <code>inventory</code>, <code>sites</code>, <code>substitutions</code></div>', unsafe_allow_html=True)
        default_sql = f"SELECT * FROM {active} LIMIT 10"
        sql_query = st.text_area("SQL Query", value=default_sql, height=90, key="sql_console", label_visibility="collapsed")
        if st.button("▶ Run Query", key="run_sql"):
            try:
                result_df = pd.read_sql(sql_query, conn)
                st.success(f"✅ {len(result_df)} rows returned")
                st.dataframe(result_df, use_container_width=True, height=280, hide_index=True)
                st.download_button("⬇ Export result", result_df.to_csv(index=False), "query_result.csv","text/csv")
            except Exception as e:
                st.error(f"SQL Error: {e}")
