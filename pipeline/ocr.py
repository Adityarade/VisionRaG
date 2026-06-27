import pytesseract
from pytesseract import Output
from PIL import Image

def extract_text(image: Image.Image) -> str:
    """
    Extracts text from an image using Tesseract OCR.
    Filters words with confidence > 60 and preserves paragraph structure.
    """
    # In a real environment, you might need to set pytesseract.pytesseract.tesseract_cmd
    # e.g., pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    
    # We use config='--psm 6' (Assume a single uniform block of text) as per prompt,
    # though psm 3 or 4 is usually better for preserving layout. The prompt asked for psm 6.
    try:
        data = pytesseract.image_to_data(image, lang='eng', config='--psm 6', output_type=Output.DICT)
    except pytesseract.TesseractNotFoundError:
        # Fallback if tesseract is not installed
        return "[Tesseract OCR Error: Tesseract is not installed or not in PATH. Please install it.]"
    
    # We will reconstruct text grouping by block_num, par_num, line_num
    # structure: {block_num: {par_num: {line_num: [words]}}}
    document_structure = {}
    
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        conf = float(data['conf'][i])
        text = data['text'][i].strip()
        
        # Filter confidence > 60 and non-empty text
        if conf > 60 and text:
            b = data['block_num'][i]
            p = data['par_num'][i]
            l = data['line_num'][i]
            
            if b not in document_structure:
                document_structure[b] = {}
            if p not in document_structure[b]:
                document_structure[b][p] = {}
            if l not in document_structure[b][p]:
                document_structure[b][p][l] = []
                
            document_structure[b][p][l].append(text)
            
    # Reconstruct string
    paragraphs = []
    for b in sorted(document_structure.keys()):
        for p in sorted(document_structure[b].keys()):
            lines = []
            for l in sorted(document_structure[b][p].keys()):
                lines.append(" ".join(document_structure[b][p][l]))
            if lines:
                paragraphs.append("\n".join(lines))
                
    full_text = "\n\n".join(paragraphs)
    return full_text
