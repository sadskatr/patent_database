"""
Patent database constants including API endpoints, field mappings, and valid search parameters
"""

# API Endpoints
API_ENDPOINTS = {
    'patent_search': 'https://api.uspto.gov/api/v1/patent/applications/search',
    'patent_details': 'https://api.uspto.gov/api/v1/patent/applications'
}

# Search Types
SEARCH_TYPES = [
    'simple',               # Simple keyword search
    'boolean',              # Boolean search with AND, OR, NOT operators
    'wildcard',             # Wildcard search with *
    'field_specific',       # Field-specific search
    'range',                # Range search
    'filtered',             # Filtered search
    'faceted',              # Faceted search
    'advanced_query',       # Advanced query with raw syntax
    'exact_phrase',         # Exact phrase search with quotes
    'greater_than',         # Greater than or equal to
    'less_than',            # Less than or equal to 
    'boolean_parentheses'   # Boolean with parentheses
]

# Valid fields for different search types
VALID_FIELDS = {
    'simple': ['inventionTitle', 'patentText'],
    'boolean': [
        'inventionTitle', 
        'patentText', 
        'applicationMetaData.applicationStatusDescriptionText',
        'applicationMetaData.applicationNumberText',
        'applicationMetaData.filingDate',
        'inventorNameText',
        'applicationMetaData.firstInventorName',
        'applicationMetaData.firstApplicantName',
        'applicationMetaData.docketNumber',
        'applicationMetaData.examinerNameText',
        'applicationMetaData.applicationTypeLabelName',
        'applicationMetaData.class',
        'applicationMetaData.subclass',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory'
    ],
    'wildcard': ['inventionTitle', 'patentText', 'applicationMetaData.firstApplicantName', 'applicationMetaData.examinerNameText'],
    'field_specific': [
        'inventionTitle',
        'applicationMetaData.applicationNumberText',
        'filingDate',
        'inventorNameText',
        'assigneeEntityName',
        'applicationMetaData.applicationStatusDescriptionText',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory',
        'applicationMetaData.applicationTypeLabelName'
    ],
    'range': [
        'applicationMetaData.filingDate',
        'grantDate',
        'applicationStatusCode',
        'applicationMetaData.applicationConfirmationNumber'
    ],
    'sorting': [
        'applicationMetaData.filingDate',
        'grantDate'
    ],
    'filtered': [
        'applicationMetaData.applicationStatusDescriptionText',
        'applicationMetaData.entityStatusData.smallEntityStatusIndicator',
        'applicationMetaData.applicationTypeLabelName',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory'
    ],
    'faceted': [
        'applicationMetaData.applicationTypeLabelName',
        'applicationMetaData.applicationStatusCode',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory'
    ],
    'advanced_query': [
        'inventionTitle', 
        'patentText', 
        'applicationMetaData.applicationStatusDescriptionText',
        'applicationMetaData.applicationNumberText',
        'applicationMetaData.filingDate',
        'inventorNameText',
        'applicationMetaData.firstInventorName',
        'applicationMetaData.firstApplicantName',
        'applicationMetaData.docketNumber',
        'applicationMetaData.examinerNameText',
        'applicationMetaData.applicationTypeLabelName',
        'applicationMetaData.class',
        'applicationMetaData.subclass',
        'applicationMetaData.applicationConfirmationNumber',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory',
        'applicationMetaData.applicationStatusDate'
    ],
    'exact_phrase': [
        'applicationMetaData.applicationStatusDescriptionText',
        'inventionTitle',
        'patentText'
    ],
    'greater_than': [
        'applicationMetaData.applicationStatusDate',
        'applicationMetaData.filingDate'
    ],
    'less_than': [
        'applicationMetaData.applicationStatusDate',
        'applicationMetaData.filingDate'
    ],
    'boolean_parentheses': [
        'applicationMetaData.applicationTypeLabelName',
        'applicationMetaData.entityStatusData.businessEntityStatusCategory'
    ]
}

# Display names for fields (used in UI)
FIELD_DISPLAY_NAMES = {
    'inventionTitle': 'Invention Title',
    'patentText': 'Patent Text',
    'applicationMetaData.applicationNumberText': 'Application Number',
    'applicationMetaData.filingDate': 'Filing Date',
    'filingDate': 'Filing Date',
    'grantDate': 'Grant Date',
    'inventorNameText': 'Inventor Name',
    'applicationMetaData.firstInventorName': 'First Inventor',
    'applicationMetaData.firstApplicantName': 'Applicant Company',
    'assigneeEntityName': 'Assignee Entity Name',
    'applicationMetaData.applicationStatusDescriptionText': 'Application Status',
    'applicationMetaData.applicationTypeLabelName': 'Application Type',
    'applicationMetaData.entityStatusData.smallEntityStatusIndicator': 'Small Entity Status',
    'applicationMetaData.entityStatusData.businessEntityStatusCategory': 'Business Entity Status',
    'applicationMetaData.applicationStatusCode': 'Application Status Code',
    'applicationMetaData.docketNumber': 'Docket Number',
    'applicationMetaData.examinerNameText': 'Examiner Name',
    'applicationMetaData.class': 'USPTO Class',
    'applicationMetaData.subclass': 'USPTO Subclass'
}

# Boolean Operators
BOOLEAN_OPERATORS = ['AND', 'OR', 'NOT']

# Default pagination values
DEFAULT_PAGINATION = {
    'offset': 0,
    'limit': 50
}

# Maximum results per page (API limit)
MAX_RESULTS_PER_PAGE = 100

# Default sort order
DEFAULT_SORT = [
    {
        'field': 'applicationMetaData.filingDate',
        'order': 'desc'
    }
]

# CSV Export fields
CSV_EXPORT_FIELDS = [
    'inventionTitle',
    'applicationMetaData.applicationNumberText',
    'applicationMetaData.filingDate',
    'grantDate',
    'inventorNameText',
    'assigneeEntityName',
    'applicationMetaData.applicationStatusDescriptionText',
    'applicationMetaData.applicationTypeLabelName'
] 