# 🐾 Petlibro

Live brand intelligence dashboard for monitoring Petlibro mentions across the web.

## Features

- **Live Data Collection**: Monitors mentions from Google News, Reddit, YouTube, and blogs
- **Sentiment Analysis**: Automated sentiment classification with confidence scoring
- **30-Day Archive**: Persistent mention history for trend tracking
- **Interactive Dashboard**: Real-time analytics and conversation drivers
- **Multi-Brand Support**: Track Petlibro alongside competitors (Catit, Sure Petcare, Whistle)
- **Green & Cream UI**: Beautiful, accessibility-focused design

## Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Petlibro.git
   cd Petlibro
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app locally:
   ```bash
   streamlit run Petlibro.py
   ```

### Streamlit Cloud Deployment

1. Push your repository to GitHub

2. Go to [Streamlit Cloud](https://streamlit.io/cloud)

3. Click "New app" and select your repository

4. Configure the main file as `Petlibro.py`

5. (Optional) Add YouTube API key to Streamlit Secrets:
   - In the Streamlit Cloud settings, add:
     ```
     YOUTUBE_API_KEY = "your-api-key-here"
     ```

## Configuration

### Environment Variables

Optional environment variables for enhanced functionality:

- `YOUTUBE_API_KEY`: YouTube Data API v3 key for video search (optional)

### Streamlit Secrets

For secure storage of API keys on Streamlit Cloud, add them to your app's secrets in the Streamlit Cloud dashboard:

```
YOUTUBE_API_KEY = "your-youtube-api-key"
```

## Data

Mentions are stored in `data/mentions.json` (created automatically). The 30-day archive persists locally.

## Project Structure

```
Petlibro/
├── Petlibro.py          # Main Streamlit app
├── archive.py           # 30-day mention history management
├── collectors.py        # Data collection from multiple sources
├── requirements.txt     # Python dependencies
├── .streamlit/
│   └── config.toml      # Streamlit configuration
└── data/
    └── mentions.json    # Archive of mentions (auto-created)
```

## Technologies

- **Streamlit**: Web framework for data apps
- **Pandas**: Data manipulation and analysis
- **Altair**: Declarative visualization
- **Feedparser**: RSS feed parsing
- **TextBlob**: NLP sentiment analysis
- **Requests**: HTTP library for API calls

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
