import requests
import json
import logging
import time
from .utils import validate_search_params, format_results_for_csv
from .constants import API_ENDPOINTS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for rate limiting
MAX_RETRIES = 5
RETRY_DELAY = 0.5  # seconds

def run_operation(data):
    """
    Main function to process operation requests from the frontend
    """
    operation_type = data.get('operation_type')
    params = data.get('params', {})
    
    if operation_type == 'search_patents':
        return search_patents(params)
    elif operation_type == 'export_to_csv':
        return export_to_csv(params)
    elif operation_type == 'test_api_connection':
        return test_api_connection()
    else:
        raise ValueError(f"Unknown operation type: {operation_type}")

def search_patents(params):
    """
    Search patents using the USPTO ODP API
    
    Args:
        params (dict): Parameters for the search including:
            - search_type: Type of search (simple, boolean, wildcard, etc.)
            - query_params: Parameters specific to the search type
            - pagination: Offset and limit
            - sort: Sorting criteria
    
    Returns:
        dict: API response with search results
    """
    # Validate search parameters
    validated_params = validate_search_params(params)
    
    # Construct query based on search type
    query_payload = construct_query_payload(validated_params)
    
    # Log the constructed query for debugging
    logger.info(f"Constructed query payload: {json.dumps(query_payload, indent=2)}")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        logger.error("API key is empty or not set in config.py")
        return {
            'success': False,
            'error': 'API key is empty or not set in config.py',
            'query_payload': query_payload
        }
    
    # Log API key for debugging (mask most of it)
    masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
    logger.info(f"Using API key: {masked_key}")
    
    # Use the same URL as in the working test script
    url = 'https://api.uspto.gov/api/v1/patent/applications/search'
    
    # Set up headers exactly like in test.py
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Log the request details
    logger.info(f"Making API request to: {url}")
    logger.info(f"Headers: {json.dumps({k: (v if k != 'X-API-KEY' else masked_key) for k, v in headers.items()})}")
    logger.info(f"Query payload: {json.dumps(query_payload)}")
    
    # Make direct request similar to test.py
    try:
        logger.info("Sending POST request to USPTO API...")
        response = requests.post(url, headers=headers, json=query_payload)
        
        # Log the response status
        logger.info(f"API response status: {response.status_code}")
        
        # Handle response based on status code
        if response.status_code == 200:
            result = response.json()
            
            # Handle the actual API response structure
            results = result.get('patentFileWrapperDataBag', [])
            result_count = len(results)
            total_count = result.get('count', 0)
            
            # Add a results field for compatibility with frontend
            result['results'] = results
            result['metadata'] = {'total': total_count}
            
            logger.info(f"Retrieved {result_count} results out of {total_count} total")
            
            # If no results and we're searching for a company name, try alternative formats
            if result_count == 0 and query_payload.get("q") and "applicationMetaData.firstNamedApplicant:" in query_payload.get("q", ""):
                logger.info("No results found for company name search. Trying alternative formats...")
                
                # Try alternative search formats
                alternative_results = try_alternative_company_search(query_payload, url, headers)
                
                if alternative_results and alternative_results.get('success'):
                    logger.info(f"Alternative search successful! Found {len(alternative_results.get('data', {}).get('results', []))} results.")
                    return alternative_results
            
            # Always include the query_payload in the response for debugging
            return {
                'success': True,
                'data': result,
                'query_payload': query_payload
            }
        elif response.status_code == 404:
            logger.error("No matching records found or invalid endpoint")
            logger.error(f"Response text: {response.text}")
            return {
                'success': False,
                'error': 'No matching records found or invalid endpoint',
                'query_payload': query_payload
            }
        elif response.status_code == 403:
            logger.error("API Key is invalid or unauthorized")
            logger.error(f"Response text: {response.text}")
            return {
                'success': False,
                'error': 'API Key is invalid or unauthorized',
                'query_payload': query_payload
            }
        else:
            error_message = f"API error: {response.status_code}"
            if hasattr(response, 'text'):
                error_message += f" - {response.text}"
            logger.error(error_message)
            return {
                'success': False,
                'error': error_message,
                'query_payload': query_payload
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            'success': False,
            'error': f"Request error: {str(e)}",
            'query_payload': query_payload
        }
    except Exception as e:
        logger.error(f"Error in search_patents: {str(e)}")
        return {
            'success': False,
            'error': f"Connection error: {str(e)}",
            'query_payload': query_payload
        }

def try_alternative_company_search(original_payload, url, headers):
    """
    Try alternative search formats for company names
    
    Args:
        original_payload (dict): Original search payload
        url (str): API endpoint URL
        headers (dict): Request headers
        
    Returns:
        dict: Search results from the most successful alternative search
    """
    # Extract the company name from the query
    query = original_payload.get("q", "")
    if not query or "applicationMetaData.firstNamedApplicant:" not in query:
        return None
    
    # Extract the company name part
    parts = query.split("applicationMetaData.firstNamedApplicant:")
    if len(parts) <= 1:
        return None
    
    company_part = parts[1].strip()
    
    # If it's part of a complex query, extract just the company name
    if " " in company_part:
        space_pos = company_part.find(" ")
        if space_pos > 0:
            company_part = company_part[:space_pos].strip()
    
    # Remove any surrounding quotes
    if company_part.startswith('"') and company_part.endswith('"'):
        company_part = company_part[1:-1]
    
    logger.info(f"Extracted company name for alternative search: {company_part}")
    
    # Create alternative search formats
    alternative_formats = []
    
    # 1. Try without quotes
    if " " in company_part:
        alternative_formats.append(company_part)
    
    # 2. Try with quotes
    if not (company_part.startswith('"') and company_part.endswith('"')):
        alternative_formats.append(f'"{company_part}"')
    
    # 3. Try with wildcards
    if " " in company_part:
        words = company_part.split()
        if len(words) >= 2:
            # Try just the first word with wildcard
            alternative_formats.append(f"{words[0]}*")
    
    # 4. For company names with LLC, Inc, etc., try different formats
    company_suffixes = ['LLC', 'INC', 'CORP', 'CORPORATION', 'CO', 'LTD', 'LIMITED', 'LP', 'LLP']
    words = company_part.upper().split()
    
    if words and words[-1] in company_suffixes:
        # Try without the suffix
        alternative_formats.append(" ".join(words[:-1]))
        
        # Try with different suffix formats
        if words[-1] == "LLC":
            alternative_formats.append(f"{' '.join(words[:-1])} L.L.C.")
            alternative_formats.append(f"{' '.join(words[:-1])}, LLC")
        elif words[-1] == "INC":
            alternative_formats.append(f"{' '.join(words[:-1])} Inc.")
            alternative_formats.append(f"{' '.join(words[:-1])}, Inc.")
        elif words[-1] == "CORP":
            alternative_formats.append(f"{' '.join(words[:-1])} Corporation")
            alternative_formats.append(f"{' '.join(words[:-1])}, Corp.")
    
    # 5. Try a more general search using assignee field
    alternative_formats.append(f"assigneeName:{company_part}")
    
    # 6. Try a more general search using just the company name without field specification
    if len(words) > 1:
        # For multi-word company names, try just the most distinctive word
        # Usually the first word is the most distinctive for company names
        alternative_formats.append(words[0])
    
    # Try each alternative format
    best_result = None
    max_results = 0
    
    for alt_format in alternative_formats:
        logger.info(f"Trying alternative company name format: {alt_format}")
        
        # Create a new payload with the alternative format
        alt_payload = original_payload.copy()
        
        # Replace the company name in the query
        if "applicationMetaData.firstNamedApplicant:" in query:
            # Special case for assigneeName field
            if alt_format.startswith("assigneeName:"):
                new_query = alt_format
            # Special case for general search without field
            elif not ":" in alt_format:
                new_query = alt_format
            else:
                new_query = query.replace(f"applicationMetaData.firstNamedApplicant:{company_part}", 
                                         f"applicationMetaData.firstNamedApplicant:{alt_format}")
            alt_payload["q"] = new_query
        
        # Make the request
        try:
            logger.info(f"Sending alternative search request with payload: {json.dumps(alt_payload)}")
            response = requests.post(url, headers=headers, json=alt_payload)
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('patentFileWrapperDataBag', [])
                result_count = len(results)
                
                logger.info(f"Alternative search returned {result_count} results")
                
                # Add a results field for compatibility with frontend
                result['results'] = results
                result['metadata'] = {'total': result.get('count', 0)}
                
                # Keep track of the best result
                if result_count > max_results:
                    max_results = result_count
                    best_result = {
                        'success': True,
                        'data': result,
                        'query_payload': alt_payload,
                        'note': f"Used alternative company name format: {alt_format}"
                    }
        except Exception as e:
            logger.error(f"Error in alternative search: {str(e)}")
    
    # If no results found with alternative formats, try a fallback search
    if not best_result:
        logger.info("No results found with alternative formats. Trying fallback search...")
        fallback_result = try_fallback_search(original_payload, url, headers)
        if fallback_result:
            return fallback_result
    
    return best_result

def try_fallback_search(original_payload, url, headers):
    """
    Try a fallback search when all other searches fail
    
    Args:
        original_payload (dict): Original search payload
        url (str): API endpoint URL
        headers (dict): Request headers
        
    Returns:
        dict: Search results from the fallback search
    """
    # Create a fallback payload that searches for patents in the same date range
    # but without the specific company name constraint
    fallback_payload = original_payload.copy()
    
    # Use a wildcard search to get any patents in the date range
    fallback_payload["q"] = "*"
    
    # Keep the date range filters
    # The rangeFilters should already be in the original payload
    
    # Limit results to avoid overwhelming the user
    if "pagination" in fallback_payload:
        fallback_payload["pagination"]["limit"] = 20
    
    logger.info(f"Trying fallback search with payload: {json.dumps(fallback_payload)}")
    
    try:
        response = requests.post(url, headers=headers, json=fallback_payload)
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('patentFileWrapperDataBag', [])
            result_count = len(results)
            
            logger.info(f"Fallback search returned {result_count} results")
            
            # Add a results field for compatibility with frontend
            result['results'] = results
            result['metadata'] = {'total': result.get('count', 0)}
            
            if result_count > 0:
                return {
                    'success': True,
                    'data': result,
                    'query_payload': fallback_payload,
                    'note': "Used fallback search with date range only. The specific company name was not found."
                }
    except Exception as e:
        logger.error(f"Error in fallback search: {str(e)}")
    
    return None

def make_api_request(url, payload, retry_count=0):
    """
    Make an API request with retry logic for rate limiting
    
    Args:
        url (str): API endpoint URL
        payload (dict): Request payload
        retry_count (int): Current retry attempt
        
    Returns:
        dict: API response data or error message
    """
    try:
        api_key = get_api_key()
        # Log API key for debugging (mask most of it)
        if api_key:
            masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
            logger.info(f"Using API key: {masked_key}")
        else:
            logger.error("API key is empty or not set in config.py")
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        # Log the full request details
        logger.info(f"Making API request to: {url}")
        logger.info(f"Headers: {json.dumps({k: (v if k != 'X-API-KEY' else masked_key) for k, v in headers.items()})}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            allow_redirects=True
        )
        
        # Log the response status and headers
        logger.info(f"API response status: {response.status_code}")
        logger.info(f"API response headers: {dict(response.headers)}")
        
        # Handle rate limiting (429 Too Many Requests)
        if response.status_code == 429 and retry_count < MAX_RETRIES:
            retry_count += 1
            wait_time = RETRY_DELAY * retry_count
            logger.warning(f"Rate limit exceeded (429). Retrying in {wait_time} seconds. Attempt {retry_count}/{MAX_RETRIES}")
            time.sleep(wait_time)
            return make_api_request(url, payload, retry_count)
        
        # Check if request was successful
        response.raise_for_status()
        
        result = response.json()
        
        # Log summary of results
        if 'results' in result:
            result_count = len(result.get('results', []))
            total_count = result.get('metadata', {}).get('total', 0)
            logger.info(f"Retrieved {result_count} results out of {total_count} total")
        
        return {
            'success': True,
            'data': result,
            'query_payload': payload  # Return the query for transparency/debugging
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        error_message = "API request failed"
        
        # Try to extract more detailed error info if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('message', error_message)
            except:
                error_message = f"API error: {e.response.status_code} - {e.response.text}"
        
        return {
            'success': False,
            'error': error_message,
            'query_payload': payload
        }

def format_applicant_name_for_search(applicant_name):
    """
    Format an applicant name for search to improve search results
    
    Args:
        applicant_name (str): The raw applicant name
        
    Returns:
        str: Properly formatted applicant name for search
    """
    if not applicant_name:
        return applicant_name
        
    # Trim whitespace
    formatted_name = applicant_name.strip()
    
    # Check if the name already has quotes
    has_quotes = (formatted_name.startswith('"') and formatted_name.endswith('"'))
    
    # If the name contains special characters or spaces and doesn't already have quotes, add them
    if not has_quotes and (' ' in formatted_name or ',' in formatted_name or '.' in formatted_name):
        # For company names with LLC, Inc, Corp, etc., try to handle them specially
        company_suffixes = ['LLC', 'INC', 'CORP', 'CORPORATION', 'CO', 'LTD', 'LIMITED', 'LP', 'LLP']
        
        # Check if the name ends with a common company suffix
        name_parts = formatted_name.upper().split()
        if name_parts and name_parts[-1] in company_suffixes:
            # Try two formats - with and without quotes
            logger.info(f"Company name detected: {formatted_name}")
            
            # Format 1: Use exact phrase with quotes
            formatted_name = f'"{formatted_name}"'
            
            # Log the formatted name
            logger.info(f"Formatted applicant name for search: {formatted_name}")
            return formatted_name
        
        # For other names with spaces, just add quotes
        formatted_name = f'"{formatted_name}"'
    
    # Log the formatted name
    logger.info(f"Formatted applicant name for search: {formatted_name}")
    return formatted_name

def validate_date_range(date_from, date_to):
    """
    Validate and adjust date ranges to ensure they are reasonable
    
    Args:
        date_from (str): Start date in YYYY-MM-DD format
        date_to (str): End date in YYYY-MM-DD format
        
    Returns:
        tuple: Adjusted (date_from, date_to)
    """
    import datetime
    
    # If either date is missing, return as is
    if not date_from or not date_to:
        return date_from, date_to
    
    try:
        # Parse the dates
        from_date = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
        to_date = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Get current date
        today = datetime.date.today()
        
        # Check if end date is in the future
        if to_date > today:
            logger.warning(f"End date {date_to} is in the future. Adjusting to current date.")
            to_date = today
            date_to = today.strftime('%Y-%m-%d')
        
        # Ensure the date range is not too large (USPTO API may have limits)
        max_range = datetime.timedelta(days=365*5)  # 5 years
        if to_date - from_date > max_range:
            logger.warning(f"Date range too large: {date_from} to {date_to}. Adjusting to 5 years.")
            from_date = to_date - max_range
            date_from = from_date.strftime('%Y-%m-%d')
        
        # Ensure from_date is not after to_date
        if from_date > to_date:
            logger.warning(f"Start date {date_from} is after end date {date_to}. Swapping dates.")
            date_from, date_to = date_to, date_from
        
        logger.info(f"Validated date range: {date_from} to {date_to}")
        return date_from, date_to
    
    except ValueError as e:
        # If there's an error parsing the dates, log it and return the original values
        logger.error(f"Error validating date range: {str(e)}")
        return date_from, date_to

def construct_query_payload(params):
    """
    Construct the API query payload based on the search parameters
    
    Args:
        params (dict): Validated search parameters
    
    Returns:
        dict: API query payload
    """
    logger.info(f"Constructing query payload from request data: {json.dumps(params, indent=2)}")
    
    search_type = params.get('search_type')
    query_params = params.get('query_params', {})
    pagination = params.get('pagination', {'offset': 0, 'limit': 50})
    sort = params.get('sort', [{"field": "applicationMetaData.filingDate", "order": "desc"}])
    quick_fields = params.get('quick_fields', {})
    
    # Create the payload with fields exactly matching the order in test.py
    payload = {}
    
    # 1. fields (first in test.py)
    payload["fields"] = params.get('fields', [
        "inventionTitle",
        "applicationNumberText",
        "applicationMetaData",
        "inventorNameText"
    ])
    
    # 2. filters (second in test.py)
    payload["filters"] = params.get('filters', [])
    
    # 3. pagination (third in test.py)
    payload["pagination"] = pagination
    
    # 4. q (query term)
    # Default query handling
    if search_type == 'simple':
        # If term parameter already contains combined fields (from our frontend changes)
        # then we use it directly
        term = query_params.get('term', '')
        logger.info(f"Simple search with term: {term}")
        payload["q"] = term
    elif search_type == 'advanced_query':
        # Use the raw query exactly as provided for advanced queries
        # This allows for direct use of complex query syntax
        raw_query = query_params.get('raw_query', '*')
        logger.info(f"Advanced query: {raw_query}")
        payload["q"] = raw_query
    else:
        # Default to wildcard for other search types
        payload["q"] = '*'
    
    # Check for and handle date range directly from query_params
    date_from = query_params.get('dateFrom', '')
    date_to = query_params.get('dateTo', '')
    
    # Validate and adjust the date range
    if date_from and date_to:
        date_from, date_to = validate_date_range(date_from, date_to)
    
    # Process quick search fields if present - this is now a backup in case frontend doesn't combine them
    quick_search_criteria = []
    
    if quick_fields:
        logger.info(f"Processing quick fields from params: {json.dumps(quick_fields)}")
        
        # Applicant name - use firstNamedApplicant consistently
        if 'applicant_name' in quick_fields and quick_fields['applicant_name']:
            # Format the applicant name for better search results
            formatted_applicant_name = format_applicant_name_for_search(quick_fields['applicant_name'])
            quick_search_criteria.append(f"applicationMetaData.firstNamedApplicant:{formatted_applicant_name}")
            logger.info(f"Added applicant name filter: {formatted_applicant_name}")
        
        # Inventor name - use firstNamedInventor consistently
        if 'inventor_name' in quick_fields and quick_fields['inventor_name']:
            # Format the inventor name for better search results
            formatted_inventor_name = format_applicant_name_for_search(quick_fields['inventor_name'])
            quick_search_criteria.append(f"applicationMetaData.firstNamedInventor:{formatted_inventor_name}")
            logger.info(f"Added inventor name filter: {formatted_inventor_name}")
        
        # Title contains
        if 'title' in quick_fields and quick_fields['title']:
            quick_search_criteria.append(f"inventionTitle:{quick_fields['title']}")
            logger.info(f"Added title filter: {quick_fields['title']}")
    
    # Combine the quick search criteria with the existing query
    if quick_search_criteria:
        quick_query = " AND ".join(quick_search_criteria)
        logger.info(f"Combined quick search criteria: {quick_query}")
        
        if payload["q"] and payload["q"] != '*':
            previous_q = payload["q"]
            payload["q"] = f"({payload['q']}) AND ({quick_query})"
            logger.info(f"Combined with existing query: {previous_q} -> {payload['q']}")
        else:
            payload["q"] = quick_query
            logger.info(f"Set query to quick search criteria: {payload['q']}")
    
    # 5. rangeFilters (fifth in test.py)
    # Add date range if provided (applies to all search types)
    if date_from and date_to:
        logger.info(f"Adding date range filter: {date_from} to {date_to}")
        # Create or update rangeFilters array
        if "rangeFilters" not in payload:
            payload["rangeFilters"] = []
            
        # Add date range filter
        date_range_filter = {
            "field": "applicationMetaData.filingDate",
            "valueFrom": date_from,
            "valueTo": date_to
        }
        
        # Check if we already have a date range filter
        date_filter_exists = False
        for i, rf in enumerate(payload["rangeFilters"]):
            if rf.get("field") == "applicationMetaData.filingDate":
                # Update existing filter
                payload["rangeFilters"][i] = date_range_filter
                date_filter_exists = True
                break
                
        # Add new filter if none exists
        if not date_filter_exists:
            payload["rangeFilters"].append(date_range_filter)
    
    # Handle additional range filters if provided
    if params.get('rangeFilters'):
        if "rangeFilters" not in payload:
            payload["rangeFilters"] = []
        # Add all range filters from params that aren't already covered
        for range_filter in params.get('rangeFilters'):
            # Check if this range filter is already in payload
            if not any(rf['field'] == range_filter['field'] for rf in payload["rangeFilters"]):
                payload["rangeFilters"].append(range_filter)
    
    # 6. sort (sixth in test.py)
    payload["sort"] = sort
    
    # Now handle specific search types
    if search_type == 'boolean':
        # For boolean search, format in the style of "field1:term1 AND field2:term2"
        query_terms = []
        for i, term in enumerate(query_params.get('terms', [])):
            if term.get('field') and term.get('value'):
                # First term has no operator
                if i == 0 or term.get('operator') is None:
                    query_terms.append(f"{term['field']}:{term['value']}")
                else:
                    # Subsequent terms have operators
                    operator = term.get('operator', 'AND').upper()
                    if operator == 'NOT':
                        query_terms.append(f"NOT {term['field']}:{term['value']}")
                    else:
                        query_terms.append(f"{operator} {term['field']}:{term['value']}")
        
        payload["q"] = ' '.join(query_terms) or '*'  # Use * as fallback if no terms
    
    elif search_type == 'wildcard':
        # Format as field:term* for wildcard searches
        field = query_params.get('field', 'inventionTitle')
        value = query_params.get('value', '')
        if value and not value.endswith('*'):
            value = value + '*'  # Ensure it ends with a wildcard
        payload["q"] = f"{field}:{value}"
    
    elif search_type == 'field_specific':
        # Format as field:value for field-specific searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        payload["q"] = f"{field}:{value}"
    
    elif search_type == 'range':
        # For range searches using [TO] syntax in query
        field = query_params.get('field', 'applicationMetaData.filingDate')
        value_from = query_params.get('valueFrom', '')
        value_to = query_params.get('valueTo', '')
        
        if value_from and value_to:
            # Use the query format for range searches
            payload["q"] = f"{field}:[{value_from} TO {value_to}]"
            
            # Create or update rangeFilters
            if "rangeFilters" not in payload:
                payload["rangeFilters"] = []
            
            # Add our range filter
            range_filter = {
                "field": field,
                "valueFrom": value_from,
                "valueTo": value_to
            }
            
            # Check if we need to replace an existing one
            found = False
            for i, existing in enumerate(payload["rangeFilters"]):
                if existing.get("field") == field:
                    payload["rangeFilters"][i] = range_filter
                    found = True
                    break
            
            if not found:
                payload["rangeFilters"].append(range_filter)
    
    elif search_type == 'filtered':
        # For filtered searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        
        if field and value:
            # Use the field:value format for the query
            payload["q"] = f"{field}:{value}"
            
            # Also add as a filter if appropriate
            filter_field = field
            if filter_field in ['applicationMetaData.applicationStatusDescriptionText', 
                              'applicationMetaData.applicationTypeLabelName']:
                # Find or create the appropriate filter
                found = False
                for existing_filter in payload["filters"]:
                    if existing_filter.get("name") == filter_field:
                        if value not in existing_filter["value"]:
                            existing_filter["value"].append(value)
                        found = True
                        break
                
                if not found:
                    payload["filters"].append({
                        "name": filter_field,
                        "value": [value]
                    })
    
    elif search_type == 'faceted':
        # For faceted searches
        facets = query_params.get('facets', [])
        
        if facets:
            # Handle facets in filter section
            for facet in facets:
                field = facet.get('field')
                values = facet.get('values', [])
                
                if field and values:
                    found = False
                    for existing_filter in payload["filters"]:
                        if existing_filter.get("name") == field:
                            for value in values:
                                if value not in existing_filter["value"]:
                                    existing_filter["value"].append(value)
                            found = True
                            break
                    
                    if not found:
                        payload["filters"].append({
                            "name": field,
                            "value": values
                        })
    
    # Add support for advanced query syntax types
    elif search_type == 'exact_phrase':
        # Format as field:"exact phrase" for exact phrase searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        if value:
            # Ensure value is properly quoted
            if not value.startswith('"') and not value.endswith('"'):
                value = f'"{value}"'
            payload["q"] = f"{field}:{value}"
    
    elif search_type == 'greater_than':
        # Format as field:>=value for greater than searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        if field and value:
            payload["q"] = f"{field}:>={value}"
    
    elif search_type == 'less_than':
        # Format as field:<=value for less than searches
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        if field and value:
            payload["q"] = f"{field}:<={value}"
    
    elif search_type == 'boolean_parentheses':
        # Format as field:(term1 OR term2) for boolean with parentheses
        field = query_params.get('field', '')
        value = query_params.get('value', '')
        if field and value:
            payload["q"] = f"{field}:({value})"
    
    # Special case - if we already have a term that includes firstApplicantName, replace it with firstNamedApplicant
    if payload["q"] and "applicationMetaData.firstApplicantName:" in payload["q"]:
        logger.info("Replacing firstApplicantName with firstNamedApplicant in query")
        payload["q"] = payload["q"].replace("applicationMetaData.firstApplicantName:", "applicationMetaData.firstNamedApplicant:")
    
    # Special case - if we have a direct applicant name search, format it properly
    if payload["q"] and "applicationMetaData.firstNamedApplicant:" in payload["q"]:
        # Extract the applicant name part
        parts = payload["q"].split("applicationMetaData.firstNamedApplicant:")
        if len(parts) > 1:
            # Get the part after the field name
            applicant_part = parts[1].strip()
            
            # If it's at the beginning of a complex query, extract just the name part
            if " " in applicant_part:
                # Find where the next condition starts
                space_pos = applicant_part.find(" ")
                if space_pos > 0:
                    name_part = applicant_part[:space_pos]
                    rest_part = applicant_part[space_pos:]
                    
                    # Format just the name part
                    if not (name_part.startswith('"') and name_part.endswith('"')) and " " in name_part:
                        formatted_name = format_applicant_name_for_search(name_part)
                        # Reconstruct the query
                        payload["q"] = f"applicationMetaData.firstNamedApplicant:{formatted_name}{rest_part}"
                        logger.info(f"Reformatted applicant name in query: {payload['q']}")
            else:
                # It's a simple query with just the applicant name
                if not (applicant_part.startswith('"') and applicant_part.endswith('"')) and " " in applicant_part:
                    formatted_name = format_applicant_name_for_search(applicant_part)
                    # Reconstruct the query
                    payload["q"] = f"applicationMetaData.firstNamedApplicant:{formatted_name}"
                    logger.info(f"Reformatted applicant name in query: {payload['q']}")
    
    # Final validation - ensure query term exists
    if "q" not in payload or not payload["q"]:
        payload["q"] = "*"  # Default to wildcard search if no query term
    
    logger.info(f"Constructed API payload: {json.dumps(payload, indent=2)}")
    return payload

def export_to_csv(params):
    """
    Export search results to CSV format
    
    Args:
        params (dict): Parameters including search results to export
    
    Returns:
        dict: Success flag and CSV data
    """
    # If results are provided directly, format them
    if 'results' in params:
        results = params.get('results', [])
        csv_data = format_results_for_csv(results)
        
        return {
            'success': True,
            'csv_data': csv_data
        }
    
    # Otherwise, perform a search and then format results
    elif 'search_params' in params:
        search_params = params.get('search_params', {})
        
        # Set limit to maximum to get more results for export
        if 'pagination' in search_params:
            search_params['pagination']['limit'] = 100
        
        # Run the search
        search_result = search_patents(search_params)
        
        if search_result.get('success'):
            # Get results from the patentFileWrapperDataBag field
            data = search_result.get('data', {})
            
            # Use the results field we added in search_patents for compatibility
            results = data.get('results', [])
            
            # If no results field (older version), try patentFileWrapperDataBag directly
            if not results and 'patentFileWrapperDataBag' in data:
                results = data.get('patentFileWrapperDataBag', [])
                
            csv_data = format_results_for_csv(results)
            
            return {
                'success': True,
                'csv_data': csv_data
            }
        else:
            return {
                'success': False,
                'error': search_result.get('error', 'Failed to retrieve results for export')
            }
    else:
        return {
            'success': False,
            'error': 'No results or search parameters provided for export'
        }

def get_api_key():
    """Get API key from config"""
    from config import DevConfig
    return getattr(DevConfig, 'ODP_API_KEY', '')

def test_api_connection():
    """
    Test function to check if the USPTO API is reachable
    
    Returns:
        dict: Status of the API connection
    """
    try:
        api_key = get_api_key()
        
        if not api_key:
            return {
                'success': False,
                'error': 'API key is not set in config.py'
            }
        
        # Use the exact same URL and test payload from the working test script
        test_url = 'https://api.uspto.gov/api/v1/patent/applications/search'
        
        # Use a simple, known-working test payload
        test_payload = {
            "q": "applicationMetaData.applicationTypeLabelName:Utility",
            "filters": [
                {
                    "name": "applicationMetaData.applicationStatusDescriptionText",
                    "value": ["Patented Case"]
                }
            ],
            "pagination": {
                "offset": 0,
                "limit": 1
            },
            "fields": [
                "applicationNumberText",
                "applicationMetaData.filingDate"
            ]
        }
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Testing API connection to: {test_url}")
        logger.info(f"Test payload: {json.dumps(test_payload)}")
        
        # Make a POST request to match how the working example does it
        response = requests.post(
            test_url,
            headers=headers,
            json=test_payload,
            allow_redirects=True,
            timeout=30
        )
        
        status = response.status_code
        logger.info(f"Test connection status: {status}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if status == 200:
            # Try to parse the response
            try:
                result = response.json()
                
                # Handle the actual API response structure
                results = result.get('patentFileWrapperDataBag', [])
                result_count = len(results)
                total_count = result.get('count', 0)
                
                logger.info(f"API test successful: {total_count} total results, {result_count} returned")
                
                return {
                    'success': True,
                    'message': f'API connection successful. Found {total_count} matching patents.'
                }
            except Exception as e:
                logger.error(f"Error parsing API response: {str(e)}")
                return {
                    'success': True,
                    'message': 'API connection successful, but error parsing response'
                }
        elif status == 403:
            logger.error(f"API Key is invalid or unauthorized: {response.text}")
            return {
                'success': False,
                'error': 'API Key is invalid or unauthorized'
            }
        elif status == 404:
            logger.error(f"No matching records found or invalid endpoint: {response.text}")
            return {
                'success': False,
                'error': 'No matching records found or invalid endpoint'
            }
        else:
            error_message = f"API error: {status}"
            if hasattr(response, 'text'):
                error_message += f" - {response.text[:200]}"
            logger.error(error_message)
            return {
                'success': False,
                'error': error_message
            }
    
    except Exception as e:
        logger.error(f"Error testing API connection: {str(e)}")
        return {
            'success': False,
            'error': f"Connection error: {str(e)}"
        }
