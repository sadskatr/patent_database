import requests
import json

# Base API URL for USPTO Patent Search
BASE_URL = "https://api.uspto.gov/api/v1/patent/applications/search"

def get_api_key():
    """Get API key from config"""
    from config import DevConfig
    return getattr(DevConfig, 'ODP_API_KEY', '')
# Function to perform API search
def perform_search(api_key, payload):
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    print("\n[INFO] Sending POST request to USPTO API...")
    response = requests.post(BASE_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print("\n[SUCCESS] Search successful! Here are the results:")
        print(json.dumps(response.json(), indent=2))  # Pretty-print JSON response
    elif response.status_code == 404:
        print("\n[ERROR] No matching records found. Try refining your search.")
    elif response.status_code == 403:
        print("\n[ERROR] API Key is invalid or unauthorized.")
    else:
        print("\n[ERROR] Failed with status:", response.status_code)
        print(response.text)  # Print error response

# User inputs API Key
api_key = get_api_key()
    
# Test payload - exact copy from test.py
test_payload = {
    "fields": [
        "inventionTitle",
        "applicationNumberText",
        "applicationMetaData",
        "inventorNameText"
    ],
    "filters": [
        {
        "name": "applicationMetaData.applicationTypeLabelName",
        "value": [
            "Utility"
        ]
        }
    ],
    "pagination": {
        "limit": 50,
        "offset": 0
    },
    "q": "antenna",
    "rangeFilters": [
        {
        "field": "applicationMetaData.filingDate",
        "valueFrom": "2020-03-09",
        "valueTo": "2025-03-09"
        }
    ],
    "sort": [
        {
        "field": "applicationMetaData.filingDate",
        "order": "desc"
        }
    ]
}

# Perform the test search
perform_search(api_key, test_payload) 