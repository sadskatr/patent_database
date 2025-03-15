"""
Utility functions for the patent database tool
"""
import csv
import io
import json
import logging
from .constants import VALID_FIELDS, SEARCH_TYPES, MAX_RESULTS_PER_PAGE, CSV_EXPORT_FIELDS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_search_params(params):
    """
    Validate and sanitize search parameters
    
    Args:
        params (dict): Search parameters
    
    Returns:
        dict: Validated parameters
    """
    # Clone the params to avoid modifying the input
    validated = params.copy()
    
    # Verify search type
    search_type = validated.get('search_type')
    if not search_type or search_type not in SEARCH_TYPES:
        logger.warning(f"Invalid search type: {search_type}. Defaulting to 'simple'.")
        validated['search_type'] = 'simple'
    
    # Check query parameters based on search type
    query_params = validated.get('query_params', {})
    
    if search_type == 'simple':
        # Simple search needs a term, but we're going to be lenient about field validation
        # since it might include custom fields or combinations from quick search
        if not query_params.get('term'):
            logger.warning("No search term provided for simple search")
        else:
            # Log the term we're using
            logger.info(f"Using simple search term: {query_params.get('term')}")
    
    elif search_type == 'advanced_query':
        # Advanced query - we don't validate the raw_query since it may contain arbitrary field names
        if not query_params.get('raw_query'):
            logger.warning("No raw query provided for advanced query search")
        else:
            # Log the raw query we're using
            logger.info(f"Using advanced raw query: {query_params.get('raw_query')}")
    
    elif search_type == 'boolean':
        # Boolean search needs at least one term with field and value
        terms = query_params.get('terms', [])
        if not terms:
            logger.warning("No terms provided for boolean search")
        else:
            # Filter out invalid terms
            valid_terms = []
            for term in terms:
                if term.get('field') and term.get('value'):
                    # Be more lenient about field names - just log warnings but include the term
                    if term['field'] not in VALID_FIELDS['boolean']:
                        logger.warning(f"Potentially invalid field for boolean search: {term['field']} - including anyway")
                    valid_terms.append(term)
            
            if not valid_terms and terms:
                logger.warning("No valid terms found for boolean search")
            
            query_params['terms'] = valid_terms
    
    elif search_type in ['wildcard', 'field_specific']:
        # These search types need a field and value
        field = query_params.get('field')
        value = query_params.get('value')
        
        if not field or not value:
            logger.warning(f"Missing field or value for {search_type} search")
        elif field not in VALID_FIELDS.get(search_type, []):
            logger.warning(f"Potentially invalid field for {search_type} search: {field} - including anyway")
    
    elif search_type == 'range':
        # Range search needs a field, valueFrom and valueTo
        field = query_params.get('field')
        value_from = query_params.get('valueFrom')
        value_to = query_params.get('valueTo')
        
        if not field or not value_from or not value_to:
            logger.warning("Missing field, valueFrom, or valueTo for range search")
        elif field not in VALID_FIELDS.get('range', []):
            logger.warning(f"Potentially invalid field for range search: {field} - including anyway")
    
    elif search_type == 'filtered':
        # Filtered search needs a field and value
        field = query_params.get('field')
        value = query_params.get('value')
        
        if not field or not value:
            logger.warning("Missing field or value for filtered search")
        elif field not in VALID_FIELDS.get('filtered', []):
            logger.warning(f"Potentially invalid field for filtered search: {field} - including anyway")
    
    elif search_type == 'faceted':
        # Faceted search needs at least one facet
        facets = query_params.get('facets', [])
        if not facets:
            logger.warning("No facets provided for faceted search")
        else:
            # Be more lenient - just log warnings and include all facets
            for facet in facets:
                if facet not in VALID_FIELDS.get('faceted', []):
                    logger.warning(f"Potentially invalid facet: {facet} - including anyway")
    
    # Validate pagination
    pagination = validated.get('pagination', {})
    limit = pagination.get('limit', 50)
    offset = pagination.get('offset', 0)
    
    # Ensure limit is within allowed range
    if limit > MAX_RESULTS_PER_PAGE:
        logger.warning(f"Limit exceeds maximum allowed ({MAX_RESULTS_PER_PAGE}). Adjusting.")
        pagination['limit'] = MAX_RESULTS_PER_PAGE
    
    # Ensure offset is non-negative
    if offset < 0:
        logger.warning("Negative offset provided. Setting to 0.")
        pagination['offset'] = 0
    
    validated['query_params'] = query_params
    validated['pagination'] = pagination
    
    # Handle date range parameters in query_params
    if 'dateFrom' in query_params and 'dateTo' in query_params:
        logger.info(f"Date range parameters found: {query_params['dateFrom']} to {query_params['dateTo']}")
    
    return validated

def format_results_for_csv(results):
    """
    Format search results for CSV export
    
    Args:
        results (list): List of patent search results from patentFileWrapperDataBag
    
    Returns:
        str: CSV formatted data
    """
    if not results:
        return ""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    header = [field.split('.')[-1] if '.' in field else field for field in CSV_EXPORT_FIELDS]
    writer.writerow(header)
    
    # Write data rows
    for patent in results:
        row = []
        for field in CSV_EXPORT_FIELDS:
            # Handle nested fields
            if '.' in field:
                parts = field.split('.')
                value = patent
                
                # Special case for applicationMetaData fields
                if parts[0] == 'applicationMetaData':
                    value = patent.get('applicationMetaData', {})
                    for part in parts[1:]:
                        if isinstance(value, dict) and part in value:
                            value = value.get(part)
                        else:
                            value = ""
                            break
                else:
                    # Handle other nested fields
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value.get(part)
                        else:
                            value = ""
                            break
            else:
                # Handle top-level fields
                value = patent.get(field, "")
                
            row.append(value)
        writer.writerow(row)
    
    return output.getvalue()

def log_debug_info(message, data=None):
    """
    Log debug information
    
    Args:
        message (str): Debug message
        data (any, optional): Data to log
    """
    logger.info(message)
    if data:
        if isinstance(data, (dict, list)):
            logger.info(json.dumps(data, indent=2))
        else:
            logger.info(str(data))

def get_nested_value(obj, path, default=""):
    """
    Get a value from a nested object using a dot-separated path
    
    Args:
        obj (dict): The object to retrieve from
        path (str): Dot-separated path to the value
        default (any, optional): Default value if not found
    
    Returns:
        any: The value at the path or default if not found
    """
    parts = path.split('.')
    current = obj
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current 