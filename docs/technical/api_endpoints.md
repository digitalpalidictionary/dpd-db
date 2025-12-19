# API Endpoints

Here are the API endpoints available in the DPD Web App (`exporter/webapp`). The application is built using FastAPI.

The website is online here [https://www.dpdict.net/](https://www.dpdict.net/)

All API endpoints can be tested here [https://www.dpdict.net/docs](https://www.dpdict.net/docs)

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
        "dpd_html": "..."
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
- **Description:** Serves the audio file for a specific headword.
- **Parameters:**
    - `headword` (path parameter): The headword to retrieve audio for.
    - `gender` (query parameter, optional): Preferred voice gender ("male" or "female"). Defaults to "male".
- **Response:** Audio file (`audio/mpeg`) or 404 if not found.

