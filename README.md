<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-AI%20Powered-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/Gradio-Web%20UI-FF7C00?style=for-the-badge&logo=gradio&logoColor=white" alt="Gradio"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🤖 Nitesh-GPT</h1>
<h3 align="center">Your Personal AI Chatbot — Powered by Google Gemini</h3>

<p align="center">
  <em>A portfolio-style AI assistant that answers questions about you, captures leads, and sends you real-time notifications — all through a sleek web chat interface.</em>
</p>

---

## 📖 What Is This?

**Nitesh-GPT** is a personal AI chatbot that acts as *you*. It reads your LinkedIn profile (PDF) and a summary text file, then uses **Google Gemini AI** to answer visitors' questions about your professional background, skills, and experience — as if they were chatting with you directly.

Think of it as an AI-powered portfolio assistant that works 24/7.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI-Powered Chat** | Uses Google Gemini (via OpenAI-compatible API) to generate intelligent, context-aware responses |
| 📄 **Resume Ingestion** | Automatically reads your LinkedIn PDF + summary text to build a rich knowledge base |
| 💬 **Web Chat Interface** | Beautiful, responsive chat UI powered by Gradio — works on desktop & mobile |
| 📧 **Lead Capture** | When visitors want to connect, the AI captures their email and sends you a notification |
| ❓ **Unknown Question Logging** | Questions the AI can't answer are logged and sent to you for review |
| 📱 **Push Notifications** | Real-time phone alerts via Pushover when leads are captured or unknown questions are asked |
| 🔒 **Secure by Design** | API keys stored in `.env` (excluded from git) — never exposed publicly |
| 🛡️ **Error Handling** | Graceful error messages on API failures (rate limits, network issues) instead of crashes |
| 📝 **Fully Commented Code** | Every line is explained — perfect for learning and customization |

---

## 🏗️ Project Structure

```
nitesh-gpt/
│
├── app.py              # 🚀 Main application — AI chatbot logic + Gradio web server
├── requirements.txt    # 📦 Python package dependencies
├── .env                # 🔑 Secret API keys (local only — NOT pushed to git)
├── .gitignore          # 🚫 Files excluded from version control
├── README.md           # 📖 This file — project documentation
│
└── me/                 # 👤 Your personal data folder
    ├── linkedin.pdf    # 📄 Your LinkedIn profile exported as PDF
    ├── summary.txt     # ✍️ Your bio, achievements, blog posts, resume text
    └── config.json     # ⚙️ (Optional) Custom configurations
```

---

## 🔧 Prerequisites

Before you begin, make sure you have the following:

| Requirement | Details |
|-------------|---------|
| **Python 3.10+** | [Download Python](https://www.python.org/downloads/) |
| **Google API Key** | Free from [Google AI Studio](https://aistudio.google.com/apikey) |
| **Git** | [Download Git](https://git-scm.com/downloads) |
| **Pushover Account** *(optional)* | For phone notifications — [pushover.net](https://pushover.net) |

---

## 🚀 Getting Started — Step by Step

### Step 1: Clone the Repository

```bash
git clone https://github.com/Nits02/nitesh-gpt.git
cd nitesh-gpt/nitesh-gpt
```

---

### Step 2: Create a Virtual Environment

It's best practice to use a virtual environment to keep dependencies isolated.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

> ✅ You should see `(.venv)` at the start of your terminal prompt.

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the following packages:

| Package | Purpose |
|---------|---------|
| `python-dotenv` | Loads API keys from `.env` file |
| `openai` | Talks to Google Gemini via OpenAI-compatible API |
| `pypdf` | Extracts text from your LinkedIn PDF |
| `requests` | Sends HTTP requests (for Pushover notifications) |
| `gradio` | Creates the web-based chat interface |

---

### Step 4: Get Your Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

---

### Step 5: Create Your `.env` File

Create a file named `.env` in the project root:

```bash
touch .env
```

Add your API keys:

```env
GOOGLE_API_KEY=your-google-api-key-here
PUSHOVER_TOKEN=your-pushover-token-here
PUSHOVER_USER=your-pushover-user-key-here
```

> ⚠️ **Important:** The `.env` file is listed in `.gitignore` and will **NOT** be pushed to GitHub. Your keys stay local and safe.

> 💡 **Note:** Pushover keys are **optional**. The app works without them — notifications will just be printed to the console instead.

---

### Step 6: Add Your Personal Data

#### 📄 LinkedIn PDF
1. Go to your [LinkedIn Profile](https://www.linkedin.com/in/)
2. Click **"More" → "Save to PDF"**
3. Save the downloaded file as `me/linkedin.pdf`

#### ✍️ Summary Text
Edit `me/summary.txt` with your personal information:
- Professional bio / summary
- Key achievements and impact
- Skills and certifications
- Blog posts or articles
- Anything you want the AI to know about you

> 💡 **Tip:** The more detailed your `summary.txt` is, the better the AI will answer questions about you!

---

### Step 7: Run the Application

```bash
python app.py
```

You should see output like:

```
* Running on local URL:  http://127.0.0.1:7860
```

---

### Step 8: Start Chatting! 🎉

Open your browser and go to:

👉 **http://127.0.0.1:7860**

Try asking questions like:
- *"Tell me about Nitesh's experience"*
- *"What are your key skills?"*
- *"What cloud platforms have you worked with?"*
- *"I'd like to hire you, my email is example@email.com"*

---

## 🔄 How It Works — Under the Hood

```
┌──────────────────────────────────────────────────────────────┐
│                    VISITOR'S BROWSER                         │
│              (Gradio Chat Interface)                         │
│                        │                                     │
│              Types a question                                │
│                        ▼                                     │
├──────────────────────────────────────────────────────────────┤
│                      app.py                                  │
│                                                              │
│  1. Loads LinkedIn PDF + summary.txt at startup              │
│  2. Builds system prompt with your persona + resume data     │
│  3. Sends conversation to Google Gemini API                  │
│                        │                                     │
│              ┌─────────┴──────────┐                          │
│              ▼                    ▼                           │
│        Text Reply           Tool Call                        │
│     (direct answer)    (email capture or                     │
│              │          unknown question)                     │
│              │                    │                           │
│              │          Execute function                      │
│              │          + Notify via Pushover                 │
│              │          + Second API call                     │
│              │                    │                           │
│              └─────────┬──────────┘                          │
│                        ▼                                     │
│              Return AI response                              │
│              to chat interface                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 📱 Push Notifications (Optional)

To get real-time phone notifications when someone interacts with your bot:

1. **Create a Pushover account** at [pushover.net](https://pushover.net)
2. **Create an application** in your Pushover dashboard to get an API Token
3. **Copy your User Key** from the Pushover dashboard
4. **Add both keys** to your `.env` file:
   ```env
   PUSHOVER_TOKEN=your-app-token
   PUSHOVER_USER=your-user-key
   ```
5. **Install the Pushover app** on your phone ([iOS](https://apps.apple.com/app/pushover-notifications/id506088175) / [Android](https://play.google.com/store/apps/details?id=net.superblock.pushover))

You'll now receive instant notifications when:
- 📧 A visitor shares their email (lead captured)
- ❓ The AI encounters a question it can't answer

---

## 🎨 Customization Guide

### Change the Persona Name
In `app.py`, update the name in the `Me` class:
```python
self.name = "Your Name Here"
```

### Change the AI Model
In `app.py`, update the model name in the `chat()` method:
```python
model="gemini-2.0-flash"        # Fast and efficient
model="gemini-1.5-pro"          # More capable, slower
model="gemini-3-flash-preview"  # Latest preview model
```

### Add More Context Data
Simply add more text to `me/summary.txt` — the AI will automatically use it. You can include:
- Project descriptions
- Technical blog posts
- Certifications and courses
- Awards and recognitions
- Personal interests and hobbies

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GOOGLE_API_KEY not found` | Make sure your `.env` file exists and contains the key |
| `429 Rate Limit Error` | You've exceeded the free tier quota — wait a minute or upgrade your Google plan |
| `pip: command not found` | Use `pip3` instead of `pip`, or activate your virtual environment |
| App doesn't start | Check that all dependencies are installed: `pip install -r requirements.txt` |
| PDF not loading | Ensure `me/linkedin.pdf` exists and is a valid PDF file |
| Pushover not working | Verify your `PUSHOVER_TOKEN` and `PUSHOVER_USER` in `.env` are correct |

---

## 📦 Tech Stack

| Technology | Role |
|------------|------|
| **Python 3.10+** | Core programming language |
| **Google Gemini AI** | Large Language Model for generating responses |
| **Gradio** | Web-based chat UI framework |
| **OpenAI Python SDK** | Client library for Gemini's OpenAI-compatible API |
| **PyPDF** | PDF text extraction |
| **Pushover** | Real-time push notifications |
| **python-dotenv** | Environment variable management |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/Nits02">Nitesh Sharma</a></strong>
</p>
<p align="center">
  <em>If you found this useful, give it a ⭐ on GitHub!</em>
</p>
