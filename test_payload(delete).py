print("Starting test...")
try:
    import sys
    print("Imported sys")
    import json
    print("Imported json")
    from patent_database.operations import construct_query_payload
    print("Imported construct_query_payload")
    
    # Test with the example search parameters
    test_params = {
        'search_type': 'simple',
        'query_params': {
            'term': '(antenna) AND (applicationMetaData.firstNamedApplicant:OWN LLC)',
            'dateFrom': '2022-03-13',
            'dateTo': '2025-03-13'
        },
        'pagination': {
            'offset': 0,
            'limit': 50
        },
        'sort': [
            {
                'field': 'applicationMetaData.filingDate',
                'order': 'desc'
            }
        ]
    }

    # Construct the payload
    payload = construct_query_payload(test_params)

    # Print the result
    print("Constructed payload:")
    print(json.dumps(payload, indent=2))

    # Compare with expected payload
    expected_payload = {
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
        "q": "(antenna) AND (applicationMetaData.firstNamedApplicant:OWN LLC)",
        "rangeFilters": [
            {
                "field": "applicationMetaData.filingDate",
                "valueFrom": "2022-03-13",
                "valueTo": "2025-03-13"
            }
        ],
        "sort": [
            {
                "field": "applicationMetaData.filingDate",
                "order": "desc"
            }
        ]
    }

    print("\nChecking if payload matches expected format...")
    # Check if the payload matches the expected format
    matches = True
    for key in expected_payload:
        if key not in payload:
            print(f"Missing key: {key}")
            matches = False
        elif key == "rangeFilters":
            # Special check for rangeFilters
            if len(payload[key]) != len(expected_payload[key]):
                print(f"Different number of rangeFilters: {len(payload[key])} vs {len(expected_payload[key])}")
                matches = False
            else:
                for i, rf in enumerate(expected_payload[key]):
                    for field in rf:
                        if field not in payload[key][i] or payload[key][i][field] != rf[field]:
                            print(f"Mismatch in rangeFilters[{i}][{field}]: {payload[key][i].get(field)} vs {rf[field]}")
                            matches = False
        elif payload[key] != expected_payload[key]:
            print(f"Mismatch in {key}: {payload[key]} vs {expected_payload[key]}")
            matches = False

    if matches:
        print("\nSUCCESS: Payload matches expected format!")
    else:
        print("\nFAILURE: Payload does not match expected format.")

    print("Test completed successfully!")
except Exception as e:
    print(f"Error: {str(e)}") 