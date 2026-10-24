"""
config.py
Shared settings for all scripts: folder paths, SEC User-Agent,
study period and the list of companies.
"""
from pathlib import Path

from private_settings import SEC_EMAIL   # kept off GitHub (see .gitignore)

# Folders, relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"
for folder in (RAW, PROCESSED):
    folder.mkdir(parents=True, exist_ok=True)

# SEC requires a User-Agent with name and email
HEADERS = {"User-Agent": f"Candy Mellania Severin {SEC_EMAIL}"}

# Study period
START_DATE = "2015-01-01"
END_DATE = "2025-12-31"

# Companies in the study: ticker -> segment
COMPANIES = {
    # Large US banks
    "JPM": "Large bank", "BAC": "Large bank", "C": "Large bank",
    "WFC": "Large bank", "GS": "Large bank", "MS": "Large bank",
    # Regional banks
    "USB": "Regional bank", "PNC": "Regional bank", "TFC": "Regional bank",
    "MTB": "Regional bank", "FITB": "Regional bank", "KEY": "Regional bank",
    "RF": "Regional bank", "HBAN": "Regional bank", "CFG": "Regional bank",
    # Custody and wealth
    "BK": "Custody and wealth", "STT": "Custody and wealth",
    "NTRS": "Custody and wealth", "SCHW": "Custody and wealth",
    # Consumer credit and cards
    "COF": "Consumer credit", "AXP": "Consumer credit",
    "SYF": "Consumer credit", "ALLY": "Consumer credit",
    # Payments
    "V": "Payments", "MA": "Payments", "PYPL": "Payments", "FI": "Payments",
    "FIS": "Payments", "GPN": "Payments", "XYZ": "Payments",
    # Fintech
    "SOFI": "Fintech", "AFRM": "Fintech", "UPST": "Fintech",
    "HOOD": "Fintech", "COIN": "Fintech",
    # Exchanges and market data
    "ICE": "Exchange and data", "CME": "Exchange and data",
    "NDAQ": "Exchange and data", "SPGI": "Exchange and data",
    "MCO": "Exchange and data",
}