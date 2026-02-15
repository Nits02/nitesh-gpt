"""
=============================================================================
NITESH-GPT: A Personal AI Chatbot
=============================================================================
This application creates a personal AI chatbot that acts as "Nitesh Sharma".
It reads your LinkedIn PDF and a summary text file, feeds that information
to Google's Gemini AI model, and lets visitors chat with your AI persona
through a web interface (Gradio).

HOW IT WORKS (Simple Overview):
1. Reads your personal data (LinkedIn PDF + summary.txt) at startup.
2. When a visitor asks a question, it sends that question along with your
   personal data to Google Gemini AI.
3. Gemini answers the question AS IF it were you, using your resume/bio.
4. If someone wants to contact you, the bot captures their email and sends
   you a phone notification via Pushover.
5. If the bot can't answer a question, it logs it so you can review later.

DEPENDENCIES (installed via requirements.txt):
- openai       : Client library to talk to Google Gemini (using OpenAI-compatible API)
- gradio       : Creates the web-based chat UI (the webpage visitors see)
- pypdf        : Reads text from your LinkedIn PDF file
- requests     : Makes HTTP calls (used for Pushover notifications)
- python-dotenv: Loads secret API keys from the .env file
=============================================================================
"""

# ──────────────────────────────────────────────────────────────────────────────
# STEP 0: IMPORT LIBRARIES
# These are external packages/modules that give us extra functionality.
# Think of them like "plugins" that add new abilities to our code.
# ──────────────────────────────────────────────────────────────────────────────

import os           # For reading environment variables (secret keys) and file paths
import json         # For converting Python dictionaries to/from JSON text format
import requests     # For making HTTP requests (e.g., sending Pushover notifications)
import gradio as gr # For creating the web-based chat interface that users interact with
from openai import OpenAI   # Client library to communicate with Google Gemini AI
from pypdf import PdfReader  # For extracting text content from PDF files
from dotenv import load_dotenv  # For loading secret keys from the .env file

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD ENVIRONMENT VARIABLES (Secret Keys)
# ──────────────────────────────────────────────────────────────────────────────
# The .env file contains sensitive API keys that should NEVER be shared publicly.
# load_dotenv() reads the .env file and makes those keys available via os.getenv().
# "override=True" means: if a key already exists in the system, replace it with
# the value from .env (ensures our local .env always takes priority).
load_dotenv(override=True)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2: CONNECT TO GOOGLE GEMINI AI
# ──────────────────────────────────────────────────────────────────────────────
# Google Gemini provides an "OpenAI-compatible" endpoint, which means we can
# use the familiar OpenAI Python library to talk to Gemini. We just need to
# point it to Google's URL instead of OpenAI's.

# This is Google's API endpoint that mimics the OpenAI API format
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Read the Google API key from the .env file
# (This key authenticates us with Google's servers — like a password)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Safety check: if the API key is missing, stop immediately with a clear error
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Create the AI client — this is our "connection" to Google Gemini.
# Every time we want to ask the AI something, we'll use this 'client' object.
client = OpenAI(
    base_url=GEMINI_BASE_URL,  # Tell the client to talk to Google, not OpenAI
    api_key=GOOGLE_API_KEY     # Authenticate with our API key
)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3: DEFINE HELPER FUNCTIONS (Tools)
# ──────────────────────────────────────────────────────────────────────────────
# These functions perform specific actions that the AI can "call" during a
# conversation. For example, if a visitor provides their email, the AI can
# trigger record_user_details() to notify you.

def push_notification(text):
    """
    Sends a push notification to your phone via the Pushover service.
    
    WHY: So you get instant alerts when someone wants to contact you or
    asks a question the bot can't answer.
    
    HOW: Makes an HTTP POST request to Pushover's API with your message.
    
    OPTIONAL: If Pushover keys are not set, the message is just printed
    to the console (no notification sent). The app still works fine without it.
    """
    # Read Pushover credentials from .env file
    token = os.getenv("PUSHOVER_TOKEN")  # Your Pushover app's API token
    user = os.getenv("PUSHOVER_USER")    # Your Pushover user/group key

    # If Pushover keys aren't configured, just log to console and skip
    if not token or not user:
        print(f"Bypassing Pushover (Keys missing). Log: {text}")
        return

    # Try to send the notification; if it fails, print the error but don't crash
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": text}
        )
    except Exception as e:
        print(f"Pushover failed: {e}")


def record_user_details(email, name="Name not provided", notes="not provided"):
    """
    Called by the AI when a visitor wants to get in touch with you.
    
    WHAT IT DOES:
    - Takes the visitor's email (required), name, and any notes
    - Sends you a push notification with their contact info
    - Returns a success message so the AI can confirm to the visitor
    
    EXAMPLE: A visitor says "I'd like to hire Nitesh, my email is john@example.com"
    → The AI calls this function → You get a notification on your phone
    """
    msg = f"LEAD CAPTURED: {name} ({email}). Notes: {notes}"
    push_notification(msg)  # Send you the notification
    return {"status": "success", "message": "User details recorded."}


def record_unknown_question(question):
    """
    Called by the AI when it receives a question it CANNOT answer
    based on the provided context (your resume/bio).
    
    WHAT IT DOES:
    - Logs the unanswered question
    - Sends you a notification so you can review and potentially
      update your summary.txt or LinkedIn PDF with that info
    
    EXAMPLE: A visitor asks "What's Nitesh's favourite programming language?"
    but that info isn't in the resume → AI calls this function → You get notified
    """
    msg = f"UNKNOWN QUESTION: {question}"
    push_notification(msg)  # Send you the notification
    return {"status": "success", "message": "Question logged for review."}


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3b: TOOL DEFINITIONS FOR THE AI
# ──────────────────────────────────────────────────────────────────────────────
# The AI model (Gemini) needs to know WHAT tools it can use and HOW to use them.
# Below, we describe each tool in a structured JSON format that the AI understands.
# Think of this as giving the AI a "menu" of actions it can take during a chat.
#
# Each tool definition includes:
#   - "name": The function name to call
#   - "description": When should the AI use this tool?
#   - "parameters": What inputs does the function need? (and which are required)

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Record user contact info if they want to get in touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},   # Visitor's email (required)
                    "name": {"type": "string"},    # Visitor's name (optional)
                    "notes": {"type": "string"}    # Any extra context (optional)
                },
                "required": ["email"]  # Only email is mandatory
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Log questions you (the AI) cannot answer based on the context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}  # The question that couldn't be answered
                },
                "required": ["question"]
            }
        }
    }
]


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4: THE PERSONA CLASS — The Heart of the Application
# ──────────────────────────────────────────────────────────────────────────────
# This class represents "you" (Nitesh Sharma) as an AI persona.
# It:
#   1. Loads your personal data (LinkedIn PDF + summary.txt) at startup
#   2. Builds a "system prompt" — instructions telling the AI how to behave
#   3. Handles the back-and-forth chat with visitors

class Me:
    def __init__(self):
        """
        Constructor — runs when we create a new Me() object.
        Sets the persona name and loads all personal data from files.
        """
        self.name = "Nitesh Sharma"  # The name the AI will use as its identity
        self.context_data = ""        # Will hold all the text from your resume/bio
        self._load_data()             # Load the PDF and summary files right away

    def _load_data(self):
        """
        Reads your personal data from THREE sources and combines them
        into one big text block (self.context_data).
        
        SOURCE 1: me/linkedin.pdf  — Your LinkedIn profile exported as PDF
        SOURCE 2: me/summary.txt   — Your bio, blog posts, achievements, etc.
        SOURCE 3: me/website.txt   — Content scraped from your personal website (thedataarch.com)
        
        This combined text is what the AI uses to answer questions about you.
        The more detailed these files are, the better the AI can respond!
        """
        # --- Load LinkedIn PDF ---
        pdf_path = "me/linkedin.pdf"
        if os.path.exists(pdf_path):
            reader = PdfReader(pdf_path)           # Open the PDF file
            for page in reader.pages:              # Loop through each page
                text = page.extract_text()         # Extract the text from that page
                if text:
                    self.context_data += text + "\n"  # Append it to our context

        # --- Load Summary/Bio Text File ---
        summary_path = "me/summary.txt"
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                self.context_data += "\n" + f.read()  # Append summary text to context

        # --- Load Website Content ---
        # This file contains scraped content from the personal website (thedataarch.com)
        # including career journey, technical expertise, blog posts, and philosophy.
        website_path = "me/website.txt"
        if os.path.exists(website_path):
            with open(website_path, "r", encoding="utf-8") as f:
                self.context_data += "\n" + f.read()  # Append website content to context

    def system_prompt(self):
        """
        Builds the "system prompt" — a set of instructions that tells the AI:
        - WHO it is (your name/persona)
        - HOW it should behave (tone, style, formatting)
        - WHAT data to use for answering (your resume/bio text)
        - WHEN to use tools (unknown questions, contact requests)
        
        This prompt is sent to Google Gemini at the start of every conversation.
        The AI follows these instructions for all its responses.
        """
        return f"""You are acting as {self.name}. You are an AI assistant on {self.name}'s personal portfolio website.

Your Goal: Answer questions about {self.name}'s professional background, skills, experience, projects, and blog posts.

Personality & Tone:
- Professional yet warm and approachable — like a friendly colleague.
- Speak in first person as {self.name} (e.g., "I have experience in…", "My work at…").
- Show genuine enthusiasm when discussing technical topics.

Response Guidelines:
1. Use the Context below to answer questions faithfully and accurately.
2. Format responses using **Markdown** (bold, bullet points, headers) to improve readability.
3. Keep answers concise (3-5 sentences) unless the user explicitly asks for more detail.
4. If the user greets you, respond warmly and briefly introduce yourself with a one-liner about your expertise.
5. If the user asks something NOT covered in the Context, use the 'record_unknown_question' tool and let them know politely that you don't have that specific detail.
6. If the user expresses interest in hiring, collaborating, or getting in touch, ask for their email and use 'record_user_details'.
7. Never fabricate information not present in the Context.

## Context / Resume:
{self.context_data}
"""

    def chat(self, message, history):
        """
        The main chat function — called every time a visitor sends a message.
        
        HOW THE CONVERSATION FLOW WORKS:
        ┌─────────────────────────────────────────────────────────┐
        │  Visitor types a message in the Gradio chat UI          │
        │       ↓                                                 │
        │  This function receives the message + chat history      │
        │       ↓                                                 │
        │  We build a list of messages (system prompt + history   │
        │  + new message) and send it to Google Gemini            │
        │       ↓                                                 │
        │  Gemini responds with either:                           │
        │    a) A text reply → we return it directly              │
        │    b) A "tool call" → we execute the tool, send the     │
        │       result back to Gemini, and get a final reply      │
        └─────────────────────────────────────────────────────────┘
        
        Args:
            message (str):  The latest message typed by the visitor
            history (list): The full conversation history so far
                            (list of dicts like {"role": "user", "content": "..."})
        
        Returns:
            str: The AI's response text to display in the chat
        """

        # --- Build the conversation messages list ---
        # Every API call needs the FULL conversation context:
        #   1. System prompt (who the AI is + your resume data)
        #   2. Previous messages (chat history)
        #   3. The new message from the visitor
        messages = [{"role": "system", "content": self.system_prompt()}]

        # Append the entire conversation history so the AI remembers
        # what was said before (Gradio provides this as a list of dicts)
        messages.extend(history)

        # Append the visitor's new message
        messages.append({"role": "user", "content": message})

        # --- Send everything to Google Gemini and get a response ---
        # "model"       = which Gemini model to use
        # "tools"       = the list of functions the AI is allowed to call
        # "temperature" = controls creativity (0.7 = balanced)
        # "max_tokens"  = caps response length to keep answers concise
        try:
            response = client.chat.completions.create(
                model="gemini-2.5-flash-lite",
                messages=messages,
                tools=tools,
                temperature=0.7,
                max_tokens=500,
            )
        except Exception as e:
            # If the API call fails (e.g., rate limit, network error), show a friendly message
            return (
                "I'm sorry, I'm having a bit of trouble connecting right now. "
                "Please try again in a moment. 🙏"
            )

        # --- Check if the AI wants to call a tool (function) ---
        # Sometimes, instead of replying with text, the AI decides it needs to
        # call one of our tools (e.g., record a visitor's email or log an unknown question).
        # When that happens, finish_reason will be "tool_calls".
        if response.choices[0].finish_reason == "tool_calls":

            # Get the list of tool calls the AI wants to make
            tool_calls = response.choices[0].message.tool_calls

            # Add the AI's tool-call request to the conversation
            # (so the next API call has the full context)
            messages.append(response.choices[0].message)

            # --- Execute each tool call ---
            for tool_call in tool_calls:
                fn_name = tool_call.function.name  # Which function to call

                # Safely parse the arguments (guard against malformed JSON)
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                # Match the function name and call the corresponding Python function
                if fn_name == "record_user_details":
                    result = record_user_details(**args)     # ** unpacks the dict as keyword arguments
                elif fn_name == "record_unknown_question":
                    result = record_unknown_question(**args)
                else:
                    result = {"error": "function not found"}  # Safety fallback

                # Add the tool's result back into the conversation
                # so Gemini knows what happened and can craft a proper reply
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,      # Links this result to the specific tool call
                    "content": json.dumps(result)       # Convert the result dict to JSON text
                })

            # --- Second API call: Get the AI's final text response ---
            # Now that the tool has been executed and results are in the messages,
            # we ask Gemini to craft a nice reply to the visitor
            try:
                final_response = client.chat.completions.create(
                    model="gemini-2.5-flash-lite",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500,
                )
                return final_response.choices[0].message.content
            except Exception as e:
                return (
                    "I captured your information, but had trouble generating a response. "
                    "Please try again! 🙏"
                )

        # --- If no tool was called, just return the AI's text response directly ---
        return response.choices[0].message.content


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5: LAUNCH THE WEB APPLICATION
# ──────────────────────────────────────────────────────────────────────────────
# This is the entry point — the code that runs when you execute: python app.py
#
# It creates the "Me" persona (loads all your data) and starts a Gradio web
# server with a chat interface. Visitors can then open the URL in their browser
# and start chatting with your AI persona.

if __name__ == "__main__":
    bot = Me()  # Create the persona (loads LinkedIn PDF + summary.txt + website.txt)

    # ── Branded Header HTML ──
    # A custom header with icon, title, subtitle, and social links.
    # Gives the chatbot a polished, professional identity.
    header_html = """
    <div class="chat-header">
        <div class="header-content">
            <div class="header-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                     stroke="white" stroke-width="2" stroke-linecap="round"
                     stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
            </div>
            <div>
                <div class="header-title">Chat with Nitesh Sharma's AI</div>
                <div class="header-subtitle">
                    AI assistant trained on resume, LinkedIn, website &amp; blog content
                </div>
            </div>
        </div>
        <div class="header-links">
            <a href="https://thedataarch.com" target="_blank">🌐 Website</a>
            <span class="link-sep">·</span>
            <a href="https://www.linkedin.com/in/nsharma02/" target="_blank">💼 LinkedIn</a>
            <span class="link-sep">·</span>
            <a href="https://github.com/Nits02" target="_blank">💻 GitHub</a>
        </div>
    </div>
    """

    # ── Chatbot Placeholder (Welcome Screen) ──
    # Shown inside the chatbot area when no messages exist yet.
    # Disappears as soon as the first message is sent.
    # Gradio 6.x renders placeholder as plain text, so keep it simple.
    chatbot_placeholder = (
        "💬  Welcome! I'm Nitesh's AI Assistant.\n"
        "Ask me about professional experience, skills, projects, blog posts, or anything else!\n\n"
        "💡 Try one of the suggested prompts below, or type your own question."
    )

    # ── Comprehensive CSS — Designed for Gradio 6.x ──
    # Modern, clean design with consistent color palette, smooth transitions,
    # and responsive layout for embedding in iframes (HF Spaces).
    custom_css = """
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Design Tokens ── */
    :root {
        --c-primary: #667eea;
        --c-primary-hover: #5a6fd6;
        --c-accent: #764ba2;
        --c-bg: #f4f5fa;
        --c-surface: #ffffff;
        --c-text: #16213e;
        --c-text-secondary: #555577;
        --c-text-muted: #8b8baa;
        --c-border: #e2e4f0;
        --c-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-pill: 9999px;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 14px rgba(0,0,0,0.08);
    }

    /* ── Container ── */
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        max-width: 850px !important;
        margin: 0 auto !important;
        background: var(--c-bg) !important;
        padding: 12px !important;
    }

    /* ── Branded Header ── */
    .chat-header {
        background: var(--c-surface);
        border-radius: var(--radius-lg);
        padding: 20px 24px 16px;
        margin-bottom: 10px;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--c-border);
    }
    .header-content {
        display: flex;
        align-items: center;
        gap: 14px;
        justify-content: center;
    }
    .header-icon {
        width: 48px;
        height: 48px;
        background: var(--c-gradient);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    .header-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--c-text);
        line-height: 1.3;
    }
    .header-subtitle {
        font-size: 0.83rem;
        color: var(--c-text-secondary);
        margin-top: 2px;
        font-weight: 400;
    }
    .header-links {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid var(--c-border);
    }
    .header-links a {
        color: var(--c-primary) !important;
        text-decoration: none !important;
        font-size: 0.82rem;
        font-weight: 500;
        transition: color 0.2s;
    }
    .header-links a:hover {
        color: var(--c-accent) !important;
    }
    .link-sep {
        color: var(--c-text-muted);
        font-size: 0.7rem;
    }

    /* ── Suppress default ChatInterface title/desc (we have custom header) ── */
    .chat-interface-title, .gradio-container h1 {
        display: none !important;
    }
    .chat-interface .prose, .gradio-container > .prose {
        display: none !important;
    }

    /* ── Chatbot placeholder text styling ── */
    .chatbot .placeholder,
    .gradio-chatbot .placeholder {
        color: var(--c-text-secondary) !important;
        font-size: 0.95rem !important;
        text-align: center !important;
        padding: 40px 20px !important;
        white-space: pre-line !important;
        line-height: 1.7 !important;
    }

    /* ── Chatbot Container ── */
    .chatbot, .gradio-chatbot {
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--c-border) !important;
        background: var(--c-bg) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── Message Bubbles — User (gradient) ── */
    .message-row.user-row .message-bubble,
    .chatbot .user .message-bubble-border,
    .message.user .bubble-wrap .bubble {
        background: var(--c-gradient) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 10px 16px !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25) !important;
    }
    .message-row.user-row .message-content,
    .chatbot .user .message-content,
    .message.user .bubble-wrap .bubble * {
        color: #ffffff !important;
    }

    /* ── Message Bubbles — Bot (clean white) ── */
    .message-row.bot-row .message-bubble,
    .chatbot .bot .message-bubble-border,
    .message.bot .bubble-wrap .bubble {
        background: var(--c-surface) !important;
        color: var(--c-text) !important;
        border: 1px solid var(--c-border) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 10px 16px !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .message-row.bot-row .message-content,
    .chatbot .bot .message-content,
    .message.bot .bubble-wrap .bubble * {
        color: var(--c-text) !important;
    }

    /* ── Markdown inside bot messages ── */
    .chatbot .bot .message-content strong,
    .message.bot .bubble-wrap strong {
        color: var(--c-text) !important;
        font-weight: 600 !important;
    }
    .chatbot .bot .message-content a,
    .message.bot .bubble-wrap a {
        color: var(--c-primary) !important;
        text-decoration: underline !important;
    }
    .chatbot .bot .message-content code,
    .message.bot .bubble-wrap code {
        background: #f0f1f7 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.85em !important;
    }

    /* ── Input Textbox ── */
    textarea, input[type="text"] {
        border-radius: var(--radius-md) !important;
        border: 1.5px solid var(--c-border) !important;
        background: var(--c-surface) !important;
        color: var(--c-text) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 12px 16px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    textarea:focus, input[type="text"]:focus {
        border-color: var(--c-primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        outline: none !important;
    }
    textarea::placeholder, input[type="text"]::placeholder {
        color: var(--c-text-muted) !important;
    }

    /* ── Primary Button (Send) ── */
    button.primary, .submit-btn {
        background: var(--c-gradient) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 10px 22px !important;
        transition: transform 0.15s ease, box-shadow 0.2s ease !important;
        cursor: pointer !important;
    }
    button.primary:hover, .submit-btn:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md), 0 4px 14px rgba(102, 126, 234, 0.3) !important;
    }
    button.primary:active, .submit-btn:active {
        transform: translateY(0) !important;
    }

    /* ── Secondary / Utility Buttons (Retry, Undo, Clear) ── */
    button.secondary, .undo-btn, .retry-btn, .clear-btn {
        background: var(--c-surface) !important;
        border: 1px solid var(--c-border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--c-text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    button.secondary:hover, .undo-btn:hover, .retry-btn:hover, .clear-btn:hover {
        border-color: var(--c-primary) !important;
        color: var(--c-primary) !important;
        background: rgba(102, 126, 234, 0.04) !important;
    }

    /* ── Example Prompt Buttons ── */
    .examples button, button.example-btn, .example-btn,
    .gallery-item, table.examples button {
        background: var(--c-surface) !important;
        border: 1px solid var(--c-border) !important;
        border-radius: var(--radius-pill) !important;
        color: var(--c-text-secondary) !important;
        padding: 8px 18px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    .examples button:hover, button.example-btn:hover, .example-btn:hover,
    .gallery-item:hover, table.examples button:hover {
        background: rgba(102, 126, 234, 0.06) !important;
        border-color: var(--c-primary) !important;
        color: var(--c-primary) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12) !important;
    }

    /* ── Labels & Text ── */
    label, .label-wrap, span, p {
        color: var(--c-text) !important;
    }

    /* ── Hide Gradio footer for clean embedding ── */
    footer { display: none !important; }

    /* ── Responsive Design for iframe / mobile embedding ── */
    @media (max-width: 640px) {
        .gradio-container {
            padding: 6px !important;
        }
        .chat-header {
            padding: 14px 16px 12px;
            border-radius: var(--radius-md);
            margin-bottom: 6px;
        }
        .header-title {
            font-size: 1.05rem;
        }
        .header-subtitle {
            font-size: 0.78rem;
        }
        .header-content {
            gap: 10px;
        }
        .header-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
        }
        .header-icon svg {
            width: 22px;
            height: 22px;
        }
        .header-links {
            gap: 8px;
        }
        .header-links a {
            font-size: 0.78rem;
        }
        .welcome-screen {
            padding: 32px 16px;
        }
        .welcome-screen h3 {
            font-size: 1rem;
        }
    }
    """

    # ── Example prompts visitors can click on ──
    examples = [
        "Tell me about Nitesh's professional experience",
        "What cloud platforms has he worked with?",
        "What is the AI-First Data Architect blog series about?",
        "What are his key achievements and impact?",
        "What is his philosophy on data architecture?",
    ]

    # ── Build & Launch the Interface ──
    # Uses gr.Blocks for full layout control with a custom header,
    # then embeds ChatInterface for robust chat functionality.
    with gr.Blocks(
        title="Chat with Nitesh Sharma's AI",
    ) as demo:

        # Custom branded header (above the chatbot)
        gr.HTML(header_html)

        # Chat interface with pre-configured chatbot and textbox
        gr.ChatInterface(
            fn=bot.chat,
            examples=examples,
            chatbot=gr.Chatbot(
                height=480,
                show_label=False,
                placeholder=chatbot_placeholder,
            ),
            textbox=gr.Textbox(
                placeholder="Ask me anything about Nitesh…",
                show_label=False,
                scale=7,
            ),
        )

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        css=custom_css,
        theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate"),
    )
