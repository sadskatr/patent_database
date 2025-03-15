# Patent Database Search Tool

A Flask-based web application for searching patents using the USPTO Open Data Portal API. This tool provides a user-friendly interface to search, filter, and explore patent data.

## Features

- Simple, Boolean, and Field-specific search types
- Advanced filtering capabilities
- Modern, responsive UI
- JSON response viewer
- Export results to Excel
- Detailed patent information display

## Installation

1. Clone this repository:
```bash
git clone https://github.com/sadskatr/patent_database.git
cd patent_database
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your USPTO API key in `config.py`

## Usage

1. Start the development server:
```bash
python run.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000/patent_database
```

## Search Types

- **Simple Search**: Quick keyword search across patent data
- **Boolean Search**: Combine multiple search terms with AND, OR, NOT operators
- **Field-specific Search**: Search in specific fields of patent data

## Development

This project follows a simple Flask Blueprint structure:

```
patent_database/
├── run.py              # Standalone development server
├── config.py           # Tool configuration
└── tool/               # Main tool directory
    ├── __init__.py     # Blueprint setup
    ├── routes.py       # Route handlers
    ├── operations.py   # Core business logic
    └── templates/      # Templates
        ├── base.html   # Base template
        └── patent_database/
            └── index.html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 