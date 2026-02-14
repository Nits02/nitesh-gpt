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
        - HOW it should behave (tone, style)
        - WHAT data to use for answering (your resume/bio text)
        - WHEN to use tools (unknown questions, contact requests)
        
        This prompt is sent to Google Gemini at the start of every conversation.
        The AI follows these instructions for all its responses.
        """
        return f"""
        You are acting as {self.name}. You are an AI assistant on {self.name}'s portfolio website.
        
        Your Goal: Answer questions about professional background, skills, and experience.
        Tone: Professional, engaging, and friendly.
        
        Instructions:
        1. Use the Context below to answer questions faithfully.
        2. If the user asks something NOT in the context, strictly use the 'record_unknown_question' tool.
        3. If the user seems interested in hiring or collaborating, ask for their email and use 'record_user_details'.
        4. Keep answers concise (under 4 sentences) unless asked for elaboration.

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
        # "model" = which Gemini model to use (gemini-2.0-flash is fast and capable)
        # "tools" = the list of functions the AI is allowed to call
        try:
            response = client.chat.completions.create(
                model="gemini-3-flash-preview",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            # If the API call fails (e.g., rate limit, network error), show a friendly message
            return f"Sorry, I'm having trouble connecting right now. Please try again in a moment. (Error: {e})"

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
                fn_name = tool_call.function.name               # Which function to call
                args = json.loads(tool_call.function.arguments)  # The arguments (as a dict)

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
            # (e.g., "Thanks! I've noted your email. Nitesh will be in touch soon.")
            final_response = client.chat.completions.create(
                model="gemini-3-flash-preview",
                messages=messages
            )
            return final_response.choices[0].message.content

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

    # ── Custom CSS for a polished, professional look ──
    # This CSS is injected into the Gradio page to customize colors, fonts, and layout.
    custom_css = """
    /* Overall page styling */
    .gradio-container {
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }

    /* Chat header / title styling */
    h1 {
        color: #1a1a2e !important;
        text-align: center !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.2rem !important;
    }

    /* Description text below the title */
    .prose p, .prose a {
        color: #444466 !important;
        text-align: center !important;
    }
    .prose a {
        color: #667eea !important;
        text-decoration: underline !important;
    }

    /* Chat container */
    .chatbot {
        background: #f8f8fc !important;
        border: 1px solid #e0e0ee !important;
        border-radius: 16px !important;
    }

    /* User message bubbles — purple gradient with white text */
    .chatbot .message.user .bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 18px !important;
    }

    /* Bot message bubbles — light background with dark text */
    .chatbot .message.bot .bubble {
        background: #ffffff !important;
        color: #1a1a2e !important;
        border: 1px solid #e0e0ee !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 18px !important;
    }

    /* Input textbox — dark text on light background for readability */
    textarea, input[type="text"] {
        background: #ffffff !important;
        border: 1px solid #d0d0e0 !important;
        border-radius: 12px !important;
        color: #1a1a2e !important;
        font-size: 1rem !important;
        padding: 12px !important;
    }
    textarea::placeholder, input[type="text"]::placeholder {
        color: #8888aa !important;
    }
    textarea:focus, input[type="text"]:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }

    /* Ensure all general text and labels are visible */
    label, .label-wrap, span, p {
        color: #1a1a2e !important;
    }

    /* Send / Submit button */
    button.primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    button.primary:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }

    /* Secondary buttons (Clear, etc.) */
    button.secondary {
        background: #f0f0f8 !important;
        border: 1px solid #d0d0e0 !important;
        border-radius: 12px !important;
        color: #444466 !important;
    }

    /* Example buttons */
    .example-btn {
        background: #f0f0f8 !important;
        border: 1px solid #d0d0e0 !important;
        color: #444466 !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    .example-btn:hover {
        background: rgba(102, 126, 234, 0.15) !important;
        border-color: #667eea !important;
        color: #1a1a2e !important;
    }

    /* Footer area */
    footer { display: none !important; }
    """

    # -- Description shown below the title --
    description = (
        "**AI-powered assistant** trained on Nitesh's resume, LinkedIn, website & blog content.\n\n"
        "Ask me about professional experience, skills, projects, or blog posts!\n\n"
        "[Website](https://thedataarch.com) | "
        "[LinkedIn](https://www.linkedin.com/in/nsharma02/) | "
        "[GitHub](https://github.com/Nits02)"
    )

    # ── Example prompts visitors can click on ──
    examples = [
        "Tell me about Nitesh's professional experience",
        "What cloud platforms has he worked with?",
        "What is the AI-First Data Architect blog series about?",
        "What are his key achievements and impact?",
        "What is his philosophy on data architecture?",
    ]

    # Launch the Gradio chat interface with the enhanced UI
    # We use gr.Blocks to apply custom CSS, then embed ChatInterface inside it.
    # - fn: The chat function that processes each message
    # - title: Heading at the top of the page
    # - description: Subtitle text with links
    # - examples: Clickable sample questions for visitors
    # - css: Custom styling for a dark, modern look (applied via Blocks)
    # - theme: Gradio's built-in soft theme as the base with indigo accent
    with gr.Blocks(
        css=custom_css,
        theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate"),
    ) as demo:
        gr.ChatInterface(
            fn=bot.chat,
            title=f"Chat with {bot.name}'s AI",
            description=description,
            examples=examples,
        )
    demo.launch()
