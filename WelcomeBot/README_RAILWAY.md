# Railway Deployment Files

**Procfile**
Defines the start command for Railway:

    start: python PaymentsScript.py

Adjust the filename if your main script is different.

**requirements.txt**
Pinned Python dependencies for your bot:

- aiogram 3.x
- python-dotenv
- tzdata (makes ZoneInfo work on slim Linux images)

**.env.example**
Template for your environment variables.  
Copy to `.env`, fill the real values, and add the variables in Railway's UI as well.

---
## Quick deploy steps

1. Push your project (including these files) to GitHub.  
2. On Railway → New Project → Deploy from GitHub.  
3. Add `WELCOME_BOT_TOKEN` and `MY_ID` in the *Variables* tab.  
4. Click *Deploy*. Railway will build the image, install requirements and run the bot.

If your bot file is called something else (e.g., `bot.py`), edit `Procfile` accordingly.
