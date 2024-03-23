import sys
from pyglossary import Glossary
from tools.paths import ProjectPaths

pth = ProjectPaths()

# Initialize PyGlossary
Glossary.init()

# Create a Glossary object
glos = Glossary()

# Convert the .ifo file to a Tabfile
glos.convert(
    inputFilename="exporter/share/dpd/dpd.ifo",
    outputFilename="temp/gd_raw.tsv",
    outputFormat="Tabfile", # Specify the output format as Tabfile
    # Optionally, you can specify readOptions or writeOptions as a dict
    writeOptions={"encoding": "utf-8"},
)


