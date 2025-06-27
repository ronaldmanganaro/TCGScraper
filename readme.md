# TCGScraper

TCGScraper is a comprehensive toolkit for Magic: The Gathering and Pokémon sellers, providing inventory management, price tracking, repricing, and data conversion tools. The project includes a Streamlit web app, backend services, and browser extension components.

## Features

- **Streamlit Web App**:  
  - Inventory management and repricing tools
  - Booster box and precon EV calculators
  - Pokémon price tracker
  - TCGPlayer order PDF extraction and printing
  - ManaBox CSV converter
  - User authentication and preferences
  - Dark and light mode support

- **Backend**:  
  - Node.js/Express server for API and ECS integration
  - Database scripts and Docker support

- **Browser Extension**:  
  - Chrome extension for scraping and interacting with TCGPlayer

## Project Structure

```
app/           # Python backend scripts and utilities
backend/       # Node.js backend server
db/            # Database scripts and data
docker/        # Dockerfiles and compose scripts
extension/     # Browser extension source
streamlit/     # Streamlit web app, pages, and functions
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js (for backend)
- Docker (optional, for containerized setup)
- Chrome (for extension and Playwright scraping)

### Setup

1. **Clone the repository**
   ```
   git clone <repo-url>
   cd TCGScraper
   ```

2. **Install Python dependencies**
   ```
   cd streamlit
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies (optional)**
   ```
   cd ../backend
   npm install
   ```

4. **Run the Streamlit app**
   ```
   cd ../streamlit
   streamlit run pages/app.py
   ```

5. **(Optional) Run with Docker**
   ```
   docker-compose up streamlit -d
   ```

### Usage

- Access the web app at `http://localhost:8501`
- Use the sidebar to navigate between tools (Repricer, EV Tools, ManaBox, etc.)
- Upload your inventory CSVs, analyze prices, and export results
- Use the browser extension for TCGPlayer scraping

### Theming

- Switch between dark and light mode in the user preferences dialog (⚙️ button)
- The app uses Streamlit's recommended theme colors for a native look

## Contributing

Pull requests and feature suggestions are welcome! Please open an issue or join our Discord for support.

## License

MIT License

# Start runner
C:\Users\MrCool\Documents\Repos\actions-runner\run.cmd

# Set the env
[System.Environment]::SetEnvironmentVariable("VOLUME_PATH", "C:\Users\WinMax2\Documents\Repos\postgres\data")
[System.Environment]::SetEnvironmentVariable("VOLUME_PATH", "C:\Users\MrCool\Documents\Repos\postgres\data")

# pgadmin server config dir
/var/lib/pgadmin/storage/ronaldmanganaro_gmail.com/

# NPM
npm install

# To Do
Need to save creds using github actions

# Boto3
instructions for how to setup credentials
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

# Scryfall Api
https://scryfall.com/docs/syntax
