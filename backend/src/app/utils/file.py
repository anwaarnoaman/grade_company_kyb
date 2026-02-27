import magic

def detect_file_type(file_path: str) -> str:
    """
    Detect common file types using python-magic
    Returns: excel, csv, pdf, word, text, html, json, image, other
    """
    try:
        mime_type = magic.from_file(file_path, mime=True)
    except Exception as e:
        print("Failed to detect MIME type:", e)
        return 'other'

    # Map MIME types to categories
    if mime_type in ['application/vnd.ms-excel', 
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        return 'excel'
    elif mime_type == 'text/csv':
        return 'csv'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type in ['application/msword', 
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'word'
    elif mime_type.startswith('text/plain'):
        return 'text'
    elif mime_type.startswith('text/html'):
        return 'html'
    elif mime_type == 'application/json':
        return 'json'
    elif mime_type.startswith('image/'):
        return 'image'  # Handles jpg, png, gif, bmp, webp, etc.
    else:
        return 'other'