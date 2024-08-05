from pathlib import Path
import sys
from weasyprint import HTML

def makepdf(html):
    """Generate a PDF file from a string of HTML."""
    htmldoc = HTML(string=html, base_url="")
    return htmldoc.write_pdf()

def run():
    """Command runner."""
    infile = ""
    outfile = "temp/pdf_test.pdf"
    html = Path(infile).read_text()
    pdf = makepdf(html)
    Path(outfile).write_bytes(pdf)

if __name__ == "__main__":
    run()
