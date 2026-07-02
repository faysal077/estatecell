from pypdf import PdfReader, PdfWriter
import io

def extract_pages(pdf_path, from_page, to_page):

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    total_pages = len(reader.pages)

    if from_page < 1:
        from_page = 1

    if to_page > total_pages:
        to_page = total_pages

    for page_num in range(from_page - 1, to_page):
        writer.add_page(reader.pages[page_num])

    output = io.BytesIO()

    writer.write(output)

    return output.getvalue()