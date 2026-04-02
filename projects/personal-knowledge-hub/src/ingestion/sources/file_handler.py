"""
File handlers for different document types.
"""

class DOCXHandler:
    """Handler for DOCX files."""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")


class TXTHandler:
    """Handler for plain text files."""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()