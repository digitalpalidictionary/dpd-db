# Local Server Setup

This guide provides step-by-step instructions on how to set up the Digital Pāḷi Dictionary (DPD) database for use as a local server. This is useful for running the web application locally or providing an API for other dictionary software like GoldenDict or DictTango.

## Prerequisites

- **uv**: This project uses [astral uv](https://github.com/astral-sh/uv) for dependency management and Python version control. Install it if you haven't already:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Python**: `uv` will automatically manage and install the required Python version for you when you run the setup commands below. There is no need to install Python manually.

## Step-by-Step Instructions

### 1. Download the Repository

Clone the DPD database repository from GitHub (using `--depth 1` for a faster download):

```bash
git clone --depth 1 https://github.com/digitalpalidictionary/dpd-db.git
cd dpd-db
```

### 2. Setup Dependencies

Use `uv` to sync the environment and install all necessary dependencies:

```bash
uv sync
```

### 3. Download the Databases

You need to download three main database files: the primary DPD database, the audio database, and the translations database.

#### 3.1. Primary DPD Database
Download and extract the latest primary database:

```bash
wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.bz2 | tar -xj
```

#### 3.2. Audio Database
Download the audio database using the provided script:

```bash
uv run python audio/db_release_download.py
```

#### 3.3. Translations Database
Download the Tipiṭaka translations database:

```bash
uv run python resources/tipitaka_translation_db/download_and_unzip_db.py
```

### 4. Run the Server

Start the local server using `uvicorn`. By default, this will start the server on port 8080.

```bash
uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080
```

### 5. Access the Web Application

Once the server is running, you can open your web browser and navigate to:

[http://localhost:8080](http://localhost:8080)

You should now see the DPD web application running locally!

## Notes

- **Host**: Using `--host 0.0.0.0` allows the server to be accessible from other devices on your local network. Use `--host 127.0.0.1` if you want it only accessible from your own machine.
- **Port**: You can change the port by modifying the `--port` value.
- **Background Execution**: To run the server in the background, you can use `nohup` or `screen`/`tmux`.
