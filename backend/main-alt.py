import asyncio
import os
import logging
from dotenv import load_dotenv

# Vision Agents imports
from vision_agents.core import agents
from vision_agents.plugins import getstream, gemini
from vision_agents.core.edge.types import User

# Core events
from vision_agents.core.events import (
    CallSessionParticipantJoinedEvent,
    CallSessionParticipantLeftEvent,
    CallSessionStartedEvent,
    CallSessionEndedEvent,
    PluginErrorEvent,
)

# LLM events
from vision_agents.core.llm.events import (
    RealtimeUserSpeechTranscriptionEvent,
    LLMResponseChunkEvent,
)

import json

# ── Patch StreamEdge to suppress non-fatal WebRTC track timeout ──────────────
try:
    from vision_agents.plugins.getstream import stream_edge_transport as _set

    _original_on_track_published = _set.StreamEdge._on_track_published

    async def _patched_on_track_published(self, event):
        try:
            await _original_on_track_published(self, event)
        except TimeoutError as e:
            logging.getLogger(__name__).warning(
                f"⚠️ Non-fatal WebRTC track timeout (bot audio): {e}"
            )

    _set.StreamEdge._on_track_published = _patched_on_track_published
except Exception as _patch_err:
    logging.getLogger(__name__).warning(
        f"⚠️ Could not patch StreamEdge: {_patch_err}"
    )
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Read the SAME call ID your frontend uses
CALL_ID = os.getenv("PUBLIC_CALL_ID", "demo-meeting-room")

meeting_data = {
    "transcript": [],
    "notes": [],
    "is_active": False,
    "channel": None,
}


def build_meeting_context():
    context = "MEETING TRANSCRIPT:\n\n"
    for entry in meeting_data["transcript"]:
        context += f"[{entry['speaker']}]: {entry['text']}\n"
    if meeting_data["notes"]:
        context += "\n\nMEETING NOTES:\n\n"
        for note in meeting_data["notes"]:
            context += f"- {note}\n"
    return context


async def send_notes_to_frontend(channel):
    try:
        notes_json = {"NOTES": json.dumps(meeting_data["notes"])}
        await channel.send_message({
            "text": json.dumps(notes_json),
            "user_id": "meeting-assistant-bot",
            "custom": {"type": "notes", "data": notes_json},
        })
        logger.info(f"📤 Sent {len(meeting_data['notes'])} notes to frontend")
    except Exception as e:
        logger.error(f"❌ Error sending notes: {e}")


async def start_agent():
    logger.info(f"🤖 Starting Meeting Assistant...")
    logger.info(f"📞 Joining call: {CALL_ID}")

    agent = agents.Agent(
        edge=getstream.Edge(),
        agent_user=User(id="meeting-assistant-bot", name="Meeting Assistant"),
        instructions="""
        You are a meeting transcription bot.

        CRITICAL RULES - FOLLOW EXACTLY:
        1. YOU MUST NEVER SPEAK unless someone says "Hey Assistant"
        2. DO NOT respond to conversations between users
        3. DO NOT acknowledge anything users say to each other
        4. DO NOT explain that you're staying silent
        5. DO NOT say "I should remain silent" or any variation
        6. ONLY RESPOND when you explicitly hear "Hey Assistant" followed by a question
        7. If unsure whether to speak: DON'T SPEAK

        Your ONLY job:
        - Listen silently
        - Transcribe everything
        - Wait for "Hey Assistant"

        When you DO hear "Hey Assistant":
        - Answer the question using meeting transcript and notes
        - Keep answer short and factual
        - Use only information from this meeting

        ❌ User: "Let's discuss the budget" → You: STAY COMPLETELY SILENT
        ❌ User: "What do you think?" → You: STAY COMPLETELY SILENT
        ✅ User: "Hey Assistant, what are the action items?" → You: Answer
        ✅ User: "Hey Assistant, summarize the meeting" → You: Summarize
        """,
        llm=gemini.Realtime(),
    )

    @agent.events.subscribe
    async def handle_session_started(event: CallSessionStartedEvent):
        await asyncio.sleep(2)
        meeting_data["is_active"] = True
        logger.info("🎙️ Session started")
        try:
            channel = agent.edge.client.channel("messaging", CALL_ID)
            await channel.watch()
            meeting_data["channel"] = channel
            logger.info(f"✅ Chat channel ready: {CALL_ID}")
        except Exception as e:
            logger.error(f"❌ Chat channel error: {e}")

    @agent.events.subscribe
    async def handle_participant_joined(event: CallSessionParticipantJoinedEvent):
        if event.participant.user.id == "meeting-assistant-bot":
            return
        logger.info(f"👤 Joined: {event.participant.user.name}")

    @agent.events.subscribe
    async def handle_participant_left(event: CallSessionParticipantLeftEvent):
        if event.participant.user.id == "meeting-assistant-bot":
            return
        logger.info(f"👋 Left: {event.participant.user.name}")

    @agent.events.subscribe
    async def handle_transcript(event: RealtimeUserSpeechTranscriptionEvent):
        if not event.text or not event.text.strip():
            return

        speaker = getattr(event, "participant_id", "Unknown")
        transcript_text = event.text

        meeting_data["transcript"].append({
            "speaker": speaker,
            "text": transcript_text,
            "timestamp": getattr(event, "timestamp", None),
        })
        logger.info(f"📝 [{speaker}]: {transcript_text}")

        channel = meeting_data.get("channel")

        # Forward transcript to frontend via chat channel
        try:
            if channel:
                await channel.send_message({
                    "text": transcript_text,
                    "user_id": "meeting-assistant-bot",
                    "custom": {"type": "transcript", "speaker": speaker},
                })
        except Exception as e:
            logger.error(f"❌ Transcript send error: {e}")

        # Auto-note every 3 entries
        if len(meeting_data["transcript"]) % 3 == 0:
            recent = meeting_data["transcript"][-3:]
            try:
                note = f"Discussed: {recent[-1]['text'][:80]}..."
                meeting_data["notes"].append(note)
                logger.info(f"🗒️ Note: {note}")
                if channel:
                    await send_notes_to_frontend(channel)
            except Exception as e:
                logger.error(f"❌ Note error: {e}")

        # Q&A trigger
        if transcript_text.lower().startswith("hey assistant"):
            prefix = "hey assistant"
            question = transcript_text[len(prefix):].strip()
            if question:
                logger.info(f"❓ Q&A triggered: {question}")
                context = build_meeting_context()
                prompt = f"""
{context}

USER QUESTION: {question}

Answer based ONLY on the meeting transcript and notes above.
Be concise and helpful.
                """
                try:
                    await agent.simple_response(prompt)
                    logger.info("🤖 Responding to question")
                except Exception as e:
                    logger.error(f"❌ Q&A error: {e}")

    @agent.events.subscribe
    async def handle_llm_response(event: LLMResponseChunkEvent):
        if hasattr(event, "delta") and event.delta:
            logger.info(f"🤖 Agent: {event.delta}")

    @agent.events.subscribe
    async def handle_session_ended(event: CallSessionEndedEvent):
        meeting_data["is_active"] = False
        logger.info("🛑 Meeting ended")
        logger.info(f"   Transcripts: {len(meeting_data['transcript'])}")
        logger.info(f"   Notes: {len(meeting_data['notes'])}")

    @agent.events.subscribe
    async def handle_errors(event: PluginErrorEvent):
        logger.error(f"❌ Plugin error: {event.error_message}")
        if event.is_fatal:
            logger.error("🚨 Fatal error")

    await agent.create_user()
    call = agent.edge.client.video.call("default", CALL_ID)

    logger.info("✅ Joining call...")
    with await agent.join(call):
        logger.info("\n" + "=" * 60)
        logger.info("🎙️  MEETING ASSISTANT ACTIVE!")
        logger.info(f"🔗 Call ID: {CALL_ID}")
        logger.info("💡 Say 'Hey Assistant' to interact")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60 + "\n")
        await agent.finish()

    logger.info("✅ Agent finished")


def print_summary():
    print("\n" + "=" * 70)
    print("📋 MEETING SUMMARY")
    print("=" * 70)
    print(f"\n📝 Transcript ({len(meeting_data['transcript'])} entries):")
    for entry in meeting_data["transcript"]:
        print(f"  [{entry['speaker']}]: {entry['text']}")
    print(f"\n🗒️ Notes ({len(meeting_data['notes'])} items):")
    if meeting_data["notes"]:
        print(json.dumps(meeting_data["notes"], indent=2))
    else:
        print("  No notes generated")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎯 SMART MEETING ASSISTANT")
    print(f"📞 Call ID: {CALL_ID}")
    print("=" * 70 + "\n")
    try:
        asyncio.run(start_agent())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    finally:
        if meeting_data["transcript"]:
            print_summary()