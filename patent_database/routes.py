from flask import render_template, jsonify, request, current_app, send_file
from . import patent_database_bp
from .operations import run_operation, search_patents, export_to_csv
from .constants import SEARCH_TYPES, VALID_FIELDS, FIELD_DISPLAY_NAMES, BOOLEAN_OPERATORS, API_ENDPOINTS
import logging
import json
import io
import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@patent_database_bp.route('/')
def index():
    """Render the main index page"""
    # Get API key from config
    from .operations import get_api_key
    api_key = get_api_key()
    
    return render_template('patent_database/index.html', 
                           tool_name=current_app.config.get('TOOL_NAME', 'Patent Search Tool'),
                           search_types=SEARCH_TYPES,
                           valid_fields=VALID_FIELDS,
                           field_display_names=FIELD_DISPLAY_NAMES,
                           boolean_operators=BOOLEAN_OPERATORS,
                           max_results=current_app.config.get('MAX_RESULTS_PER_PAGE', 100),
                           api_key=api_key)  # Pass the API key to the template

@patent_database_bp.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for patent search"""
    try:
        data = request.get_json()
        logger.info(f"Search request received: {json.dumps(data, indent=2)}")
        
        result = search_patents(data)
        
        # Log search results summary
        if result.get('success'):
            result_count = len(result.get('data', {}).get('results', []))
            total_count = result.get('data', {}).get('metadata', {}).get('total', 0)
            logger.info(f"Search returned {result_count} of {total_count} total results")
            
            # Check if there's a note from alternative search
            if 'note' in result:
                logger.info(f"Alternative search note: {result['note']}")
        else:
            logger.error(f"Search failed: {result.get('error')}")
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Exception in search API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@patent_database_bp.route('/api/export-csv', methods=['POST'])
def api_export_csv():
    """API endpoint to export search results to CSV"""
    try:
        data = request.get_json()
        logger.info("CSV export request received")
        
        result = export_to_csv(data)
        
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error')}), 400
        
        # Create an in-memory file-like object
        buffer = io.StringIO(result.get('csv_data', ''))
        
        # Set headers for file download
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patent_search_results_{now}.csv"
        
        return send_file(buffer, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype='text/csv')
    except Exception as e:
        logger.exception(f"Exception in export CSV API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@patent_database_bp.route('/api/valid-fields/<search_type>')
def api_valid_fields(search_type):
    """API endpoint to get valid fields for a search type"""
    if search_type in VALID_FIELDS:
        fields = VALID_FIELDS[search_type]
        result = [{'field': field, 'display_name': FIELD_DISPLAY_NAMES.get(field, field)} 
                  for field in fields]
        return jsonify({'success': True, 'fields': result})
    else:
        return jsonify({'success': False, 'error': f"Invalid search type: {search_type}"}), 400

@patent_database_bp.route('/api/preview-query', methods=['POST'])
def api_preview_query():
    """API endpoint to preview the constructed query without executing it"""
    try:
        from .operations import construct_query_payload, get_api_key
        data = request.get_json()
        
        if not data:
            logger.error("No data received in preview-query request")
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        logger.info(f"Preview query request received: {json.dumps(data, indent=2)}")
        
        # Validate the parameters
        from .utils import validate_search_params
        try:
            validated_params = validate_search_params(data)
            logger.info(f"Parameters validated successfully: {json.dumps(validated_params, indent=2)}")
        except Exception as e:
            logger.error(f"Parameter validation failed: {str(e)}")
            return jsonify({'success': False, 'error': f'Parameter validation failed: {str(e)}'}), 400
        
        # Construct the query payload
        try:
            query_payload = construct_query_payload(validated_params)
            logger.info(f"Query payload constructed: {json.dumps(query_payload, indent=2)}")
        except Exception as e:
            logger.error(f"Query payload construction failed: {str(e)}")
            return jsonify({'success': False, 'error': f'Query payload construction failed: {str(e)}'}), 400
        
        # Get the API key (masked for security)
        try:
            api_key = get_api_key()
            if not api_key:
                logger.warning("API key is not set")
                masked_key = "[NOT SET]"
            else:
                masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
        except Exception as e:
            logger.error(f"Failed to get API key: {str(e)}")
            masked_key = "[ERROR]"
        
        # Get the endpoint URL
        endpoint_url = API_ENDPOINTS.get('patent_search', 'https://api.uspto.gov/api/v1/patent/applications/search')
        
        # Create a preview object with complete details
        preview_data = {
            'endpoint_url': endpoint_url,
            'headers': {
                'X-API-KEY': masked_key,
                'Content-Type': 'application/json'
            },
            'method': 'POST',
            'query_payload': query_payload
        }
        
        return jsonify({
            'success': True,
            'preview_data': preview_data
        })
    except Exception as e:
        error_message = str(e)
        logger.exception(f"Exception in preview query API: {error_message}")
        return jsonify({'success': False, 'error': error_message}), 500

@patent_database_bp.route('/api/test-connection', methods=['GET'])
def api_test_connection():
    """API endpoint to test connection to USPTO API"""
    try:
        from .operations import test_api_connection
        result = test_api_connection()
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Exception in test connection API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@patent_database_bp.route('/api/find-similar', methods=['POST'])
def api_find_similar():
    """API endpoint to find similar patents"""
    try:
        data = request.get_json()
        logger.info(f"Similar patent request received: {json.dumps(data, indent=2)}")
        
        patent_number = data.get('patent_number')
        title = data.get('title')
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        # Remove common noise words and keep words longer than 3 chars
        stop_words = ['and', 'the', 'for', 'with', 'from', 'that', 'this', 'not']
        key_terms = [
            word for word in re.findall(r'\w+', title.lower())
            if len(word) > 3 and word not in stop_words
        ][:3]  # Take up to 3 terms
        
        # Create the search query
        query = f"inventionTitle:({' OR '.join(key_terms)})"
        
        # If we have a patent number, exclude it from the results
        if patent_number:
            query += f" AND NOT applicationMetaData.applicationNumberText:{patent_number}"
        
        # Create search parameters
        search_params = {
            'search_type': 'advanced_query',
            'query_params': {
                'raw_query': query
            },
            'pagination': {
                'offset': 0,
                'limit': 20
            },
            'sort': [
                {
                    'field': 'applicationMetaData.filingDate',
                    'order': 'desc'
                }
            ]
        }
        
        # Perform the search
        from .operations import search_patents
        result = search_patents(search_params)
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Exception in find similar patents API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
