# Tipitaka Translation Database

Download the latest translation database from the [Pa Auk Society website](https://dhamma.paauksociety.org/index.php?dir=Root%2FTipitaka).

## One-Shot Command

**Linux / Windows (with wget):**
```bash
cd resources/tipitaka_translation_data/ && wget https://dhamma.paauksociety.org/Root/Tipitaka/tipitaka-translation-data.db.zip && unzip -o tipitaka-translation-data.db.zip && rm tipitaka-translation-data.db.zip && cd ../..
```

**Mac users (or if wget not available):**
```bash
cd resources/tipitaka_translation_data/ && curl -L -O https://dhamma.paauksociety.org/Root/Tipitaka/tipitaka-translation-data.db.zip && unzip -o tipitaka-translation-data.db.zip && rm tipitaka-translation-data.db.zip && cd ../..
```

> **Note for Mac users**: `curl` is built-in on macOS, so use the curl command above. 
> If you prefer `wget`, install it first with `brew install wget`.

## Manual Download

Alternatively, download manually from: https://dhamma.paauksociety.org/Root/Tipitaka/tipitaka-translation-data.db.zip

Then extract to this directory.
