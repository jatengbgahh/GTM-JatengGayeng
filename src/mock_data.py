# mock_data.py
# This file contains mock data for Branches and WOKs until real data sources are defined.

MOCK_BRANCHES = [
    {"id": "branch_1", "name": "MAGELANG"},
    {"id": "branch_2", "name": "PEKALONGAN"},
    {"id": "branch_3", "name": "PURWOKERTO"},
    {"id": "branch_4", "name": "SEMARANG"},
    {"id": "branch_5", "name": "SURAKARTA"},
    {"id": "branch_6", "name": "YOGYAKARTA"},
]

MOCK_WOKS = [
    {"id": "wok_1", "branch_id": "1", "name": "KEBUMEN"},
    {"id": "wok_2", "branch_id": "1", "name": "MAGELANG TEMANGGUNG"},
    {"id": "wok_3", "branch_id": "2", "name": "BATANG"},
    {"id": "wok_4", "branch_id": "2", "name": "PEMALANG PURBALINGGA"},
    {"id": "wok_5", "branch_id": "2", "name": "TEGAL BREBES"},
    {"id": "wok_6", "branch_id": "3", "name": "CILACAP BANYUMAS"},
    {"id": "wok_7", "branch_id": "3", "name": "WONOSOBO BANJARNEGARA"},
    {"id": "wok_8", "branch_id": "4", "name": "DEMAK"},
    {"id": "wok_9", "branch_id": "4", "name": "JEPARA KUDUS-PATI"},
    {"id": "wok_10", "branch_id": "4", "name": "SEMARANG 1"},
    {"id": "wok_11", "branch_id": "4", "name": "SEMARANG 2"},
    {"id": "wok_12", "branch_id": "5", "name": "BOYOLALI"},
    {"id": "wok_13", "branch_id": "5", "name": "SRAGEN"},
    {"id": "wok_14", "branch_id": "5", "name": "SURAKARTA"},
    {"id": "wok_15", "branch_id": "6", "name": "YOGYA 1"},
    {"id": "wok_16", "branch_id": "6", "name": "YOGYA 2"},
]

def get_branches():
    return MOCK_BRANCHES

def get_woks(branch_id=None):
    if branch_id is None:
        return MOCK_WOKS
    
    # Extract numeric part from "branch_1" to match "1" in WOKs
    numeric_id = branch_id.replace("branch_", "") if isinstance(branch_id, str) else str(branch_id)
    return [wok for wok in MOCK_WOKS if wok.get("branch_id") == numeric_id]
