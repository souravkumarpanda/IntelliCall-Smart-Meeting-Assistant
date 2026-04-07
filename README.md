<div align="center">

# 🧠 IntelliCall — Smart Meeting Assistant

**A real-time AI-powered meeting assistant that silently listens, transcribes, and answers your questions — all inside a live video call.**

<br/>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![Gemini](https://img.shields.io/badge/Google-Gemini%20Realtime-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Stream](https://img.shields.io/badge/Stream-Video%20%26%20Chat-005FFF?style=flat-square&logo=stream&logoColor=white)](https://getstream.io)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

[✨ Features](#-features) · [🏗️ Architecture](#️-architecture) · [🚀 Getting Started](#-getting-started) · [⚙️ Environment Variables](#️-environment-variables) · [📖 How It Works](#-how-it-works) · [🤝 Contributing](#-contributing)

</div>

---

## 🎯 What is IntelliCall?

**IntelliCall** is a full-stack smart meeting assistant that joins your video calls as a silent AI participant. It continuously transcribes everything said in the meeting in real time, and springs into action when called upon — just say **"Hey Assistant"** followed by your question, and it answers using everything discussed in the meeting so far.

No manual notes. No interruptions. Just intelligence, on demand.

> 💡 Think of it as a search engine for your meeting — it listened to everything, and answers when you ask.

---

## ✨ Features

### 🎙️ Real-Time Live Transcription
Using **Stream's Closed Captions API**, every word spoken in the call is captured and displayed in a sleek live transcript panel, tagged with the speaker's name and timestamp.

### 🤖 Voice-Activated AI Q&A
The backend AI bot (`Meeting Assistant`) listens silently throughout the call. Trigger it by saying **"Hey Assistant, [your question]"** — it uses the full meeting transcript as context and responds concisely via Google Gemini Realtime.

### 👥 Multi-Participant Video Calls
Built on **Stream Video React SDK** with a `SpeakerLayout`, the app supports multiple participants with a professional video conferencing UI — including camera, mic, and leave controls.

### 📋 Live Transcript Side Panel
A real-time side panel shows a scrolling feed of timestamped transcripts, colour-coded by speaker avatar, with smooth auto-scroll as new entries arrive.

### 🔑 Secure Token-Based Auth
A Next.js API route (`/api/token`) generates short-lived Stream user tokens server-side using `@stream-io/node-sdk`, keeping your API secrets out of the browser.

### 🧹 Clean Session Management
The AI agent gracefully handles participant join/leave events, session start/end, and automatically prints a full transcript summary to the console when the meeting ends.

---

## 🏗️ Architecture

```
IntelliCall-Smart-Meeting-Assistant/
│
├── 📁 backend/                        # Python AI Agent
│   ├── main.py                        # Agent entrypoint — joins call, handles events
│   ├── main-alt.py                    # Alternative agent configuration
│   ├── pyproject.toml                 # Project metadata & dependencies (uv)
│   ├── requirements.txt               # pip-compatible dependencies
│   └── .python-version                # Pins Python 3.13
│
└── 📁 frontend/                       # Next.js 16 Web App
    └── app/
        ├── page.js                    # Home — enter name & join meeting
        ├── layout.js                  # Root layout
        ├── globals.css                # Global styles (Tailwind CSS v4)
        ├── api/token/route.js         # Server-side Stream token generation
        ├── meeting/[id]/page.jsx      # Dynamic meeting page
        ├── components/
        │   ├── meeting-room.jsx       # Video call UI + transcript panel
        │   ├── transcript.jsx         # Live closed-caption transcript feed
        │   └── stream-provider.jsx    # Stream video & chat context providers
        └── hooks/
            └── use-stream-clients.js  # Custom hook — initialises video & chat clients
```

### How the pieces connect

```
User's Browser              Next.js Server           Python Backend (AI Agent)
──────────────              ──────────────           ─────────────────────────
Enter name ──► POST /api/token ──► Generate Stream token
                    ◄── token ──┘

Join meeting ──► Stream Video (WebRTC) ◄─────────── AI Agent joins same call
Live audio/video                                      (listens silently)
      │                                                      │
      │  call.closed_caption events                          │ Transcribes speech
      ▼                                                      ▼
Transcript Panel                               "Hey Assistant, summarize"
(auto-scrolling)                                             │
                                                    Gemini Realtime ──► AI responds
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend Framework** | Next.js 16 (App Router) | Full-stack React framework |
| **UI** | React 19 + Tailwind CSS v4 | Components & styling |
| **Video Calls** | Stream Video React SDK | WebRTC video conferencing |
| **Live Chat / Captions** | Stream Chat React + `stream-chat` | Closed captions & bot messages |
| **Token Auth** | `@stream-io/node-sdk` | Server-side token generation |
| **AI Agent Runtime** | `vision-agents` (Python) | Agent lifecycle management |
| **LLM** | Google Gemini Realtime | Real-time Q&A against transcript |
| **Speech Transcription** | Deepgram (via `vision-agents`) | Audio-to-text pipeline |
| **Package Manager** | `uv` (Python 3.13) | Fast Python dependency management |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18+
- **Python** 3.13
- **uv** (recommended) — [install here](https://docs.astral.sh/uv/) — or standard pip
- A **[Stream](https://getstream.io)** account with Video + Chat enabled
- A **Google Gemini** API key
- A **Deepgram** API key

---

### 1. Clone the Repository

```bash
git clone https://github.com/souravkumarpanda/IntelliCall-Smart-Meeting-Assistant.git
cd IntelliCall-Smart-Meeting-Assistant
```

---

### 2. Backend Setup

```bash
cd backend

# Using uv (recommended)
uv sync

# OR using pip
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
# Stream
STREAM_API_KEY=your_stream_api_key
STREAM_API_SECRET=your_stream_api_secret

# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_api_key

# Meeting room ID (must match NEXT_PUBLIC_CALL_ID in the frontend)
CALL_ID=my-meeting-room
```

Start the AI agent:

```bash
# Using uv
uv run python main.py

# Using pip venv
python main.py
```

> You should see: `🎙️ MEETING ASSISTANT ACTIVE!` in your terminal when the agent is ready.

---

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

Create a `.env.local` file inside `frontend/`:

```env
# Stream — public (safe for browser)
NEXT_PUBLIC_STREAM_API_KEY=your_stream_api_key

# Stream — private (server-side token generation only)
STREAM_API_KEY=your_stream_api_key
STREAM_API_SECRET=your_stream_api_secret

# Meeting room ID (must match CALL_ID in backend .env)
NEXT_PUBLIC_CALL_ID=my-meeting-room
```

Start the development server:

```bash
npm run dev
```

> The app will be available at **[http://localhost:3000](http://localhost:3000)**

---

### 4. Start Your Meeting

1. Open **[http://localhost:3000](http://localhost:3000)**
2. Enter your name (or leave blank for "anonymous") and click **Join Meeting**
3. Allow camera and microphone access when prompted
4. Speak — watch transcripts appear live in the side panel
5. Ask the AI anything: **"Hey Assistant, what were the key decisions so far?"**

---

## ⚙️ Environment Variables

### Backend — `backend/.env`

| Variable | Description | Required |
|---|---|---|
| `STREAM_API_KEY` | Your Stream project API key | ✅ |
| `STREAM_API_SECRET` | Your Stream project API secret | ✅ |
| `GOOGLE_API_KEY` | Google Gemini API key | ✅ |
| `DEEPGRAM_API_KEY` | Deepgram API key for transcription | ✅ |
| `CALL_ID` | Fixed meeting room ID (auto-generates UUID if unset) | Optional |

### Frontend — `frontend/.env.local`

| Variable | Description | Required |
|---|---|---|
| `NEXT_PUBLIC_STREAM_API_KEY` | Stream API key (exposed to browser) | ✅ |
| `STREAM_API_KEY` | Stream API key (server-side only) | ✅ |
| `STREAM_API_SECRET` | Stream API secret (server-side only, never expose publicly) | ✅ |
| `NEXT_PUBLIC_CALL_ID` | Meeting room ID (must match backend `CALL_ID`) | ✅ |

---

## 📖 How It Works

### The AI Agent (Backend)

The Python backend uses `vision-agents` to spawn an AI participant (`meeting-assistant-bot`) that joins the same Stream video call. It is configured with strict instructions to **remain completely silent** unless directly addressed:

```
✅ "Hey Assistant, what are the action items?" → AI responds with a summary
❌ "Let's discuss the budget"                  → AI stays silent
❌ "What do you think?"                        → AI stays silent
```

When triggered, the agent builds a full prompt using the in-memory transcript and sends it to **Google Gemini Realtime** to produce a short, factual answer. The response streams back into the call.

When the meeting ends, the agent prints a complete transcript summary to the terminal.

### The Frontend

The Next.js app handles:
- **Token generation** via a secure `/api/token` server route using `@stream-io/node-sdk`
- **Video call** using `StreamVideoClient` with `SpeakerLayout` and `CallControls`
- **Closed captions** by subscribing to the `call.closed_caption` WebRTC event
- **Live transcript rendering** in a side panel with per-speaker avatars and auto-scroll

---

## 🤝 Contributing

Contributions are welcome! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch — `git checkout -b feature/your-feature`
3. **Commit** your changes — `git commit -m "feat: add your feature"`
4. **Push** to the branch — `git push origin feature/your-feature`
5. **Open a Pull Request**

Please open an [issue](https://github.com/souravkumarpanda/IntelliCall-Smart-Meeting-Assistant/issues) first for major changes so we can discuss the approach.

---

## 🐛 Reporting Bugs

Open an [issue](https://github.com/souravkumarpanda/IntelliCall-Smart-Meeting-Assistant/issues) and include:
- Steps to reproduce
- Expected vs actual behaviour
- Your OS, Node.js version, and Python version

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ by [Sourav Kumar Panda](https://github.com/souravkumarpanda)

⭐ If IntelliCall saved you from writing meeting notes — give it a star!

</div>
