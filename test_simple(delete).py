import requests
import json
import os
from datetime import datetime

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
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("\n[SUCCESS] Search successful!")
            
            # Parse the JSON response
            data = response.json()
            
            # Get the number of results - handle the actual API response structure
            results = data.get('patentFileWrapperDataBag', [])
            results_count = len(results)
            total_count = data.get('count', 0)
            print(f"Retrieved {results_count} results out of {total_count} total")
            
            # Save results to a file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"patent_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n[INFO] Full results saved to {filename}")
            
            # Print a summary of the first 5 results
            if results_count > 0:
                print("\n[SUMMARY] First 5 patents:")
                for i, result in enumerate(results[:5]):
                    app_data = result.get('applicationMetaData', {})
                    app_number = result.get('applicationNumberText', 'N/A')
                    print(f"\n{i+1}. {app_data.get('inventionTitle', 'No title')}")
                    print(f"   Application #: {app_number}")
                    print(f"   Filing Date: {app_data.get('filingDate', 'N/A')}")
                    print(f"   Inventor: {app_data.get('firstInventorName', 'N/A')}")
                    print(f"   Status: {app_data.get('applicationStatusDescriptionText', 'N/A')}")
            
            return data
            
        elif response.status_code == 404:
            print("\n[ERROR] No matching records found. Try refining your search.")
        elif response.status_code == 403:
            print("\n[ERROR] API Key is invalid or unauthorized.")
        else:
            print("\n[ERROR] Failed with status:", response.status_code)
            print(response.text)  # Print error response
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Connection error. Please check your internet connection.")
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out. The USPTO API might be experiencing high load.")
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request error: {str(e)}")
    except json.JSONDecodeError:
        print("\n[ERROR] Failed to parse API response as JSON.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")

# User inputs API Key
api_key = get_api_key()

# Test payload - search for antenna patents
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
    "q": "applicationMetaData.firstApplicantName:galtronics",
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
if __name__ == "__main__":
    print("\n===== USPTO Patent Search Tool - Test Script =====")
    print(f"Searching for: 'antenna' patents filed between 2020-03-09 and 2025-03-09")
    perform_search(api_key, test_payload) 