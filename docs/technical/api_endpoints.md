# API Endpoints

Here are the API endpoints available in the DPD Web App (`exporter/webapp`). The application is built using FastAPI.

The website is online here [https://www.dpdict.net/](https://www.dpdict.net/)

All API endpoints can be tested here [https://www.dpdict.net/docs](https://www.dpdict.net/docs)

## Licensing

DPD dictionary data is released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — attribution required, non-commercial use only, derivatives shared alike.

Every endpoint that returns dictionary data (`/search_json`, `/search_html`, `/gd`) sends the licence as an RFC 8288 link header:

```
Link: <https://creativecommons.org/licenses/by-nc-sa/4.0/>; rel="license"; title="CC BY-NC-SA 4.0"
```

`/search_json` additionally ends its response body with a `license` object.

The rendered entries themselves end with a small visible notice — the four Creative Commons marks (inlined SVG, so they survive offline in GoldenDict) followed by the attribution, linking to the deed. It is appended to the results HTML rather than to a page footer, so it travels with the data into GoldenDict, the JSON `dpd_html` field and any third-party embed of the fragment. A "no results" page carries no notice.

Tipiṭaka translations (`/tt_search`), bold definitions (`/bd_search`) and audio (`/audio/{headword}`) are licensed separately and carry none of the above.

## Web Pages

### Home Page
- **URL:** `/`
- **Method:** `GET`
- **Description:** Renders the main home page of the dictionary.
- **Parameters:** None
- **Response:** HTML (`home.html`)

### Bold Definitions Page
- **URL:** `/bd`
- **Method:** `GET`
- **Description:** Renders the landing page for Bold Definitions search.
- **Parameters:** None
- **Response:** HTML (`home.html`)

## Search Endpoints

### HTML Search
- **URL:** `/search_html`
- **Method:** `GET`
- **Description:** Performs a dictionary search and returns the results rendered within the home page template. Used for direct page loads with search results.
- **Parameters:**
    - `q` (str): The search query (Pali word or English term).
- **Response:** HTML (`home.html` populated with results)

### JSON Search
- **URL:** `/search_json`
- **Method:** `GET`
- **Description:** Main search route for the website's dynamic search functionality. Returns the rendered HTML fragments for the results and summary.
- **Parameters:**
    - `q` (str): The search query.
- **Response:** JSON
    ```json
    {
        "summary_html": "...",
        "dpd_html": "...",
        "license": {
            "name": "CC BY-NC-SA 4.0",
            "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "attribution": "Digital Pāḷi Dictionary by Bodhirasa Bhikkhu — dpdict.net",
            "note": "Non-commercial use only. Derivatives must be shared alike."
        }
    }
    ```

### GoldenDict / MDict Search
- **URL:** `/gd`
- **Method:** `GET`
- **Description:** Returns a simplified HTML version of the search results, optimized for external dictionary applications like GoldenDict and MDict.
- **Parameters:**
    - `search` (str): The search query.
- **Response:** HTML (`home_simple.html`)

Check out this guide for setting up the API in [GoldenDict](https://digitalpalidictionary.github.io/webapp/api_goldendict/) or [DictTango on Android](https://digitalpalidictionary.github.io/webapp/api_dicttango/)

### Bold Definitions Search
- **URL:** `/bd_search`
- **Method:** `GET`
- **Description:** Search route specifically for "Bold Definitions" (commentarial definitions).
- **Parameters:**
    - `q1` (str): Primary search query.
    - `q2` (str): Secondary search query (context or additional filter).
    - `option` (str): Search option/mode.
- **Response:** HTML (`bold_definitions.html` with results)

### Tipiṭaka Translations Search
- **URL:** `/tt_search`
- **Method:** `GET`
- **Description:** Searches through Tipiṭaka translations.
- **Parameters:**
    - `q` (str): Search query.
    - `book` (str): Specific book to search in, or "all".
    - `lang` (str): Language/Column to search ("Pāḷi" or others).
- **Response:** JSON
    ```json
    {
        "total": 100,
        "results": [
            {
                "id": 1,
                "pali": "...",
                "eng": "...",
                "book": "...",
                "table": "..."
            }
        ]
    }
    ```

## Resources

### Audio
- **URL:** `/audio/{headword}`
- **Method:** `GET`
- **Description:** Serves the audio file for a specific headword with byte-range support.
- **Parameters:**
    - `headword` (path parameter): The headword to retrieve audio for.
    - `gender` (query parameter, optional): Preferred voice gender ("male" or "female"). Defaults to "male".
- **Response:** Audio file (`audio/mpeg`). Returns `200 OK` for full file, `206 Partial Content` for range requests, or `404 Not Found` if the headword does not exist.

**Examples:**
- `GET /audio/buddha?gender=male`
- `GET /audio/buddha?gender=female`
- `GET /audio/dhamma?gender=male`
- `GET /audio/dhamma?gender=female`
- `GET /audio/saṅgha?gender=male`
- `GET /audio/saṅgha?gender=female`

