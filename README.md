

# Reddit Persona Analyzer 

A Python-based analyzer that creates a detailed **user persona** from a Reddit profile by scraping public posts and comments using the Reddit API. It uses natural language processing to detect demographics, personality traits, writing style, and community interests.


##  Features

- Scrapes posts and comments from any public Reddit user profile.
- Uses NLP to infer:
  - Gender, age, location, occupation
  - Communication style (formal, casual, technical, emoji usage)
  - Personality traits (analytical, social, helpful, opinionated)
- Identifies top subreddit interests.
- Provides citation links for every extracted trait.
- Outputs a clean `.txt` file as a complete persona report.


##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/reddit_persona_analyzer.git
cd reddit_persona_analyzer
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```
### 3. Install Required Packages
```bash
pip install praw textblob spacy
```
### 4. Download spaCy Language Model
```bash
python -m spacy download en_core_web_sm
```

##  Reddit API Setup

### 1. Create a Reddit App

1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **“Create Another App”**
3. Choose **`script`** as the app type
4. Fill in the fields:
   - **Name**: `Reddit Persona Analyzer`
   - **Redirect URI**: `http://localhost:8080`
5. Click **“Create app”**
6. Copy your **Client ID** (under the app name) and **Client Secret**


### 2. Create ```config.py```
Create a file named ```config.py``` in your project root:

```python
REDDIT_CLIENT_ID = 'your_client_id_here'
REDDIT_CLIENT_SECRET = 'your_client_secret_here'
REDDIT_USER_AGENT = 'PersonaAnalyzer/1.0'
```

## Run the Analyzer
Make sure your virtual environment is activated and run:

```bash
python reddit_analyzer.py
```
### Example Input:
```ruby
Enter Reddit user profile URL: https://www.reddit.com/user/spez/
```
### Output:
A file like ```spez_persona_20250714_123456.txt``` will be created in your project folder containing the full analysis.


## Project Structure
```graphql
reddit_persona_analyzer/
│
├── reddit_analyzer.py        
├── config.py                 
├── venv/                     
├── README.md                 
├── username_persona_*.txt    
```
