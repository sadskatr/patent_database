import requests
import json
import time  # Import time for delay

# Base API URL for USPTO Patent Search
BASE_URL = "https://api.uspto.gov/api/v1/patent/applications/search"

def get_api_key():
    """Get API key from config"""
    from config import DevConfig
    return getattr(DevConfig, 'ODP_API_KEY', '')

# Toggle verbose output
verbose = True  
delay_seconds = 1  # Adjust delay to avoid rate limiting

def perform_search(api_key, payload, test_name):
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # Print payload for specific tests to help debug
    if test_name in ["dipole-or-test", "dipole-test", "dipole-field-test", "final-fixed-query"]:
        print(f"\n[DEBUG] Payload for {test_name}:")
        print(json.dumps(payload, indent=2))

    response = requests.post(BASE_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        result_count = len(result.get('patentFileWrapperDataBag', []))
        total_count = result.get('count', 0)
        status_icon = "✅" if result_count > 0 else "❌"
        print(f"[{test_name}] {status_icon} {result_count}/{total_count} results")

        if verbose and result_count > 0:
            print(json.dumps(result['patentFileWrapperDataBag'][0], indent=2))
    elif response.status_code == 429:
        print(f"[{test_name}] ❌ Error 429 (Rate Limit Exceeded) - Retrying after {delay_seconds}s...")
        time.sleep(delay_seconds)
        perform_search(api_key, payload, test_name)  # Retry after delay
    else:
        print(f"[{test_name}] ❌ Error {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")

# User inputs API Key
api_key = get_api_key()

# Base payload template
base_payload = {
    "fields": ["inventionTitle", "applicationNumberText", "applicationMetaData", "inventorNameText"],
    "pagination": {"limit": 50, "offset": 0},
    "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}]
}

# Test queries
test_payloads = {
    "1-simple-field": {**base_payload, "q": "applicationMetaData.entityStatusData.businessEntityStatusCategory:Small"},
    "2-or-with-parentheses": {**base_payload, "q": "applicationMetaData.applicationTypeLabelName:(Design OR Plant)"},
    "3-and-with-quotes": {**base_payload, "q": "applicationMetaData.applicationStatusDescriptionText:\"Patented Case\" AND applicationMetaData.entityStatusData.businessEntityStatusCategory:Micro"},
    "4-wildcard-asterisk": {**base_payload, "q": "applicationMetaData.firstApplicantName:Technolog*"},
    "5-wildcard-question-mark": {**base_payload, "q": "applicationMetaData.examinerNameText:ANDERS?N"},
    "6-greater-than-equal": {**base_payload, "q": "applicationMetaData.applicationStatusDate:>=2024-02-20"},
    "7-range-query": {**base_payload, "q": "applicationMetaData.applicationConfirmationNumber:[2700 TO 2710]"},
    "8-date-range": {**base_payload, "q": "applicationMetaData.filingDate:[2024-01-01 TO 2024-08-30]"},
    "9-boolean-or": {**base_payload, "q": "applicationMetaData.applicationStatusDescriptionText:\"Patented Case\" OR applicationMetaData.entityStatusData.businessEntityStatusCategory:Micro"}
}

d = {
    "fields": [
        "inventionTitle",
        "applicationNumberText",
        "applicationMetaData",
        "inventorNameText"
    ],
    "filters": [],
    "pagination": {
        "limit": 50,
        "offset": 0
    },
    "rangeFilters": [
        {
        "field": "applicationMetaData.filingDate",
        "valueFrom": "2023-03-14",
        "valueTo": "2025-03-14"
        }
    ],
    "sort": [
        {
        "field": "applicationMetaData.filingDate",
        "order": "desc"
        }
    ],
    "q": "(antenna) AND (applicationMetaData.firstNamedApplicant:OWN LLC)"
    }

dipole = {
    "fields": [
        "inventionTitle",
        "applicationNumberText",
        "applicationMetaData",
        "inventorNameText"
    ],
    "filters": [],
    "pagination": {
        "limit": 50,
        "offset": 0
    },
    "q": "applicationMetaData.firstApplicantName:galtronics",
    # "q": "applicationMetaData.firstApplicantName:Galtronics AND antenna",
    "rangeFilters": [
        {
        "field": "applicationMetaData.filingDate",
        "valueFrom": "2000-03-12",
        "valueTo": "2025-03-12"
        }
    ],
    "sort": [
        {
        "field": "applicationMetaData.filingDate",
        "order": "desc"
        }
    ]
    }

dipole_or_antenna_payload = {
    "fields": ["inventionTitle", "applicationNumberText", "applicationMetaData", "inventorNameText"],
    "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
    "pagination": {"limit": 50, "offset": 0},
    # "q": "dipole OR antenna",
    "q": "(antenna) AND (applicationMetaData.firstNamedApplicant:OWN LLC)",# Basic OR syntax
    "rangeFilters": [
        {
            "field": "applicationMetaData.filingDate",
            "valueFrom": "2023-01-01",
            "valueTo": "2025-03-11"
        }
    ],
    "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}]
}
print("\n=== Running dipole Search ===")
perform_search(api_key, dipole, "dipole")


# 2. Simple search just for dipole
dipole_only_payload = {
    "fields": ["inventionTitle", "applicationNumberText", "applicationMetaData", "inventorNameText"],
    "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
    "pagination": {"limit": 50, "offset": 0},
    "q": "dipole",  # Just search for dipole
    "rangeFilters": [
        {
            "field": "applicationMetaData.filingDate",
            "valueFrom": "2023-01-01",
            "valueTo": "2025-03-11"
        }
    ],
    "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}]
}

# 3. Field-specific syntax for invention title (doesn't work - 404 error)
dipole_title_field_payload = {
    "fields": ["inventionTitle", "applicationNumberText", "applicationMetaData", "inventorNameText"],
    "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
    "pagination": {"limit": 50, "offset": 0},
    "q": "inventionTitle:dipole",  # Field-specific syntax
    "rangeFilters": [
        {
            "field": "applicationMetaData.filingDate",
            "valueFrom": "2023-01-01",
            "valueTo": "2025-03-11"
        }
    ],
    "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}]
}

# FINAL FIXED QUERY - This is the corrected version that should work
final_fixed_query = {
    "fields": ["inventionTitle", "applicationNumberText", "applicationMetaData", "inventorNameText"],
    "filters": [{"name": "applicationMetaData.applicationTypeLabelName", "value": ["Utility"]}],
    "pagination": {"limit": 50, "offset": 0},
    # Simple query without field specificity works best
    "q": "dipole",
    "rangeFilters": [
        {
            "field": "applicationMetaData.filingDate",
            "valueFrom": "2023-01-01",
            "valueTo": "2025-03-11"
        }
    ],
    "sort": [{"field": "applicationMetaData.filingDate", "order": "desc"}]
}

# Uncomment to run the original tests
# print("\n=== Running original test payloads ===")
# for test_name, payload in test_payloads.items():
#     time.sleep(delay_seconds)  # Add delay between each request
#     perform_search(api_key, payload, test_name)

# Uncomment to run the dipole tests
# print("\n=== Running dipole OR search tests ===")
# perform_search(api_key, dipole_or_antenna_payload, "dipole-or-test")
# perform_search(api_key, dipole_only_payload, "dipole-test")
# perform_search(api_key, dipole_title_field_payload, "dipole-field-test")

# Run only the final fixed query
# print("\n=== Running FINAL FIXED QUERY ===")
# perform_search(api_key, final_fixed_query, "final-fixed-query")

# New test payload for comprehensive search
comprehensive_search_payload = {
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
    "q": "antenna OR RET",
    "rangeFilters": [
        {
            "field": "applicationMetaData.filingDate",
            "valueFrom": "2023-01-11",
            "valueTo": "2025-03-11"
        }
    ],
    "sort": [
        {
            "field": "applicationMetaData.filingDate",
            "order": "desc"
        }
    ]
}

# Run comprehensive search
# print("\n=== Running Comprehensive Search ===")
# perform_search(api_key, comprehensive_search_payload, "comprehensive-search")
