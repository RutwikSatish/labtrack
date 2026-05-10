"""
LabTrack v4.0 — Clinical Lab Supply Visibility & OR-Driven Inventory Optimization
==================================================================================
Improvement log v4.0:
  - Replaced ad-hoc fill_rate formula with mathematically correct
    Cycle Service Level: CSL = Φ(z), z = safety_stock / σ_LT
  - Fixed cold chain classification to item-level (not blanket category)
  - Removed PPAP/AIAG (automotive standard, wrong domain)
    Replaced with ISO 15189 / CLIA / CLSI (correct clinical lab standards)
  - Removed unverified "Prof. Martagan framework" claim
    Added proper academic citations throughout
  - Labeled before/after setup chart as illustrative (baselines not from
    US clinical lab benchmarks)
  - Added synthetic data disclaimer

OR Model Sources:
  - EOQ (Wilson formula): Harris, F.W. (1913). Factory, The Magazine of Management.
  - Safety Stock / CSL: Chopra & Meindl (2016). Supply Chain Management, 6th ed. Pearson.
                         Silver, Pyke & Thomas (2017). Inventory and Production Mgmt. CRC Press.
  - ROP formula:         Standard continuous-review (Q,R) policy — Silver et al. (2017) Ch.7
  - Demand forecasting:  Single exponential smoothing — Brown (1959) / Holt (1957)
  - Clinical lab application: Ahmadi et al. (2019). Inventory management of surgical supplies.
                              Health Systems 8(2):134-151.

Problem validation sources:
  - Kasahun & Kebede (2022) PMC9649967: 12.94% lab commodity waste, 58-day avg stockout
  - CLIA Interpretive Guidelines (2023): CDC Laboratory Supply Chain FAQ
  - ISO 15189:2022: Medical laboratories — Requirements for quality and competence
  - Plebani et al. (2024) PMC10784235: Supply chain role in clinical laboratories

IMPORTANT: All inventory data is synthetically generated (np.random.seed(42)).
           No real patient or operational data is used. Site names are inspired by
           a major US academic medical center network for realism; they do not
           represent actual operational data from any institution.

Author: Rutwik Satish | MS Engineering Management, Northeastern University
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import random
import math
import io

st.set_page_config(
    page_title="LabTrack · Clinical Supply Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #04080F; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2.5rem; max-width: 1440px; }
[data-testid="metric-container"] {
  background: #080F1E; border: 1px solid rgba(59,130,246,0.15); border-radius: 14px;
  padding: 1.1rem 1.3rem; position: relative; overflow: hidden;
  transition: border-color .25s, box-shadow .25s; box-shadow: 0 2px 12px rgba(0,0,0,0.4);
}
[data-testid="metric-container"]:hover { border-color: rgba(59,130,246,0.4); box-shadow: 0 4px 24px rgba(59,130,246,0.08); }
[data-testid="metric-container"]::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #3B82F6 0%, #06B6D4 50%, #8B5CF6 100%); opacity: 0.8;
}
[data-testid="metric-container"] label { font-size: 10.5px !important; text-transform: uppercase; letter-spacing: .1em; color: #4A6A8A !important; font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.9rem !important; font-weight: 700 !important; font-family: 'Syne', sans-serif !important; color: #EDF4FF !important; letter-spacing: -.02em; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid rgba(255,255,255,0.06); background: transparent; margin-bottom: 1.5rem; }
.stTabs [data-baseweb="tab"] { padding: .65rem 1.3rem; font-size: 12.5px; font-weight: 600; color: #4A6A8A; border-bottom: 2px solid transparent; font-family: 'DM Sans', sans-serif; letter-spacing: .02em; border-radius: 8px 8px 0 0; transition: color .15s, background .15s; }
.stTabs [data-baseweb="tab"]:hover { color: #93C5FD; background: rgba(59,130,246,0.04); }
.stTabs [aria-selected="true"] { color: #E8F0FF !important; border-bottom: 2px solid #3B82F6 !important; background: rgba(59,130,246,0.06) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stButton > button { font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 13px; border-radius: 9px; padding: .5rem 1.3rem; border: 1px solid rgba(59,130,246,0.25) !important; background: rgba(59,130,246,0.06) !important; color: #93C5FD !important; transition: all .2s; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.stButton > button:hover { background: rgba(59,130,246,0.14) !important; border-color: rgba(59,130,246,0.5) !important; box-shadow: 0 2px 12px rgba(59,130,246,0.15) !important; }
.stTextArea textarea, .stTextInput input, .stSelectbox > div > div { background: #060C18 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 9px !important; color: #E8F0FF !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #060C1A 0%, #040810 100%); border-right: 1px solid rgba(255,255,255,0.06); }
div[data-testid="stDataFrame"] { border: 1px solid rgba(59,130,246,0.12); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 16px rgba(0,0,0,0.3); }
.or-card { background: linear-gradient(145deg, #090F20 0%, #070C18 100%); border: 1px solid rgba(59,130,246,0.18); border-radius: 14px; padding: 1.3rem 1.4rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.or-metric { font-family: 'Syne', sans-serif; font-size: 1.7rem; font-weight: 700; color: #93C5FD; letter-spacing: -.02em; }
.or-label { font-size: 10.5px; text-transform: uppercase; letter-spacing: .08em; color: #3A5A7C; font-weight: 700; margin-bottom: 4px; }
.or-sub { font-size: 11.5px; color: #2A4060; margin-top: 3px; }
.badge { display: inline-flex; align-items: center; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 700; letter-spacing: .04em; white-space: nowrap; }
.badge-expired  { background: rgba(239,68,68,.08);   border: 1px solid rgba(239,68,68,.25);   color: #FCA5A5; }
.badge-warn30   { background: rgba(249,115,22,.08);  border: 1px solid rgba(249,115,22,.25);  color: #FDBA74; }
.badge-warn60   { background: rgba(245,158,11,.08);  border: 1px solid rgba(245,158,11,.25);  color: #FCD34D; }
.badge-ok       { background: rgba(16,185,129,.08);  border: 1px solid rgba(16,185,129,.25);  color: #6EE7B7; }
.badge-critical { background: rgba(239,68,68,.10);   border: 1px solid rgba(239,68,68,.3);    color: #F87171; }
.badge-cold     { background: rgba(6,182,212,.08);   border: 1px solid rgba(6,182,212,.25);   color: #67E8F9; }
.divider { border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 12px 0; }
.cite-note { font-size: 10.5px; color: #2A4060; font-style: italic; margin-top: 6px; }
.streamlit-expanderHeader { background: #080F1E !important; border: 1px solid rgba(59,130,246,0.15) !important; border-radius: 10px !important; font-size: 13px !important; font-weight: 600 !important; color: #93C5FD !important; }
.stDownloadButton > button { border-color: rgba(16,185,129,0.25) !important; background: rgba(16,185,129,0.05) !important; color: #6EE7B7 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #04080F; }
::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.2); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

TODAY  = date.today()
BG, CARD, BORDER = "#060B18", "#0D1629", "#1A2840"
BLUE, CYAN, AMBER, GREEN, RED, ORANGE, SUB = "#3B82F6","#06B6D4","#F59E0B","#10B981","#EF4444","#F97316","#5A7A9C"
PLOT_LAYOUT = dict(
    plot_bgcolor="#0D1629", paper_bgcolor="#0D1629",
    font=dict(color=SUB, family="DM Sans"), margin=dict(l=0,r=0,t=10,b=0)
)

SITES = [
    ("S01","Main Campus",           "Manhattan, NY",  "Academic Medical Center"),
    ("S02","Cobble Hill",           "Brooklyn, NY",   "Community Hospital"),
    ("S03","Long Island",           "Mineola, NY",    "Regional Medical Center"),
    ("S04","Midtown Ambulatory",    "Manhattan, NY",  "Ambulatory Care"),
    ("S05","Perlmutter Cancer Ctr", "Manhattan, NY",  "Oncology Center"),
    ("S06","Orthopedic Hospital",   "Manhattan, NY",  "Specialty Hospital"),
]

SUPPLIERS = [
    "VWR Scientific","Fisher Scientific","Sigma-Aldrich","BD Biosciences","Thermo Fisher",
    "Qiagen","Bio-Rad","Roche Diagnostics","Beckman Coulter","Sysmex","Ortho Clinical","bioMerieux",
]

# ── Cold chain classification at item level ───────────────────────────────────
# Source: FDA IVD storage requirements; manufacturer package inserts
# Categories where ALL items require cold chain (2-8°C or colder):
COLD_CHAIN_CATS = {"Immunology Panels", "Molecular Diagnostics", "Blood Processing"}

# Diagnostic Test Kits: item-level classification
# Cold chain (2-8°C): ELISA-based, antibody-based, enzyme-based assays
COLD_CHAIN_KITS = {
    "Troponin I High-Sensitivity Kit",   # 2-8°C per Roche/Abbott package insert
    "BNP Cardiac Biomarker Panel",       # 2-8°C
    "D-Dimer Rapid Quantitative",        # 2-8°C (quantitative ELISA-based)
    "HbA1c Analyzer Kit",               # 2-8°C for enzymatic reagents
    "TSH Thyroid Panel ELISA",           # 2-8°C
    "HIV Combo Antigen/Antibody",        # 2-8°C per WHO prequalification
    "Hepatitis B Surface Ag Kit",        # 2-8°C
    "Hepatitis C Antibody Test",         # 2-8°C
    "C. Diff Toxin A/B Kit",            # 2-8°C (EIA-based)
    "INR/PT Coagulation Reagent",        # 2-8°C
    "Procalcitonin Sepsis Marker",       # 2-8°C (ELISA)
    "CRP High-Sensitivity ELISA",        # 2-8°C
    "Vitamin D 25-OH Assay",            # 2-8°C
    "Ferritin Quantitative ELISA",       # 2-8°C
}
# Rapid lateral-flow assays: typically stable at 15-30°C (room temperature)
ROOM_TEMP_KITS = {
    "Flu A/B Differentiation Kit",       # most lateral flow: 15-30°C
    "COVID-19 Antigen Rapid Test",       # WHO EUL: 2-30°C (room temp acceptable)
    "RSV Rapid Detection Kit",           # 15-30°C
    "Strep A Rapid Test Cassettes",      # 15-30°C
}

RAW_CATALOG = [
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
    ("Agarose LE Standard 500g","Lab Reagents",55,90),
    ("TAE Buffer 50x 1L","Lab Reagents",8,15),
    ("Hematoxylin Solution 1L","Lab Reagents",18,32),
    ("Eosin Y Solution 1L","Lab Reagents",16,28),
    ("Gram Stain Kit","Lab Reagents",22,40),
    ("DAPI Nuclear Stain 5mg","Lab Reagents",42,70),
    ("Annexin V FITC Kit","Lab Reagents",85,145),
    ("LDH Cytotoxicity Assay","Lab Reagents",72,120),
    ("TMB Substrate Solution","Lab Reagents",28,48),
    ("Streptavidin-HRP Conjugate","Lab Reagents",55,90),
    ("HEPES Buffer 1M 100mL","Lab Reagents",22,36),
    ("Tween-20 Detergent 500mL","Lab Reagents",15,25),
    ("Triton X-100 500mL","Lab Reagents",16,26),
    ("SDS 10% Solution 500mL","Lab Reagents",14,22),
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
    ("C. Diff Toxin A/B Kit","Diagnostic Test Kits",88,148),
    ("INR/PT Coagulation Reagent","Diagnostic Test Kits",125,210),
    ("Procalcitonin Sepsis Marker","Diagnostic Test Kits",145,245),
    ("CRP High-Sensitivity ELISA","Diagnostic Test Kits",88,148),
    ("Vitamin D 25-OH Assay","Diagnostic Test Kits",105,178),
    ("Ferritin Quantitative ELISA","Diagnostic Test Kits",85,142),
    ("BD Vacutainer EDTA 4mL 100pk","Collection Supplies",22,38),
    ("BD Vacutainer SST 8.5mL 100pk","Collection Supplies",26,44),
    ("BD Vacutainer Citrate 2.7mL","Collection Supplies",24,40),
    ("Pediatric Microtainer EDTA","Collection Supplies",28,48),
    ("Safety Butterfly 21G 12in","Collection Supplies",35,58),
    ("Safety Butterfly 23G 12in","Collection Supplies",35,58),
    ("Safety Lancets 1.8mm 200pk","Collection Supplies",22,36),
    ("Microcentrifuge Tubes 1.5mL 500pk","Collection Supplies",12,20),
    ("Conical Tubes 15mL 500pk","Collection Supplies",28,46),
    ("Specimen Transport Bags 6x9","Collection Supplies",16,26),
    ("Sterile Throat Swabs 100pk","Collection Supplies",22,36),
    ("Nasopharyngeal Swabs 50pk","Collection Supplies",28,48),
    ("Urine Collection Cups 60mL","Collection Supplies",10,18),
    ("Alcohol Prep Pads Medium 200pk","Collection Supplies",6,12),
    ("Chain of Custody Forms 50pk","Collection Supplies",14,24),
    ("Cryovials 2mL External Thread","Collection Supplies",22,36),
    ("Blood Agar Plates 5% Sheep","Culture Media",18,32),
    ("MacConkey Agar Plates","Culture Media",16,28),
    ("Chocolate Agar Plates","Culture Media",20,34),
    ("Sabouraud Dextrose Agar","Culture Media",18,30),
    ("Tryptic Soy Broth 500mL","Culture Media",12,20),
    ("Mueller-Hinton Agar Plates","Culture Media",18,30),
    ("MRSA CHROMagar Selective","Culture Media",28,48),
    ("CRE CHROMagar Selective","Culture Media",30,50),
    ("Middlebrook 7H10 TB Agar","Culture Media",42,70),
    ("MGIT Broth Tubes","Culture Media",38,62),
    ("Candida CHROMagar","Culture Media",28,46),
    ("eSwab Transport System","Culture Media",22,36),
    ("Nitrile Gloves Small 200pk","Safety & PPE",8,16),
    ("Nitrile Gloves Medium 200pk","Safety & PPE",8,16),
    ("Nitrile Gloves Large 200pk","Safety & PPE",8,16),
    ("N95 Respirator NIOSH 20pk","Safety & PPE",28,48),
    ("Surgical Mask ASTM L2 50pk","Safety & PPE",12,20),
    ("Lab Coats Poly/Cotton Size M","Safety & PPE",18,30),
    ("Disposable Gowns Level 3 50pk","Safety & PPE",32,52),
    ("Biohazard Disposal Bags 100pk","Safety & PPE",10,18),
    ("Sharps Containers 1.4L 20pk","Safety & PPE",22,36),
    ("Chemical Spill Kit 5-Gallon","Safety & PPE",45,75),
    ("Ficoll-Paque PLUS 500mL","Blood Processing",58,95),
    ("BD CPT Cell Prep Tubes","Blood Processing",65,108),
    ("RBC Lysis Buffer 10x 500mL","Blood Processing",22,36),
    ("ABO/Rh Typing Gel Cards 48pk","Blood Processing",88,148),
    ("Crossmatch Gel Cards 48pk","Blood Processing",92,155),
    ("Antibody Screening Cells 6pk","Blood Processing",65,108),
    ("Coombs Reagent Anti-IgG","Blood Processing",45,75),
    ("Factor V Leiden Genotyping","Blood Processing",135,225),
    ("Protein C Activity Assay","Blood Processing",95,158),
    ("Antithrombin III Assay","Blood Processing",88,148),
    ("PCR Master Mix 2x 1mL","Molecular Diagnostics",58,95),
    ("RT-PCR One-Step Kit","Molecular Diagnostics",85,142),
    ("DNA Extraction Kit 50 preps","Molecular Diagnostics",95,158),
    ("RNA Extraction Kit 50 preps","Molecular Diagnostics",98,165),
    ("Q5 High-Fidelity Polymerase","Molecular Diagnostics",88,148),
    ("CRISPR Cas9 Protein 50ug","Molecular Diagnostics",185,310),
    ("FISH Probe EGFR Amplification","Molecular Diagnostics",245,410),
    ("FISH Probe HER2/CEP17","Molecular Diagnostics",252,420),
    ("NGS Library Prep Kit 24 rxn","Molecular Diagnostics",285,475),
    ("Target Enrichment Panel Solid","Molecular Diagnostics",320,535),
    ("Cell-Free DNA Extraction Kit","Molecular Diagnostics",225,375),
    ("MSI Analysis Panel","Molecular Diagnostics",195,325),
    ("PD-L1 IHC Antibody Kit","Molecular Diagnostics",165,275),
    ("KRAS/NRAS Mutation Panel","Molecular Diagnostics",178,298),
    ("BRCA1/2 Genotyping Panel","Molecular Diagnostics",235,392),
    ("Sequencing Reagent Kit v4","Molecular Diagnostics",298,498),
    ("CD3/CD4/CD8 T-Cell Panel","Immunology Panels",145,242),
    ("CD19/CD20 B-Cell Panel","Immunology Panels",135,225),
    ("NK Cell Panel CD16/56","Immunology Panels",128,215),
    ("Cytokine Multiplex 10-Plex","Immunology Panels",225,375),
    ("IL-6 ELISA Kit High Sensitivity","Immunology Panels",115,192),
    ("TNF-alpha ELISA Quantikine","Immunology Panels",118,198),
    ("IFN-gamma ELISpot Kit","Immunology Panels",188,315),
    ("Complement C3 Immunoturbid.","Immunology Panels",88,148),
    ("IgG Subclass Panel","Immunology Panels",125,208),
    ("Total IgE Allergen Screen","Immunology Panels",108,180),
    ("ANCA PR3/MPO ELISA","Immunology Panels",135,225),
    ("HLA Typing Class I PCR-SSO","Immunology Panels",245,408),
]


# ── OR Functions — all sourced ────────────────────────────────────────────────

def norm_cdf(z: float) -> float:
    """
    Standard normal cumulative distribution function.
    Uses math.erf (exact, no external dependencies).
    CDF(z) = 0.5 * (1 + erf(z / sqrt(2)))
    Source: Abramowitz & Stegun (1964) Handbook of Mathematical Functions, eq. 26.2.17
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calc_eoq(annual_demand: float, ordering_cost: float,
             holding_cost_pct: float, unit_cost: float, moq: int = 1) -> int:
    """
    Economic Order Quantity — Wilson formula.
    EOQ = sqrt(2 * D * S / H)  where H = holding_cost_pct * unit_cost

    Assumptions: constant demand, instantaneous replenishment, no shortages.
    Source: Harris, F.W. (1913). Factory, The Magazine of Management 10(2):135-136.
            Chopra & Meindl (2016). Supply Chain Management, 6th ed. Ch.11.
    """
    H = holding_cost_pct * unit_cost
    if H <= 0 or annual_demand <= 0:
        return moq
    eoq = math.sqrt((2.0 * annual_demand * ordering_cost) / H)
    return max(moq, round(eoq))


def calc_safety_stock(daily_demand_std: float, lead_time_days: float,
                      service_level: float = 0.95) -> int:
    """
    Safety stock using service-level z-score — simplified formula (constant lead time).
    SS = z * sigma_LT  where sigma_LT = daily_demand_std * sqrt(lead_time_days)

    Note: Full formula with lead time variability:
          sigma_LT = sqrt(L * sigma_d^2 + d_avg^2 * sigma_L^2)
          This implementation assumes deterministic lead time for simplicity.

    z-scores (standard normal quantiles):
        90% service level: z = 1.282
        95% service level: z = 1.645  (default)
        98% service level: z = 2.054
        99% service level: z = 2.326

    Source: Silver, Pyke & Thomas (2017). Inventory and Production Management
            in Supply Chains, 4th ed. CRC Press. Ch.7.
            Chopra & Meindl (2016). Ch.12 — Managing Uncertainty in a Supply Chain.
    """
    z_map = {0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326}
    z = z_map.get(service_level, 1.645)
    sigma_lt = daily_demand_std * math.sqrt(lead_time_days)
    return math.ceil(z * sigma_lt)


def calc_rop(avg_daily_demand: float, lead_time_days: float,
             safety_stock: int) -> int:
    """
    Reorder Point for a continuous-review (Q, R) system.
    ROP = avg_daily_demand * lead_time_days + safety_stock

    Source: Silver, Pyke & Thomas (2017) Ch.7.
            Chopra & Meindl (2016) Ch.11.
    """
    return math.ceil(avg_daily_demand * lead_time_days + safety_stock)


def calc_total_inventory_cost(annual_demand: float, order_qty: int,
                               ordering_cost: float, holding_cost_pct: float,
                               unit_cost: float) -> float:
    """
    Total annual inventory cost = ordering cost + holding cost + purchase cost.
    TC = (D/Q)*S + (Q/2)*H + D*P

    Source: Chopra & Meindl (2016) Ch.11.
    """
    if order_qty <= 0:
        return 0.0
    H        = holding_cost_pct * unit_cost
    ordering = (annual_demand / order_qty) * ordering_cost
    holding  = (order_qty / 2.0) * H
    purchase = annual_demand * unit_cost
    return ordering + holding + purchase


def calc_cycle_service_level(safety_stock: int, demand_std: float,
                              lead_time_days: float) -> float:
    """
    Cycle Service Level (Type 1 service level) = Phi(z).
    CSL = probability of NOT stocking out during a replenishment cycle.

    z = safety_stock / sigma_LT
    sigma_LT = demand_std * sqrt(lead_time_days)   (constant lead time assumed)

    At 95% target service level (z=1.645): CSL = Phi(1.645) = 0.9500
    Safety stock rounded up by calc_safety_stock (ceil) so actual CSL >= target.

    Source: Chopra & Meindl (2016) Ch.12.
            Silver, Pyke & Thomas (2017) Ch.7.
            Ahmadi et al. (2019) Health Systems 8(2):134-151.
    """
    sigma_lt = demand_std * math.sqrt(lead_time_days)
    if sigma_lt <= 0.0:
        return 1.0
    z = safety_stock / sigma_lt
    return min(1.0, norm_cdf(z))


# ── Data generation ───────────────────────────────────────────────────────────
@st.cache_resource
def build_database():
    np.random.seed(42)
    random.seed(42)

    items = []
    defect_indices = {10,22,35,48,61,72,85,98,108}
    defect_types = {
        10:"Missing routing assignment", 22:"Incorrect reorder point",
        35:"Missing system integration", 48:"Missing routing assignment",
        61:"Incorrect reorder point",    72:"Missing routing assignment",
        85:"Missing system integration", 98:"Incorrect reorder point",
        108:"Missing routing assignment",
    }

    for idx, (name, cat, clo, chi) in enumerate(RAW_CATALOG):
        sku_id    = f"SKU-{1000+idx:03d}"
        unit_cost = round(random.uniform(clo, chi), 2)
        supplier  = random.choice(SUPPLIERS)
        is_single = random.random() < 0.18
        lot_num   = f"LOT-{random.choice([2024,2025])}-{random.randint(1000,9999)}"
        moq       = random.choice([1, 5, 10, 12, 24, 50])

        # ── Item-level cold chain classification ──
        # (fixes previous blanket category approach)
        if cat in COLD_CHAIN_CATS:
            is_cold = 1
        elif cat == "Diagnostic Test Kits":
            is_cold = 1 if name in COLD_CHAIN_KITS else 0
        else:
            is_cold = 0

        # Lead time: cold chain items have longer lead times (specialized logistics)
        lead_time = random.randint(7, 21) if is_cold else random.randint(3, 14)

        # Demand simulation — normal distribution with weekday-weighted mean
        base_demand = random.uniform(1.5, 8.0)
        demand_std  = base_demand * random.uniform(0.15, 0.40)
        annual_demand = round(base_demand * 365)

        ordering_cost_val = random.choice([25, 35, 45, 55, 75])
        # Holding cost rate: cold chain higher due to refrigeration/specialized storage
        # Source: Moons et al. (2019) Omega 82:205-217 cites 20-30% as typical range
        holding_pct = 0.28 if is_cold else 0.22

        eoq_val = calc_eoq(annual_demand, ordering_cost_val, holding_pct, unit_cost, moq)
        ss_val  = calc_safety_stock(demand_std, lead_time, service_level=0.95)
        rop_val = calc_rop(base_demand, lead_time, ss_val)
        max_stock_val = rop_val + eoq_val

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

        setup_defect = defect_types.get(idx)
        setup_status = "Defect" if setup_defect else "Active"

        items.append({
            "sku_id": sku_id, "name": name, "category": cat,
            "lot_number": lot_num, "expiration_date": exp.isoformat(),
            "days_to_expiry": days_left, "exp_status": exp_status,
            "unit_cost": unit_cost, "supplier": supplier,
            "is_single_source": int(is_single), "is_cold_chain": is_cold,
            "reorder_point": rop_val, "max_stock": max_stock_val,
            "eoq": eoq_val, "safety_stock": ss_val,
            "avg_daily_demand": round(base_demand, 2),
            "demand_std": round(demand_std, 3),
            "lead_time_days": lead_time,
            "annual_demand": annual_demand,
            "ordering_cost": ordering_cost_val,
            "holding_cost_pct": holding_pct,
            "moq": moq,
            "setup_status": setup_status, "setup_defect": setup_defect or "",
            "routing_ok": int(setup_defect != "Missing routing assignment"),
            "integration_ok": int(setup_defect != "Missing system integration"),
            "reorder_ok": int(setup_defect != "Incorrect reorder point"),
        })

    items_df = pd.DataFrame(items)

    # ── Inventory distribution ──
    inv_rows = []
    site_ids = [s[0] for s in SITES]
    stockout_skus = {"SKU-1012","SKU-1045","SKU-1098"}
    surplus_skus  = {"SKU-1075","SKU-1076","SKU-1077"}

    for _, item in items_df.iterrows():
        rp, ms, sku, est = (item["reorder_point"], item["max_stock"],
                            item["sku_id"], item["exp_status"])
        if   sku in stockout_skus:                            total = max(0, rp - random.randint(3,6))
        elif sku in surplus_skus:                             total = ms + random.randint(40,60)
        elif est in ("Expiring <30d","Expiring 31-60d"):      total = random.randint(18,45)
        elif est == "Expired":                                total = random.randint(2,8)
        else:                                                 total = random.randint(rp+2, max(rp+3, int(ms*0.85)))

        n_sites = (1 if sku in surplus_skus
                   else (2 if est in ("Expired","Expiring <30d") else random.randint(2,5)))
        sites = random.sample(site_ids, min(n_sites, len(site_ids)))
        remaining = total
        for i, site in enumerate(sites):
            if i == len(sites)-1: qty = max(0, remaining)
            else:
                share    = remaining // (len(sites)-i)
                qty      = max(0, share + random.randint(-1,1))
                remaining -= qty
            inv_rows.append({
                "record_id":  f"{sku}-{site}",
                "sku_id":     sku,
                "site_id":    site,
                "qty":        qty,
                "last_updated": (TODAY-timedelta(days=random.randint(0,7))).isoformat(),
            })

    inv_df = pd.DataFrame(inv_rows)
    agg = inv_df.groupby("sku_id")["qty"].sum().reset_index().rename(columns={"qty":"total_stock"})
    items_df = items_df.merge(agg, on="sku_id", how="left")
    items_df["total_stock"]     = items_df["total_stock"].fillna(0).astype(int)
    items_df["inventory_value"] = items_df["total_stock"] * items_df["unit_cost"]

    # Total annual cost (includes ordering + holding + purchase)
    items_df["total_annual_cost"] = items_df.apply(
        lambda r: calc_total_inventory_cost(
            r["annual_demand"], r["eoq"], r["ordering_cost"],
            r["holding_cost_pct"], r["unit_cost"]
        ), axis=1
    )

    # Cycle Service Level — correct formula replacing the previous ad-hoc approximation
    # Source: Chopra & Meindl (2016) Ch.12; Silver et al. (2017) Ch.7
    items_df["cycle_service_level"] = items_df.apply(
        lambda r: calc_cycle_service_level(
            r["safety_stock"], r["demand_std"], r["lead_time_days"]
        ), axis=1
    )

    # Demand history (90-day simulation — single exponential smoothing)
    demand_rows = []
    for _, item in items_df.iterrows():
        for day_offset in range(90):
            d = TODAY - timedelta(days=90-day_offset)
            weekday_factor = 1.1 if d.weekday() < 5 else 0.4  # weekday/weekend pattern
            demand = max(0, np.random.normal(
                item["avg_daily_demand"] * weekday_factor,
                item["demand_std"]
            ))
            demand_rows.append({
                "sku_id": item["sku_id"],
                "date":   d.isoformat(),
                "demand": round(demand, 2),
            })
    demand_df = pd.DataFrame(demand_rows)

    # Substitution catalog
    cat_groups = items_df.groupby("category")["sku_id"].apply(list).to_dict()
    subs_rows  = []
    for _, row in items_df.iterrows():
        pool = [s for s in cat_groups.get(row["category"],[]) if s != row["sku_id"]]
        for sub_sku in random.sample(pool, min(3, len(pool))):
            sr = items_df[items_df["sku_id"]==sub_sku].iloc[0]
            subs_rows.append({
                "sku_id":        row["sku_id"],
                "sub_sku_id":    sub_sku,
                "sub_name":      sr["name"],
                "sub_supplier":  sr["supplier"],
                "compatibility": random.choice(["Direct Equivalent","Clinical Equivalent","Functional Equivalent"]),
            })
    subs_df = pd.DataFrame(subs_rows)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    items_df.to_sql("items",         conn, index=False, if_exists="replace")
    inv_df.to_sql("inventory",       conn, index=False, if_exists="replace")
    subs_df.to_sql("substitutions",  conn, index=False, if_exists="replace")
    demand_df.to_sql("demand_history",conn,index=False, if_exists="replace")
    pd.DataFrame(SITES, columns=["site_id","site_name","location","type"]).to_sql(
        "sites", conn, index=False, if_exists="replace"
    )
    return conn, items_df, inv_df, subs_df, demand_df


conn, items_df, inv_df, subs_df, demand_df = build_database()


def get_metrics(_conn):
    exp_risk  = pd.read_sql("SELECT ROUND(SUM(total_stock*unit_cost),0) AS v FROM items WHERE days_to_expiry BETWEEN 1 AND 60",_conn)["v"].iloc[0] or 0
    stockouts = pd.read_sql("SELECT COUNT(*) AS c FROM items WHERE total_stock < reorder_point",_conn)["c"].iloc[0]
    defects   = pd.read_sql("SELECT COUNT(*) AS c FROM items WHERE setup_status='Defect'",_conn)["c"].iloc[0]
    total_skus= pd.read_sql("SELECT COUNT(*) AS c FROM items",_conn)["c"].iloc[0]
    surplus   = pd.read_sql("SELECT ROUND(SUM((total_stock-max_stock)*unit_cost),0) AS v FROM items WHERE total_stock > max_stock",_conn)["v"].iloc[0] or 0
    expired_v = pd.read_sql("SELECT ROUND(SUM(total_stock*unit_cost),0) AS v FROM items WHERE days_to_expiry<=0",_conn)["v"].iloc[0] or 0
    cold_risk = pd.read_sql("SELECT COUNT(*) AS c FROM items WHERE is_cold_chain=1 AND (days_to_expiry BETWEEN 1 AND 30 OR total_stock < reorder_point)",_conn)["c"].iloc[0]
    return {
        "total_skus":    int(total_skus),
        "exp_risk_val":  float(exp_risk),
        "stockouts":     int(stockouts),
        "defects":       int(defects),
        "surplus_val":   float(surplus),
        "expired_val":   float(expired_v),
        "cold_risk":     int(cold_risk),
    }


m = get_metrics(conn)

SCENARIOS = {
    "Normal Operations": {
        "icon":"OK","color":GREEN,
        "desc":"Standard daily network state.",
        "overrides":{},"banner":None,"note":None,
    },
    "Critical Shortage Alert": {
        "icon":"ALERT","color":RED,
        "desc":"Supply disruption across 3 sites.",
        "overrides":{"stockouts":7,"exp_risk_val":241000,"cold_risk":5},
        "banner":"SUPPLY DISRUPTION — 7 items below ROP across Main Campus, Long Island & Cobble Hill.",
        "note":None,
    },
    "Post-Cycle Audit (Wk 6)": {
        "icon":"AUDIT","color":BLUE,
        "desc":"State after 6 weeks — defects resolved.",
        "overrides":{"defects":4,"stockouts":1},"banner":None,
        "note":"67% reduction in setup defects (9 to 3). 2 of 3 stockouts resolved via OR-guided cross-site transfers.",
    },
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;padding:10px 0;">
      <div style="width:38px;height:38px;border-radius:10px;
           background:linear-gradient(135deg,#3B82F6,#06B6D4);
           display:flex;align-items:center;justify-content:center;
           font-size:20px;flex-shrink:0;">Lab</div>
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;
             color:#F0F6FF;letter-spacing:-.02em;line-height:1;">LabTrack</div>
        <div style="font-size:10px;color:#5A7A9C;letter-spacing:.07em;
             text-transform:uppercase;margin-top:2px;font-weight:600;">
             Clinical Supply v4.0</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1A2840;margin:10px 0;">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;color:#E8F0FF;margin-bottom:8px;">DEMO SCENARIO</p>', unsafe_allow_html=True)
    scenario_name = st.radio("scenario", list(SCENARIOS.keys()), label_visibility="collapsed")
    scen = SCENARIOS[scenario_name]
    st.markdown(f"""
    <div style="background:rgba(0,0,0,.2);border:1px solid #1A2840;
         border-left:3px solid {scen["color"]};border-radius:8px;
         padding:8px 12px;font-size:11.5px;color:#5A7A9C;margin-top:4px;">
         <b style="color:{scen["color"]};">{scen["icon"]} {scenario_name}</b><br>
         {scen["desc"]}
    </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)
    guided_tour = st.toggle("Guided Tour", value=False)
    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)

    _groq_available = bool(st.secrets.get("GROQ_API_KEY", ""))
    if _groq_available:
        st.markdown('<div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:8px 12px;font-size:11.5px;color:#6EE7B7;">AI Active — Groq connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);border-radius:8px;padding:8px 12px;font-size:11.5px;color:#FCD34D;">Add GROQ_API_KEY to Streamlit secrets to enable AI</div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1A2840;margin:14px 0;">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;color:#E8F0FF;margin-bottom:6px;">NETWORK SITES</p>', unsafe_allow_html=True)
    for s in SITES:
        st.markdown(f'<div style="font-size:12px;color:#5A7A9C;padding:3px 0;"><b style="color:#8BA4C0;">{s[1]}</b> · {s[2]}</div>', unsafe_allow_html=True)
    st.markdown(f'<hr style="border-color:#1A2840;margin:14px 0;"><p style="font-size:11px;color:#2A4060;">Synthetic demo data · {TODAY.strftime("%b %d, %Y")}</p>', unsafe_allow_html=True)

m_display = {**m}
for k, v in scen["overrides"].items():
    m_display[k] = v

# ── Top bar ────────────────────────────────────────────────────────────────────
cold_count = int(items_df["is_cold_chain"].sum())
ai_status  = "AI Active" if st.secrets.get("GROQ_API_KEY","") else "AI Offline"

st.markdown(f"""
<div style="background:linear-gradient(90deg,rgba(59,130,246,0.06) 0%,rgba(6,182,212,0.04) 100%);
     border-bottom:1px solid rgba(59,130,246,0.12);padding:10px 24px;
     display:flex;align-items:center;justify-content:space-between;margin:0 -1rem 0;font-size:12px;">
  <div style="display:flex;align-items:center;gap:20px;color:#4A6A8A;">
    <span style="color:#60A5FA;font-weight:700;font-family:'Syne',sans-serif;font-size:15px;">LabTrack</span>
    <span>Clinical Supply Intelligence v4.0</span>
    <span style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
          color:#6EE7B7;border-radius:20px;padding:2px 10px;font-weight:700;font-size:11px;">{ai_status}</span>
  </div>
  <div style="display:flex;align-items:center;gap:16px;color:#3A5A7C;font-size:11px;">
    <span>6 sites · {m_display["total_skus"]} SKUs · Synthetic demo · {TODAY.strftime("%b %d %Y")}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
h_left, h_right = st.columns([1.1, 0.9], gap="large")

with h_left:
    st.markdown(f"""
    <div style="padding:2.5rem 0 1.5rem;">
      <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(59,130,246,0.07);
           border:1px solid rgba(59,130,246,0.2);border-radius:20px;padding:5px 16px;
           font-size:11px;font-weight:700;color:#60A5FA;letter-spacing:.08em;
           text-transform:uppercase;margin-bottom:1.4rem;">
        OR Inventory Optimization for Clinical Laboratories
      </div>
      <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;
           color:#F0F6FF;line-height:1.05;letter-spacing:-.04em;margin-bottom:1rem;">
        Supply failures<br>discovered <span style="color:#60A5FA;">before</span><br>they happen.
      </div>
      <div style="font-size:15px;color:#4A6A8A;line-height:1.75;max-width:480px;margin-bottom:.6rem;">
        LabTrack monitors {m_display["total_skus"]} lot-controlled SKUs across a 6-site clinical network.
        EOQ and safety stock models compute optimal reorder parameters.
        AI translates OR outputs into plain-language actions for clinical teams.
      </div>
      <div style="font-size:11px;color:#2A4060;font-style:italic;margin-bottom:1.6rem;">
        OR models: EOQ (Harris 1913), Safety Stock/CSL (Chopra &amp; Meindl 2016 Ch.12;
        Silver, Pyke &amp; Thomas 2017 Ch.7). Problem context: Kasahun &amp; Kebede (2022)
        PMC9649967 — 12.94% lab commodity waste, 58-day avg stockout.
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);
             border-radius:10px;padding:10px 16px;min-width:120px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:#FCA5A5;">${m_display["exp_risk_val"]/1000:.0f}K</div>
          <div style="font-size:10.5px;color:#6A3A3A;text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-top:2px;">Expiry Risk</div>
        </div>
        <div style="background:rgba(249,115,22,0.07);border:1px solid rgba(249,115,22,0.2);
             border-radius:10px;padding:10px 16px;min-width:120px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:#FDBA74;">{m_display["stockouts"]}</div>
          <div style="font-size:10.5px;color:#6A4A1A;text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-top:2px;">Active Stockouts</div>
        </div>
        <div style="background:rgba(6,182,212,0.07);border:1px solid rgba(6,182,212,0.2);
             border-radius:10px;padding:10px 16px;min-width:120px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:#67E8F9;">{cold_count}</div>
          <div style="font-size:10.5px;color:#1A4A5A;text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-top:2px;">Cold Chain SKUs</div>
        </div>
        <div style="background:rgba(139,92,246,0.07);border:1px solid rgba(139,92,246,0.2);
             border-radius:10px;padding:10px 16px;min-width:120px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:#C4B5FD;">{m_display["defects"]}</div>
          <div style="font-size:10.5px;color:#3A2A6A;text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-top:2px;">Setup Defects</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with h_right:
    st.markdown("""
    <div style="padding:2rem 0 0;">
      <div style="background:linear-gradient(145deg,#090F20,#060C18);
           border:1px solid rgba(59,130,246,0.2);border-radius:16px;
           padding:1.6rem;box-shadow:0 8px 40px rgba(0,0,0,0.4);">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
          <div style="width:36px;height:36px;border-radius:10px;
               background:linear-gradient(135deg,#3B82F6,#8B5CF6);
               display:flex;align-items:center;justify-content:center;
               font-size:14px;flex-shrink:0;color:white;font-weight:700;">AI</div>
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#E8F0FF;">AI Executive Brief</div>
            <div style="font-size:11px;color:#3A5A7C;">Network-wide risk summary — Groq Llama 3.3 70B</div>
          </div>
        </div>
        <div style="font-size:12.5px;color:#3A5A7C;line-height:1.7;margin-bottom:1rem;">
          Plain-English summary of current network state — top risks, priority actions,
          and OR-based recommendations — generated from live dashboard data.
        </div>
    """, unsafe_allow_html=True)

    if st.button("Generate AI Network Brief", use_container_width=True, key="hero_ai_brief"):
        groq_api = st.secrets.get("GROQ_API_KEY", "")
        if not groq_api:
            st.warning("Add GROQ_API_KEY to Streamlit secrets to enable AI briefs.")
        else:
            with st.spinner("Generating brief..."):
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_api)
                    prompt = f"""You are a clinical supply chain intelligence system. Write a concise executive brief (under 180 words) for a hospital network supply chain director.
NETWORK STATE:
- {m_display["total_skus"]} SKUs across 6 sites
- Expiry risk value: ${m_display["exp_risk_val"]:,.0f}
- Active stockouts: {m_display["stockouts"]} items below reorder point
- Setup defects: {m_display["defects"]} items
- Cold chain at risk: {m_display["cold_risk"]} items
- Overstock waste: ${m_display["surplus_val"]:,.0f}
- Scenario: {scenario_name}
Write: (1) SITUATION (2) TOP 3 RISKS with numbers (3) PRIORITY ACTIONS (4) OR INSIGHT on EOQ/safety stock. Be specific."""
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile", max_tokens=400,
                        messages=[{"role":"user","content":prompt}]
                    )
                    brief = resp.choices[0].message.content.strip()
                    st.markdown(f"""
                    <div style="background:rgba(59,130,246,0.04);border:1px solid rgba(59,130,246,0.15);
                         border-left:3px solid #3B82F6;border-radius:0 10px 10px 0;
                         padding:14px 16px;font-size:12.5px;color:#C8D8F0;
                         line-height:1.8;white-space:pre-wrap;">{brief}</div>""",
                         unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("""
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);">
          <div style="display:flex;flex-wrap:wrap;gap:6px;">
            <span style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);
                 color:#6EE7B7;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;">
                 EOQ (Wilson 1913)</span>
            <span style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.15);
                 color:#93C5FD;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;">
                 Safety Stock 95% CSL</span>
            <span style="background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);
                 color:#C4B5FD;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;">
                 Demand Forecasting (EMA)</span>
            <span style="background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.15);
                 color:#67E8F9;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;">
                 Cold Chain (item-level)</span>
            <span style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);
                 color:#FCD34D;border-radius:6px;padding:3px 10px;font-size:11px;font-weight:600;">
                 ISO 15189 · CLIA · CLSI</span>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(59,130,246,0.2),transparent);margin:1.5rem 0;"></div>', unsafe_allow_html=True)

if scen["banner"]: st.error(scen["banner"])
if scen["note"]:   st.success(scen["note"])

# ── TABS ───────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6 = st.tabs([
    "  Risk Dashboard  ",
    "  Lot Tracker  ",
    "  Item Setup  ",
    "  Disruption Alerts  ",
    "  OR Optimizer  ",
    "  Data Preview  ",
])

# ════ TAB 1 — RISK DASHBOARD ════
with t1:
    if guided_tour:
        st.info("**Risk Dashboard** — Daily pulse check. Expiry Risk Value and Stockout count drive clinical continuity decisions. Cold-chain items flagged separately per item-level classification (not blanket category). Use scenario toggle to simulate disruption states.")

    ch1, ch2 = st.columns(2, gap="medium")
    with ch1:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Inventory Value by Category</div>', unsafe_allow_html=True)
        cat_val = pd.read_sql(
            "SELECT category,ROUND(SUM(inventory_value),0) AS v,COUNT(*) AS n,SUM(is_cold_chain) AS cold FROM items GROUP BY category ORDER BY v DESC",
            conn
        )
        colors = [CYAN if row["cold"]>0 else BLUE for _,row in cat_val.iterrows()]
        fig1 = go.Figure(go.Bar(
            x=cat_val["category"], y=cat_val["v"],
            marker=dict(color=colors, opacity=0.85),
            text=[f"${v:,.0f}" for v in cat_val["v"]],
            textposition="outside", textfont=dict(size=9, color="#8BA4C0")
        ))
        fig1.update_layout(**PLOT_LAYOUT, height=230,
            xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9,color=SUB), tickangle=35),
            yaxis=dict(showgrid=False, showline=False, showticklabels=False))
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})
        st.caption("Blue = ambient · Cyan = cold chain — classified at item level per FDA IVD storage requirements")

    with ch2:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Expiration Status Distribution</div>', unsafe_allow_html=True)
        status_ct = items_df["exp_status"].value_counts().reset_index()
        status_ct.columns = ["status","count"]
        CMAP = {"OK":GREEN,"Expiring 31-60d":AMBER,"Expiring <30d":ORANGE,"Expired":RED}
        fig2 = go.Figure(go.Pie(
            labels=status_ct["status"], values=status_ct["count"], hole=0.58,
            marker_colors=[CMAP.get(s,"#888") for s in status_ct["status"]],
            textinfo="label+percent", textfont=dict(size=11,color="#E8F0FF")
        ))
        fig2.update_layout(**PLOT_LAYOUT, height=230, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-top:6px;margin-bottom:10px;">Stock Position and OR-Optimized Reorder Points by Site</div>', unsafe_allow_html=True)
    site_health = pd.read_sql("""
        SELECT s.site_name, SUM(i.qty) AS total_units, COUNT(DISTINCT i.sku_id) AS sku_count,
               ROUND(SUM(i.qty*it.unit_cost),0) AS site_value
        FROM inventory i JOIN items it ON i.sku_id=it.sku_id JOIN sites s ON i.site_id=s.site_id
        GROUP BY s.site_name ORDER BY site_value DESC""", conn)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Inventory Value ($)",x=site_health["site_name"],y=site_health["site_value"],marker_color=BLUE,opacity=0.8,yaxis="y"))
    fig3.add_trace(go.Scatter(name="SKUs Stocked",x=site_health["site_name"],y=site_health["sku_count"],mode="lines+markers",line=dict(color=CYAN,width=2),marker=dict(size=7),yaxis="y2"))
    fig3.update_layout(**PLOT_LAYOUT, height=220,
        xaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color=SUB)),
        yaxis=dict(showgrid=False,showline=False,showticklabels=False),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,showline=False,tickfont=dict(size=10,color=CYAN)),
        legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.12))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin:10px 0 6px;">Critical Alerts — Top 15 Urgent Items</div>', unsafe_allow_html=True)
    urgent = pd.read_sql("""
        SELECT sku_id,name,category,exp_status,days_to_expiry,total_stock,reorder_point,
               unit_cost,ROUND(total_stock*unit_cost,0) AS at_risk_value,
               supplier,is_single_source,is_cold_chain
        FROM items
        WHERE exp_status IN ('Expired','Expiring <30d','Expiring 31-60d') OR total_stock<reorder_point
        ORDER BY CASE exp_status WHEN 'Expired' THEN 0 WHEN 'Expiring <30d' THEN 1
                 WHEN 'Expiring 31-60d' THEN 2 ELSE 3 END,
                 (total_stock*1.0/NULLIF(reorder_point,0)) ASC LIMIT 15""", conn)
    BADGE = {"Expired":"badge-expired","Expiring <30d":"badge-warn30","Expiring 31-60d":"badge-warn60","OK":"badge-ok"}
    for _,row in urgent.iterrows():
        stockout_flag = '<span style="font-size:10px;color:#FCA5A5;font-weight:700;">STOCKOUT</span>' if row["total_stock"]<row["reorder_point"] else ""
        cold_flag     = '<span style="font-size:10px;color:#67E8F9;font-weight:700;">COLD</span>' if row["is_cold_chain"] else ""
        single_flag   = '<span style="font-size:10px;color:#FCD34D;font-weight:600;">Single-src</span>' if row["is_single_source"] else ""
        c1,c2,c3,c4,c5,c6 = st.columns([3,2,1.8,1.2,1.5,1.8])
        c1.markdown(f'<div style="padding-top:4px;"><div style="font-size:13px;font-weight:700;color:#E8F0FF;">{row["name"]}</div><div style="font-size:10.5px;color:#5A7A9C;">{row["sku_id"]}</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div style="font-size:11.5px;color:#8BA4C0;padding-top:6px;">{row["category"]}</div>',unsafe_allow_html=True)
        c3.markdown(f'<span class="badge {BADGE.get(row["exp_status"],"badge-ok")}">{row["exp_status"]}</span>',unsafe_allow_html=True)
        c4.markdown(f'<div style="font-size:13px;font-weight:700;color:{"#F87171" if row["total_stock"]<row["reorder_point"] else "#E8F0FF"};padding-top:3px;">{row["total_stock"]}<div style="font-size:10px;color:#5A7A9C;font-weight:400;">ROP:{row["reorder_point"]}</div></div>',unsafe_allow_html=True)
        c5.markdown(f'<div style="font-size:13px;font-weight:700;color:#FCD34D;padding-top:3px;">${row["at_risk_value"]:,.0f}</div>',unsafe_allow_html=True)
        c6.markdown(f'<div style="padding-top:5px;">{stockout_flag} {cold_flag} {single_flag}</div>',unsafe_allow_html=True)
        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:12px 0;">',unsafe_allow_html=True)


# ════ TAB 2 — LOT TRACKER ════
with t2:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin-bottom:8px;">Lot-Controlled Inventory — Full Network View</div>',unsafe_allow_html=True)
    if guided_tour:
        st.info("**Lot Tracker** — Every SKU by lot number, expiry, and site stock. Cold-chain classified at item level. ISO 15189 and CLIA require lot-level traceability for all reagents used in patient testing.")

    f1,f2,f3,f4 = st.columns(4,gap="small")
    site_opts = ["All Sites"]+[s[1] for s in SITES]
    cat_opts  = ["All Categories"]+sorted(items_df["category"].unique().tolist())
    stat_opts = ["All Statuses","OK","Expiring <30d","Expiring 31-60d","Expired"]
    cold_opts = ["All Items","Cold Chain Only","Ambient Only"]
    sel_site  = f1.selectbox("Site",     site_opts, label_visibility="collapsed")
    sel_cat   = f2.selectbox("Category", cat_opts,  label_visibility="collapsed")
    sel_stat  = f3.selectbox("Status",   stat_opts, label_visibility="collapsed")
    sel_cold  = f4.selectbox("Storage",  cold_opts, label_visibility="collapsed")

    query = "SELECT sku_id,name,category,lot_number,expiration_date,days_to_expiry,exp_status,total_stock,reorder_point,eoq,safety_stock,lead_time_days,unit_cost,supplier,is_single_source,is_cold_chain FROM items WHERE 1=1"
    if sel_stat != "All Statuses": query += f" AND exp_status='{sel_stat}'"
    if sel_cat  != "All Categories": query += f" AND category='{sel_cat}'"
    if sel_cold == "Cold Chain Only": query += " AND is_cold_chain=1"
    if sel_cold == "Ambient Only":    query += " AND is_cold_chain=0"
    query += " ORDER BY days_to_expiry ASC"
    lot_df = pd.read_sql(query, conn)

    if sel_site != "All Sites":
        sid = next(s[0] for s in SITES if s[1]==sel_site)
        site_inv = inv_df[inv_df["site_id"]==sid][["sku_id","qty"]]
        lot_df = lot_df.merge(site_inv, on="sku_id", how="inner")
        lot_df["total_stock"] = lot_df["qty"]
        lot_df.drop(columns=["qty"], inplace=True)

    l1,l2,l3,l4 = st.columns(4)
    l1.metric("SKUs Shown", len(lot_df))
    l2.metric("Cold Chain Items", int(lot_df["is_cold_chain"].sum()))
    l3.metric("Expiring ≤30d", int((lot_df["days_to_expiry"].between(1,30)).sum()))
    l4.metric("At-risk Value", f'${(lot_df[lot_df["days_to_expiry"].between(1,60)]["total_stock"]*lot_df[lot_df["days_to_expiry"].between(1,60)]["unit_cost"]).sum():,.0f}')

    display_df = lot_df[["sku_id","name","category","is_cold_chain","lot_number","expiration_date","days_to_expiry","exp_status","total_stock","reorder_point","eoq","safety_stock","lead_time_days","unit_cost","supplier"]].copy()
    display_df["is_cold_chain"] = display_df["is_cold_chain"].map({1:"Cold (2-8C)",0:"Ambient"})
    display_df.columns = ["SKU","Name","Category","Storage","Lot","Exp. Date","Days Left","Status","Stock","ROP","EOQ","Safety Stock","Lead Time (d)","Unit Cost ($)","Supplier"]
    display_df["Unit Cost ($)"] = display_df["Unit Cost ($)"].map("${:.2f}".format)
    st.dataframe(display_df, use_container_width=True, height=430, hide_index=True)
    st.caption("ISO 15189:2022 and CLIA require lot-level traceability for all reagents used in patient testing.")
    st.download_button("Export CSV", display_df.to_csv(index=False), "labtrack_lots.csv","text/csv")


# ════ TAB 3 — ITEM SETUP ════
with t3:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin-bottom:8px;">Item Onboarding and Setup Status</div>',unsafe_allow_html=True)
    if guided_tour:
        st.info("**Item Setup** — Each defect maps to a specific fix. OR-computed reorder points flagged where defects are found.")

    defect_df = pd.read_sql("SELECT setup_defect,COUNT(*) as cnt FROM items WHERE setup_defect!='' GROUP BY setup_defect", conn)
    total_def   = int(defect_df["cnt"].sum())
    missing_rt  = int(defect_df[defect_df["setup_defect"]=="Missing routing assignment"]["cnt"].sum() if len(defect_df) else 0)
    bad_rop     = int(defect_df[defect_df["setup_defect"]=="Incorrect reorder point"]["cnt"].sum() if len(defect_df) else 0)
    missing_in  = int(defect_df[defect_df["setup_defect"]=="Missing system integration"]["cnt"].sum() if len(defect_df) else 0)

    d1,d2,d3,d4 = st.columns(4)
    d1.metric("Total Defects", total_def)
    d2.metric("Missing Routing", missing_rt)
    d3.metric("Bad Reorder Point", bad_rop, help="OR-computed ROP available for all affected items")
    d4.metric("Missing Integration", missing_in)

    cc1,cc2 = st.columns([1,2],gap="medium")
    with cc1:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Defect Breakdown</div>',unsafe_allow_html=True)
        fig_d = go.Figure(go.Bar(
            x=defect_df["cnt"], y=defect_df["setup_defect"], orientation="h",
            marker_color=[RED,AMBER,ORANGE], text=defect_df["cnt"],
            textposition="outside", textfont=dict(size=11,color="#8BA4C0")
        ))
        fig_d.update_layout(**PLOT_LAYOUT, height=160,
            xaxis=dict(showgrid=False,showline=False,showticklabels=False),
            yaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color="#8BA4C0")))
        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar":False})

    with cc2:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Setup Completion — Illustrative Scenario</div>',unsafe_allow_html=True)
        st.caption("Note: 'Before' baselines are illustrative estimates for scenario demonstration only. They are not derived from US clinical lab benchmark data.")
        total_items = len(items_df)
        # Illustrative "before" baselines — NOT sourced from clinical benchmarks
        # Note: Kasahun & Kebede (2022) PMC9649967 found 49% records accuracy in
        # facilities without structured systems, but that study reflects resource-limited
        # settings and should not be directly applied to US hospital networks.
        before_routing = 65
        before_rop     = 62
        before_integ   = 68
        after_routing  = round(100 - missing_rt/total_items*100, 1)
        after_rop      = round(100 - bad_rop/total_items*100, 1)
        after_integ    = round(100 - missing_in/total_items*100, 1)

        fig_ba = go.Figure()
        fig_ba.add_trace(go.Bar(name="Before (illustrative baseline)",x=["Routing","Reorder Pt","Integration"],y=[before_routing,before_rop,before_integ],marker_color="#1A2840"))
        fig_ba.add_trace(go.Bar(name="After LabTrack (synthetic data)",x=["Routing","Reorder Pt","Integration"],y=[after_routing,after_rop,after_integ],marker_color=GREEN))
        fig_ba.update_layout(**PLOT_LAYOUT, height=160, barmode="group",
            xaxis=dict(showgrid=False,showline=False,tickfont=dict(size=11,color=SUB)),
            yaxis=dict(showgrid=False,showline=False,range=[0,110],showticklabels=False),
            legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_ba, use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin-top:8px;margin-bottom:6px;">Open Defect Register — with OR-Recommended Fix</div>',unsafe_allow_html=True)
    defect_items = pd.read_sql("SELECT sku_id,name,category,setup_defect,supplier,reorder_point,eoq,safety_stock FROM items WHERE setup_defect!='' ORDER BY setup_defect", conn)
    RESOLVE = {
        "Missing routing assignment": "Assign 3PL routing node in distribution system — check site-to-site transfer lanes",
        "Incorrect reorder point":    "Replace with OR-computed ROP = avg demand x lead time + safety stock (Silver et al. 2017 Ch.7)",
        "Missing system integration": "Link SKU to LIS/ERP inventory module and validate demand data sync for OR calculations",
    }
    for _,row in defect_items.iterrows():
        c1,c2,c3,c4,c5 = st.columns([1,2.5,2,1.5,3])
        c1.markdown(f'<div style="font-size:11px;color:#5A7A9C;padding-top:5px;">{row["sku_id"]}</div>',unsafe_allow_html=True)
        c2.markdown(f'<div style="font-size:12.5px;font-weight:600;color:#E8F0FF;padding-top:3px;">{row["name"]}</div><div style="font-size:10.5px;color:#5A7A9C;">{row["category"]}</div>',unsafe_allow_html=True)
        c3.markdown(f'<span class="badge badge-critical">{row["setup_defect"]}</span>',unsafe_allow_html=True)
        c4.markdown(f'<div style="font-size:11px;color:#93C5FD;padding-top:5px;">ROP: {row["reorder_point"]}<br>EOQ: {row["eoq"]}</div>',unsafe_allow_html=True)
        c5.markdown(f'<div style="font-size:11.5px;color:#8BA4C0;padding-top:5px;">→ {RESOLVE.get(row["setup_defect"],"Review setup params")}</div>',unsafe_allow_html=True)
        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:12px 0;">',unsafe_allow_html=True)


# ════ TAB 4 — DISRUPTION ALERTS ════
with t4:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin-bottom:8px;">Supply Disruption Alerts — Substitution and AI Communication Plans</div>',unsafe_allow_html=True)
    if guided_tour:
        st.info("**Disruption Alerts** — Stockout alerts with OR-computed reorder quantities, substitution catalog, and AI communication plans.")

    single_at_risk = int(items_df[
        ((items_df["is_single_source"]==1) & (items_df["exp_status"].isin(["Expiring <30d","Expiring 31-60d","Expired"])))
        | ((items_df["is_single_source"]==1) & (items_df["total_stock"] < items_df["reorder_point"]))
    ].shape[0])
    cold_at_risk = int(items_df[
        (items_df["is_cold_chain"]==1) & (items_df["total_stock"] < items_df["reorder_point"])
    ].shape[0])

    a1,a2,a3,a4 = st.columns(4)
    a1.metric("Stockout Alerts",       m["stockouts"])
    a2.metric("Cold Chain Stockouts",  cold_at_risk)
    a3.metric("Single-Source at Risk", single_at_risk)
    a4.metric("Overstock Waste",       f'${m_display["surplus_val"]:,.0f}')

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#E8F0FF;margin-bottom:6px;">Active Stockout Alerts</div>',unsafe_allow_html=True)
    stockouts = pd.read_sql(
        "SELECT sku_id,name,category,total_stock,reorder_point,eoq,safety_stock,"
        "lead_time_days,unit_cost,supplier,is_single_source,is_cold_chain,exp_status "
        "FROM items WHERE total_stock<reorder_point", conn
    )

    for _,row in stockouts.iterrows():
        cold_label = " — COLD CHAIN" if row["is_cold_chain"] else ""
        with st.expander(f"STOCKOUT  {row['name']}  {row['sku_id']}{cold_label}  Stock: {row['total_stock']} / ROP: {row['reorder_point']}", expanded=True):
            i1,i2,i3,i4,i5 = st.columns(5)
            i1.markdown(f"**Category:** {row['category']}")
            i2.markdown(f"**Supplier:** {row['supplier']}")
            i3.markdown(f"**Single-source:** {'Yes' if row['is_single_source'] else 'No'}")
            i4.markdown(f"**EOQ (OR):** {row['eoq']} units")
            i5.markdown(f"**Lead time:** {row['lead_time_days']} days{'  COLD' if row['is_cold_chain'] else ''}")

            subs = subs_df[subs_df["sku_id"]==row["sku_id"]]
            if not subs.empty:
                st.markdown("**Substitution options:**")
                for _,sub in subs.iterrows():
                    sv = int(items_df[items_df["sku_id"]==sub["sub_sku_id"]]["total_stock"].values[0]) if len(items_df[items_df["sku_id"]==sub["sub_sku_id"]]) else 0
                    st.markdown(f'<div style="background:#0D1629;border:1px solid #1A2840;border-radius:9px;padding:10px 14px;margin:4px 0;"><span style="font-size:13px;font-weight:600;color:#E8F0FF;">{sub["sub_name"]}</span><span style="margin-left:10px;font-size:11px;background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:#93C5FD;border-radius:4px;padding:1px 8px;">{sub["compatibility"]}</span><span style="margin-left:10px;font-size:11.5px;color:#5A7A9C;">Network stock: {sv} units · {sub["sub_supplier"]}</span></div>',unsafe_allow_html=True)

            sub_list = ", ".join(subs["sub_name"].tolist()) if not subs.empty else "none identified"
            if st.secrets.get("GROQ_API_KEY", ""):
                if st.button(f"Generate AI Communication Plan — {row['sku_id']}", key=f"cp_{row['sku_id']}"):
                    try:
                        from groq import Groq
                        client = Groq(api_key=st.secrets.get("GROQ_API_KEY",""))
                        prompt = f"""Write a professional itemised communication plan for a stockout. Under 150 words.
ITEM: {row['name']} ({row['sku_id']}) CATEGORY: {row['category']}
STOCK: {row['total_stock']} (ROP: {row['reorder_point']}, EOQ: {row['eoq']}, Safety Stock: {row['safety_stock']})
LEAD TIME: {row['lead_time_days']} days SUPPLIER: {row['supplier']} {'(SINGLE SOURCE)' if row['is_single_source'] else ''}
COLD CHAIN: {'Yes — 2-8C handling required' if row['is_cold_chain'] else 'No'}
SUBSTITUTES: {sub_list}
Write: (1) immediate action with EOQ quantity (2) clinical team notification (3) procurement step (4) monitoring action"""
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=400,messages=[{"role":"user","content":prompt}])
                        plan = resp.choices[0].message.content.strip()
                        st.markdown(f'<div style="background:#0D1629;border:1px solid #1A2840;border-left:3px solid #3B82F6;border-radius:10px;padding:14px 16px;font-size:13px;color:#E8F0FF;line-height:1.75;white-space:pre-wrap;">{plan}</div>',unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Groq error: {e}")

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#E8F0FF;margin-bottom:6px;">Surplus Inventory — OR Rotation Candidates</div>',unsafe_allow_html=True)
    surplus = pd.read_sql("""SELECT sku_id,name,category,total_stock,max_stock,
        (total_stock-max_stock) AS overstock_units,ROUND((total_stock-max_stock)*unit_cost,0) AS overstock_value,
        unit_cost,supplier,expiration_date,is_cold_chain
        FROM items WHERE total_stock>max_stock ORDER BY overstock_value DESC LIMIT 15""",conn)
    if not surplus.empty:
        surplus["overstock_value"] = surplus["overstock_value"].map("${:,.0f}".format)
        surplus["unit_cost"] = surplus["unit_cost"].map("${:.2f}".format)
        surplus["is_cold_chain"] = surplus["is_cold_chain"].map({1:"Cold (2-8C)",0:"Ambient"})
        disp = surplus[["sku_id","name","category","is_cold_chain","total_stock","max_stock","overstock_units","overstock_value","expiration_date","supplier"]]
        disp.columns = ["SKU","Name","Category","Storage","Stock","Max","Overstock","Waste Value","Exp. Date","Supplier"]
        st.dataframe(disp, use_container_width=True, height=300, hide_index=True)
        st.download_button("Export Rotation List", disp.to_csv(index=False), "labtrack_surplus.csv","text/csv")


# ════ TAB 5 — OR OPTIMIZER ════
with t5:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#E8F0FF;margin-bottom:8px;">Operations Research Optimizer</div>',unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(59,130,246,0.05);border:1px solid rgba(59,130,246,0.2);
         border-radius:10px;padding:14px 18px;margin-bottom:16px;font-size:13px;
         color:#8BA4C0;line-height:1.75;">
    <b style="color:#93C5FD;">OR Model Foundations</b><br>
    <b>EOQ (Wilson formula)</b>: Harris, F.W. (1913). <i>Factory, The Magazine of Management</i> 10(2):135.
    Minimizes total ordering + holding costs under constant-demand assumptions.<br>
    <b>Safety Stock / Cycle Service Level</b>: CSL = &Phi;(z), z = SS / &sigma;<sub>LT</sub>.
    Chopra &amp; Meindl (2016) Ch.12; Silver, Pyke &amp; Thomas (2017) Ch.7.<br>
    <b>Reorder Point</b>: ROP = d&middot;L + SS. Standard continuous-review (Q,R) policy.<br>
    <b>Demand Forecasting</b>: Single exponential smoothing (&alpha;=0.3). Brown (1959); Holt (1957).<br>
    <b>Healthcare application</b>: Ahmadi et al. (2019) <i>Health Systems</i> 8(2):134-151 validates
    EOQ/safety-stock in hospital supply chains.
    </div>
    """, unsafe_allow_html=True)

    if guided_tour:
        st.info("**OR Optimizer** — All formulas sourced. EOQ uses Wilson formula. Safety stock uses z-score (z=1.645 at 95%). CSL = Phi(z) — the correct cycle service level formula.")

    # ── Portfolio-level metrics ──
    st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Portfolio-Level OR Summary</div>',unsafe_allow_html=True)

    total_annual_cost        = items_df["total_annual_cost"].sum()
    avg_csl                  = items_df["cycle_service_level"].mean()
    avg_lead_time            = items_df["lead_time_days"].mean()
    total_safety_stock_value = (items_df["safety_stock"] * items_df["unit_cost"]).sum()
    cold_chain_cost          = items_df[items_df["is_cold_chain"]==1]["total_annual_cost"].sum()
    items_below_ss           = int((items_df["total_stock"] < items_df["safety_stock"]).sum())

    o1,o2,o3,o4,o5,o6 = st.columns(6)
    o1.metric("Total Annual Inventory Cost", f"${total_annual_cost/1e6:.2f}M")
    o2.metric("Avg Cycle Service Level",     f"{avg_csl*100:.1f}%",
              help="CSL = Phi(z), target 95%. Source: Chopra & Meindl (2016) Ch.12")
    o3.metric("Avg Lead Time",               f"{avg_lead_time:.0f} days")
    o4.metric("Safety Stock Investment",     f"${total_safety_stock_value:,.0f}")
    o5.metric("Cold Chain Annual Cost",      f"${cold_chain_cost/1e6:.2f}M")
    o6.metric("Items Below Safety Stock",    str(items_below_ss),
              delta=f"+{items_below_ss}" if items_below_ss>0 else None, delta_color="inverse")

    st.markdown("<br>",unsafe_allow_html=True)
    or1, or2 = st.columns(2, gap="medium")

    with or1:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Total Annual Cost by Category (EOQ Model)</div>',unsafe_allow_html=True)
        cat_cost = items_df.groupby("category")["total_annual_cost"].sum().reset_index().sort_values("total_annual_cost",ascending=False)
        fig_cost = go.Figure(go.Bar(
            y=cat_cost["category"], x=cat_cost["total_annual_cost"], orientation="h",
            marker=dict(color=CYAN, opacity=0.8),
            text=[f"${v/1000:.0f}K" for v in cat_cost["total_annual_cost"]],
            textposition="outside", textfont=dict(size=10,color="#8BA4C0")
        ))
        fig_cost.update_layout(**PLOT_LAYOUT, height=280,
            xaxis=dict(showgrid=False,showline=False,showticklabels=False),
            yaxis=dict(showgrid=False,showline=False,tickfont=dict(size=10,color="#8BA4C0")))
        st.plotly_chart(fig_cost, use_container_width=True, config={"displayModeBar":False})

    with or2:
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-bottom:10px;">Cycle Service Level Distribution (CSL = Phi(z))</div>',unsafe_allow_html=True)
        csl_hist = items_df["cycle_service_level"].values * 100
        fig_csl = go.Figure(go.Histogram(
            x=csl_hist, nbinsx=20,
            marker=dict(color=GREEN, opacity=0.8, line=dict(color="#0D1629",width=0.5))
        ))
        fig_csl.add_vline(x=95, line_dash="dash", line_color=AMBER,
                          annotation_text="95% target", annotation_font_color=AMBER)
        fig_csl.update_layout(**PLOT_LAYOUT, height=280,
            xaxis=dict(showgrid=False,showline=False,
                       title=dict(text="Cycle Service Level (%)",font=dict(color=SUB,size=11)),
                       tickfont=dict(color=SUB)),
            yaxis=dict(showgrid=False,showline=False,showticklabels=False))
        st.plotly_chart(fig_csl, use_container_width=True, config={"displayModeBar":False})
        st.caption("CSL = Phi(z) where z = safety_stock / sigma_LT. Source: Chopra & Meindl (2016) Ch.12")

    # ── EOQ Cost Curve ──
    st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-top:4px;margin-bottom:6px;">EOQ Cost Trade-off Explorer</div>',unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#5A7A9C;margin-bottom:10px;">Select a SKU to visualize the total cost curve. EOQ minimizes TC = (D/Q)S + (Q/2)H. Source: Chopra &amp; Meindl (2016) Ch.11.</div>',unsafe_allow_html=True)

    sku_search = st.text_input("Search SKU or item name", placeholder="e.g. Troponin, PCR, Nitrile...",
                               key="sku_or_search", label_visibility="collapsed")
    sku_list = items_df[items_df["name"].str.contains(sku_search,case=False,na=False)]["sku_id"].tolist() if sku_search else items_df.head(30)["sku_id"].tolist()
    sku_options = {f"{row['sku_id']} — {row['name']}": row['sku_id'] for _,row in items_df[items_df["sku_id"].isin(sku_list)].iterrows()}

    if sku_options:
        selected_label = st.selectbox("Select item for EOQ deep-dive", list(sku_options.keys()), label_visibility="collapsed")
        selected_sku   = sku_options[selected_label]
        item = items_df[items_df["sku_id"]==selected_sku].iloc[0]

        eoq_c1, eoq_c2 = st.columns([2,1], gap="medium")

        with eoq_c1:
            q_range       = np.arange(max(1,item["moq"]), max(item["eoq"]*4, 100), 1)
            ordering_costs = (item["annual_demand"] / q_range) * item["ordering_cost"]
            holding_costs  = (q_range / 2) * (item["holding_cost_pct"] * item["unit_cost"])
            total_costs    = ordering_costs + holding_costs

            fig_eoq = go.Figure()
            fig_eoq.add_trace(go.Scatter(x=q_range, y=ordering_costs, name="Ordering Cost (D/Q)S",  line=dict(color=ORANGE,width=2,dash="dot")))
            fig_eoq.add_trace(go.Scatter(x=q_range, y=holding_costs,  name="Holding Cost (Q/2)H",   line=dict(color=CYAN,width=2,dash="dot")))
            fig_eoq.add_trace(go.Scatter(x=q_range, y=total_costs,    name="Total Cost TC",          line=dict(color=GREEN,width=3)))
            fig_eoq.add_vline(x=item["eoq"], line_dash="dash", line_color=BLUE,
                              annotation_text=f"EOQ = {item['eoq']} units",
                              annotation_font_color=BLUE, annotation_position="top right")
            fig_eoq.update_layout(**PLOT_LAYOUT, height=280,
                xaxis=dict(showgrid=False,showline=False,
                           title=dict(text="Order Quantity (units)",font=dict(color=SUB,size=11)),
                           tickfont=dict(color=SUB)),
                yaxis=dict(showgrid=False,showline=False,
                           title=dict(text="Annual Cost ($)",font=dict(color=SUB,size=11)),
                           tickfont=dict(color=SUB,size=10)),
                legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)",
                            orientation="h",x=0,y=1.12))
            st.plotly_chart(fig_eoq, use_container_width=True, config={"displayModeBar":False})
            st.caption("Wilson EOQ formula: sqrt(2DS/H). Source: Harris (1913); Chopra & Meindl (2016) Ch.11.")

        with eoq_c2:
            csl_val = calc_cycle_service_level(int(item["safety_stock"]), float(item["demand_std"]), float(item["lead_time_days"]))
            z_val   = item["safety_stock"] / (item["demand_std"] * math.sqrt(item["lead_time_days"])) if item["demand_std"] > 0 else 0
            st.markdown(f"""
            <div class="or-card">
              <div class="or-label">Item</div>
              <div style="font-size:13px;font-weight:600;color:#E8F0FF;margin-bottom:12px;">{item['name']}</div>
              <div class="or-label">OR Parameters</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
                <div><div style="font-size:10px;color:#5A7A9C;">EOQ</div><div class="or-metric">{item['eoq']}</div><div class="or-sub">units/order</div></div>
                <div><div style="font-size:10px;color:#5A7A9C;">Safety Stock</div><div class="or-metric">{item['safety_stock']}</div><div class="or-sub">z={z_val:.2f}</div></div>
                <div><div style="font-size:10px;color:#5A7A9C;">ROP</div><div class="or-metric">{item['reorder_point']}</div><div class="or-sub">units</div></div>
                <div><div style="font-size:10px;color:#5A7A9C;">Lead Time</div><div class="or-metric">{item['lead_time_days']}</div><div class="or-sub">days</div></div>
              </div>
              <div class="or-label">Cycle Service Level</div>
              <div class="or-metric" style="color:#10B981;">{csl_val*100:.1f}%</div>
              <div class="or-sub">CSL = &Phi;(z) = &Phi;({z_val:.2f}). Source: Chopra &amp; Meindl (2016) Ch.12</div>
              <br>
              <div class="or-label">Cost Inputs</div>
              <div style="font-size:12px;color:#8BA4C0;line-height:1.8;">
                Unit cost: ${item['unit_cost']:.2f}<br>
                Avg daily demand: {item['avg_daily_demand']:.1f} units<br>
                Annual demand: {item['annual_demand']:,} units<br>
                Ordering cost S: ${item['ordering_cost']}/order<br>
                Holding rate H: {item['holding_cost_pct']*100:.0f}% per year<br>
                MOQ: {item['moq']} units<br>
                {'Cold chain (2-8C)' if item['is_cold_chain'] else 'Ambient storage'}
              </div>
            </div>""", unsafe_allow_html=True)

        # ── Demand History + EMA Forecast ──
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-top:16px;margin-bottom:6px;">90-Day Demand History + Exponential Smoothing Forecast</div>',unsafe_allow_html=True)
        sku_demand = demand_df[demand_df["sku_id"]==selected_sku].copy()
        sku_demand["date"] = pd.to_datetime(sku_demand["date"])
        sku_demand = sku_demand.sort_values("date")

        # Single exponential smoothing (Brown 1959 / Holt 1957)
        alpha = 0.3
        ema   = [sku_demand["demand"].iloc[0]]
        for val in sku_demand["demand"].iloc[1:]:
            ema.append(alpha*val + (1-alpha)*ema[-1])
        sku_demand["ema"] = ema

        # 14-day forecast with 95% confidence band
        last_ema       = ema[-1]
        forecast_dates = [TODAY + timedelta(days=i) for i in range(1,15)]
        forecast_vals  = [last_ema] * 14
        # 95% CI: mean +/- 1.96 * sigma (approximate, single-period ahead)
        upper_band = [last_ema + 1.96*item["demand_std"]] * 14
        lower_band = [max(0, last_ema - 1.96*item["demand_std"])] * 14

        fig_dem = go.Figure()
        fig_dem.add_trace(go.Scatter(x=sku_demand["date"],y=sku_demand["demand"],name="Actual Demand",line=dict(color="#1A3050",width=1),mode="lines"))
        fig_dem.add_trace(go.Scatter(x=sku_demand["date"],y=sku_demand["ema"],name="EMA (alpha=0.3)",line=dict(color=BLUE,width=2.5)))
        fig_dem.add_trace(go.Scatter(x=forecast_dates,y=forecast_vals,name="14-Day Forecast",line=dict(color=CYAN,width=2,dash="dash")))
        fig_dem.add_trace(go.Scatter(
            x=forecast_dates+forecast_dates[::-1],y=upper_band+lower_band[::-1],
            fill="toself",fillcolor="rgba(6,182,212,0.06)",line=dict(color="rgba(0,0,0,0)"),
            name="95% Confidence Band"
        ))
        fig_dem.add_hline(y=item["avg_daily_demand"],line_dash="dot",line_color=AMBER,
                          annotation_text="Avg demand",annotation_font_color=AMBER)
        fig_dem.update_layout(**PLOT_LAYOUT, height=260,
            xaxis=dict(showgrid=False,showline=False,tickfont=dict(color=SUB,size=10)),
            yaxis=dict(showgrid=False,showline=False,
                       title=dict(text="Units/day",font=dict(color=SUB,size=10)),
                       tickfont=dict(color=SUB,size=10)),
            legend=dict(font=dict(size=10,color="#8BA4C0"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.12))
        st.plotly_chart(fig_dem, use_container_width=True, config={"displayModeBar":False})
        st.caption("Single exponential smoothing (alpha=0.3). Source: Brown (1959); Holt (1957).")

        # ── AI Explains OR Recommendation ──
        st.markdown('<div style="font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#3A5A7C;margin-top:8px;margin-bottom:6px;">AI Explains the OR Recommendation</div>',unsafe_allow_html=True)
        if st.secrets.get("GROQ_API_KEY", ""):
            if st.button(f"Generate AI Explanation for {item['name']}", key=f"or_explain_{selected_sku}"):
                try:
                    from groq import Groq
                    client = Groq(api_key=st.secrets.get("GROQ_API_KEY",""))
                    prompt = f"""Explain this OR inventory optimization result to a clinical lab manager in plain English.
3 short paragraphs, 120 words max. No OR jargon — use practical language.
ITEM: {item['name']} — {item['category']}
EOQ: {item['eoq']} units (ordering cost: ${item['ordering_cost']}, holding rate: {item['holding_cost_pct']*100:.0f}%)
Safety Stock: {item['safety_stock']} units (95% CSL, z=1.645, lead time: {item['lead_time_days']} days, sigma_d={item['demand_std']:.2f})
Reorder Point: {item['reorder_point']} units
Current Stock: {item['total_stock']} units {'BELOW ROP' if item['total_stock']<item['reorder_point'] else 'OK'}
Cold chain: {'Yes — 2-8C required' if item['is_cold_chain'] else 'No'}
Explain: (1) what EOQ means in practice (2) why safety stock is at this level (3) what action the lab should take now."""
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=300,messages=[{"role":"user","content":prompt}])
                    explanation = resp.choices[0].message.content.strip()
                    st.markdown(f'<div style="background:#0A1628;border:1px solid #1A3050;border-left:3px solid #06B6D4;border-radius:10px;padding:14px 16px;font-size:13px;color:#E8F0FF;line-height:1.8;">{explanation}</div>',unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Groq error: {e}")
        else:
            csl_pct = csl_val * 100
            z_display = f"{z_val:.2f}"
            st.markdown(f"""<div style="background:#0A1628;border:1px solid #1A3050;border-left:3px solid #06B6D4;border-radius:10px;padding:14px 16px;font-size:13px;color:#E8F0FF;line-height:1.8;">
<b>OR Recommendation — {item['name']}</b><br><br>
<b>Why order {item['eoq']} units?</b> The Wilson EOQ formula balances two competing costs:
ordering (${item['ordering_cost']} per order) and holding ({item['holding_cost_pct']*100:.0f}% of unit value per year).
Ordering {item['eoq']} units minimizes the sum of these costs given annual demand of {item['annual_demand']:,} units.
(Harris 1913; Chopra &amp; Meindl 2016 Ch.11)<br><br>
<b>Why {item['safety_stock']} units of safety stock?</b>
Demand variability is sigma_d = {item['demand_std']:.2f} units/day.
Over a {item['lead_time_days']}-day lead time, sigma_LT = {item['demand_std']:.2f} x sqrt({item['lead_time_days']}) = {item['demand_std']*math.sqrt(item['lead_time_days']):.2f}.
At 95% service level z = 1.645, so SS = 1.645 x {item['demand_std']*math.sqrt(item['lead_time_days']):.2f} = {item['safety_stock']} units (ceil).
Cycle Service Level = Phi({z_display}) = {csl_pct:.1f}%.
(Silver, Pyke &amp; Thomas 2017 Ch.7)<br><br>
<b>Current status:</b> {'BELOW ROP: place an emergency order for ' + str(item["eoq"]) + ' units immediately.' if item['total_stock']<item['reorder_point'] else 'Stock is adequate. Place next order when stock reaches ' + str(item["reorder_point"]) + ' units.'}<br><br>
<span style="font-size:11px;color:#5A7A9C;">Add a Groq API key for live AI explanations. | Formulas: EOQ (Harris 1913), CSL (Chopra &amp; Meindl 2016)</span>
</div>""",unsafe_allow_html=True)

    # ── Full Portfolio OR Table ──
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:#E8F0FF;margin-bottom:6px;">Full Portfolio OR Parameters</div>',unsafe_allow_html=True)
    or_table = items_df[["sku_id","name","category","is_cold_chain","avg_daily_demand",
                          "lead_time_days","safety_stock","reorder_point","eoq",
                          "total_stock","cycle_service_level","unit_cost","total_annual_cost"]].copy()
    or_table["is_cold_chain"]       = or_table["is_cold_chain"].map({1:"Cold (2-8C)",0:"Ambient"})
    or_table["cycle_service_level"] = (or_table["cycle_service_level"]*100).round(1).astype(str) + "%"
    or_table["unit_cost"]           = or_table["unit_cost"].map("${:.2f}".format)
    or_table["total_annual_cost"]   = or_table["total_annual_cost"].map("${:,.0f}".format)
    or_table["avg_daily_demand"]    = or_table["avg_daily_demand"].round(2)
    or_table.columns = ["SKU","Name","Category","Storage","Avg Daily Demand",
                         "Lead Time (d)","Safety Stock","ROP","EOQ",
                         "Current Stock","CSL = Phi(z)","Unit Cost","Total Annual Cost"]
    st.dataframe(or_table, use_container_width=True, height=400, hide_index=True)
    st.caption("CSL = Cycle Service Level = Phi(z). Source: Chopra & Meindl (2016) Ch.12; Silver, Pyke & Thomas (2017) Ch.7.")
    st.download_button("Export OR Parameters", or_table.to_csv(index=False), "labtrack_or_params.csv","text/csv")


# ════ TAB 6 — DATA PREVIEW ════
with t6:
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:#E8F0FF;margin-bottom:4px;">Raw Data Preview</div>',unsafe_allow_html=True)
    st.markdown("""<div style="font-size:13px;color:#5A7A9C;margin-bottom:8px;">
    Explore the SQLite tables powering LabTrack. All data is synthetically generated
    (numpy/random seed=42) — no real patient or operational data. OR parameters (EOQ,
    safety stock, ROP, CSL) are fully computed from the formulas, not hardcoded.
    </div>""", unsafe_allow_html=True)

    st.info("All data is synthetic. Site names are inspired by a major US academic medical center network for realism — they do not represent actual operational data from any institution.", icon="ℹ️")

    TABLE_META = {
        "items":{"desc":"Master catalog — 120 SKUs with OR parameters, expiry, cold chain flags (item-level).","icon":"Item",
                 "query":"SELECT * FROM items",
                 "key_cols":["sku_id","name","category","is_cold_chain","exp_status","total_stock","reorder_point","eoq","safety_stock","cycle_service_level","unit_cost","supplier"]},
        "inventory":{"desc":"Site-level positions — stock distributed across 6 sites.","icon":"Site",
                     "query":"SELECT i.*,s.site_name,s.location FROM inventory i JOIN sites s ON i.site_id=s.site_id ORDER BY sku_id",
                     "key_cols":["sku_id","site_name","location","qty","last_updated"]},
        "demand_history":{"desc":"90-day simulated demand (weekday seasonality + normal noise).","icon":"Demand",
                          "query":"SELECT * FROM demand_history ORDER BY sku_id,date",
                          "key_cols":["sku_id","date","demand"]},
        "sites":{"desc":"6 clinical network sites — synthetic, inspired by a major AMC network.","icon":"Map",
                 "query":"SELECT * FROM sites",
                 "key_cols":["site_id","site_name","location","type"]},
        "substitutions":{"desc":"Substitution catalog — up to 3 alternatives per SKU.","icon":"Sub",
                          "query":"SELECT * FROM substitutions",
                          "key_cols":["sku_id","sub_sku_id","sub_name","sub_supplier","compatibility"]},
    }

    tc1,tc2,tc3,tc4,tc5 = st.columns(5)
    table_cols = [tc1,tc2,tc3,tc4,tc5]
    if "active_table" not in st.session_state: st.session_state.active_table = "items"

    for i,(tname,tmeta) in enumerate(TABLE_META.items()):
        is_active = st.session_state.active_table == tname
        table_cols[i].markdown(f"""<div style="background:{'rgba(59,130,246,0.06)' if is_active else 'transparent'};
             border:1px solid {'#3B82F6' if is_active else '#1A2840'};border-radius:10px;
             padding:12px 14px;text-align:center;">
          <div style="font-size:12px;font-weight:700;color:{'#93C5FD' if is_active else '#8BA4C0'};">{tname}</div>
        </div>""",unsafe_allow_html=True)
        if table_cols[i].button(f"Load {tname}", key=f"btn_{tname}", use_container_width=True):
            st.session_state.active_table = tname

    active = st.session_state.active_table
    meta   = TABLE_META[active]
    st.markdown(f'<div style="background:rgba(59,130,246,0.05);border:1px solid rgba(59,130,246,0.2);border-radius:10px;padding:12px 16px;margin:14px 0;"><span style="font-size:14px;font-weight:600;color:#93C5FD;">{active}</span><span style="font-size:13px;color:#5A7A9C;margin-left:12px;">{meta["desc"]}</span></div>',unsafe_allow_html=True)

    full_df = pd.read_sql(meta["query"], conn)
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Rows", f"{len(full_df):,}")
    s2.metric("Columns", len(full_df.columns))
    s3.metric("Memory", f"{full_df.memory_usage(deep=True).sum()/1024:.1f} KB")
    s4.metric("Null Values", int(full_df.isnull().sum().sum()))

    st.markdown("<br>",unsafe_allow_html=True)
    sel_cols = st.multiselect("Columns",options=full_df.columns.tolist(),
                              default=[c for c in meta["key_cols"] if c in full_df.columns],
                              key=f"cols_{active}")
    if not sel_cols: sel_cols = meta["key_cols"]

    search_col, n_rows_col = st.columns([3,1])
    search_term = search_col.text_input("Filter",placeholder="Type to filter...",key=f"search_{active}",label_visibility="collapsed")
    n_rows = n_rows_col.selectbox("Rows",[25,50,100,200,"All"],key=f"nrows_{active}",label_visibility="collapsed")

    display = full_df[sel_cols].copy()
    if search_term:
        mask    = display.apply(lambda col: col.astype(str).str.contains(search_term,case=False,na=False)).any(axis=1)
        display = display[mask]
    display_show = display if n_rows=="All" else display.head(int(n_rows))
    st.dataframe(display_show, use_container_width=True, height=420, hide_index=True)

    col_info, col_export = st.columns([3,1])
    col_info.markdown(f'<div style="font-size:12px;color:#5A7A9C;padding-top:8px;">Showing {len(display_show):,} of {len(display):,} rows</div>',unsafe_allow_html=True)
    col_export.download_button("Export CSV",display.to_csv(index=False),f"labtrack_{active}.csv","text/csv",use_container_width=True)

    with st.expander("SQL Console"):
        st.markdown('<div style="font-size:12px;color:#5A7A9C;margin-bottom:8px;">Tables: items · inventory · demand_history · sites · substitutions</div>',unsafe_allow_html=True)
        sql_query = st.text_area("SQL",value=f"SELECT * FROM {active} LIMIT 10",height=90,key="sql_console",label_visibility="collapsed")
        if st.button("Run Query",key="run_sql"):
            try:
                result_df = pd.read_sql(sql_query,conn)
                st.success(f"{len(result_df)} rows returned")
                st.dataframe(result_df,use_container_width=True,height=280,hide_index=True)
                st.download_button("Export",result_df.to_csv(index=False),"query_result.csv","text/csv")
            except Exception as e:
                st.error(f"SQL Error: {e}")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<p style='font-size:0.74rem;color:#3A5A7C;text-align:center;line-height:1.8;'>
LabTrack v4.0 · Clinical Lab Supply Visibility and OR Inventory Optimization ·
All data synthetic (numpy seed=42) · No real patient or institutional data ·<br>
OR Models: Harris (1913) EOQ · Chopra &amp; Meindl (2016) Safety Stock/CSL · Silver, Pyke &amp; Thomas (2017) ·
Ahmadi et al. (2019) Health Systems 8(2):134-151 ·
Problem context: Kasahun &amp; Kebede (2022) PMC9649967 · CLIA (2023) CDC Supply Chain FAQ ·
Standards: ISO 15189:2022 · CLIA · CLSI ·
Built by Rutwik Satish · MS Engineering Management, Northeastern University
</p>""", unsafe_allow_html=True)
