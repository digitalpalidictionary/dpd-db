# exporter/apple_dictionary/

## Purpose & Rationale

The `apple_dictionary/` directory provides a specialized export path for Apple Dictionary Development Kit (DDK) compatible source files. Its rationale is to enable native Dictionary.app integration on macOS by generating properly formatted XML, CSS, and plist files that can be compiled into a `.dictionary` bundle using Apple's Dictionary Development Kit.

## Architectural Logic

This subsystem follows a "Template-to-XML" transformation pattern:

1.  **Rendering:** `apple_dictionary.py` iterates through the database, rendering entries into Apple's Dictionary XML format using a memory-efficient streaming approach.
2.  **Templating:** Uses Jinja2 (`templates/`) to render entry HTML content, maintaining DPD branding and styling.
3.  **Styling:** Incorporates DPD's identity colors and CSS (`templates/dictionary.css`) to ensure consistent branding.
4.  **Metadata:** Generates `Info.plist` with proper bundle identifier (`org.digitalpalidictionary.dpd`) and dictionary metadata.
5.  **Build Process:** The generated source files are compiled on macOS using the Dictionary Development Kit's `build_dict.sh` tool, invoked via Rosetta 2 (`arch -x86_64`) on modern Apple Silicon runners.

## Relationships & Data Flow

- **Source:** Pulls from **db/** models, specifically the `DpdHeadword` table.
- **Tools:** Uses Jinja2 for templating and Python's `xml.etree.ElementTree` for streaming XML generation.
- **Output:** Produces three files in `exporter/share/apple_dictionary/`:
    - `Dictionary.xml` - The main dictionary content in Apple XML format.
    - `Dictionary.css` - Stylesheet for entry rendering.
    - `Info.plist` - Dictionary metadata and bundle information.

## Interface

- **Export:** `uv run python exporter/apple_dictionary/apple_dictionary.py`
- **Output Location:** `exporter/share/apple_dictionary/`

## GitHub Actions Integration

This exporter is integrated into the main automated release workflow defined in `.github/workflows/draft_release.yml`. The process:

1. **Linux Job:** Runs the Python export script to generate the source files (XML, CSS, plist).
2. **macOS Job:** Downloads the source artifacts, clones the Apple Dictionary Development Kit, and compiles the `.dictionary` bundle directly using the DDK's command-line tools.
3. **Release:** Attaches the final `.dictionary.zip` file to the GitHub draft release alongside other formats.

## DPD Styling

The dictionary maintains DPD's visual identity using the primary color scheme:
- Primary: hsl(198, 100%, 50%) - Cyan/blue accent color
- Light backgrounds and dark text optimized for Dictionary.app rendering

## References

- [Apple Dictionary Development Kit Documentation](https://developer.apple.com/)
- See `exporter/kobo/` for similar export pattern using Jinja2 templates
- DPD identity colors defined in `identity/css/dpd-variables.css`
