import os

from pypdf import PdfReader


# ============================================================
# EXTRACT TEXT FROM SUPPORTED FILES
# ============================================================

def extract_text(file_path):
    if not file_path:
        raise ValueError("File path is required.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, extension = os.path.splitext(file_path)
    extension = extension.lower().strip('.')

    if extension == 'pdf':
        reader = PdfReader(file_path)

        if not reader.pages:
            return ''

        text = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            except Exception as e:
                print(f"PDF PAGE {page_number} ERROR:", e)

        final_text = '\n'.join(text)

        # Some valid PDFs expose text poorly through pypdf. Try a second
        # PDF engine before treating the document as image-only.
        if not final_text.strip():
            try:
                import pymupdf

                document = pymupdf.open(file_path)
                final_text = '\n'.join(
                    page.get_text()
                    for page in document
                )
                document.close()
            except Exception as e:
                print(f"PDF FALLBACK EXTRACTION ERROR: {e}")

    elif extension == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            final_text = f.read()

    else:
        raise ValueError(f"Unsupported file type: {extension}")

    final_text = final_text.replace('\x00', '')
    final_text = '\n'.join(
        line.strip()
        for line in final_text.splitlines()
        if line.strip()
    )

    return final_text.strip()
