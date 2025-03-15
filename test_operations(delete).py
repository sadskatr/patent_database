import json
from patent_database.operations import search_patents, test_api_connection

def test_search():
    """Test the search_patents function with the updated structure"""
    print("\n===== Testing search_patents function =====")
    
    # Create a simple search params object
    search_params = {
        'search_type': 'simple',
        'query_params': {
            'term': 'antenna'
        },
        'pagination': {
            'offset': 0,
            'limit': 5
        },
        'fields': [
            'inventionTitle',
            'applicationNumberText',
            'applicationMetaData',
            'inventorNameText'
        ]
    }
    
    # Call the search_patents function
    result = search_patents(search_params)
    
    # Check if the search was successful
    if result.get('success'):
        print("Search successful!")
        
        # Get the data from the result
        data = result.get('data', {})
        
        # Check if we have results
        results = data.get('results', [])
        result_count = len(results)
        total_count = data.get('metadata', {}).get('total', 0)
        
        print(f"Retrieved {result_count} results out of {total_count} total")
        
        # Print the first result
        if result_count > 0:
            first_result = results[0]
            app_data = first_result.get('applicationMetaData', {})
            
            print("\nFirst result:")
            print(f"Title: {app_data.get('inventionTitle', 'No title')}")
            print(f"Application #: {first_result.get('applicationNumberText', 'N/A')}")
            print(f"Filing Date: {app_data.get('filingDate', 'N/A')}")
            print(f"Inventor: {app_data.get('firstInventorName', 'N/A')}")
    else:
        print(f"Search failed: {result.get('error')}")

def test_api_connection_function():
    """Test the test_api_connection function with the updated structure"""
    print("\n===== Testing test_api_connection function =====")
    
    # Call the test_api_connection function
    result = test_api_connection()
    
    # Check if the test was successful
    if result.get('success'):
        print(f"API connection test successful: {result.get('message')}")
    else:
        print(f"API connection test failed: {result.get('error')}")

if __name__ == "__main__":
    print("===== Testing Patent Database Operations =====")
    
    # Test the API connection
    test_api_connection_function()
    
    # Test the search function
    test_search() 