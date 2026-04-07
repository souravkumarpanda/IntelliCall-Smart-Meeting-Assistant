"use client";

import { useEffect, useState, useRef } from "react";
import { useCall } from "@stream-io/video-react-sdk";
import { useChatContext } from "stream-chat-react";

export function TranscriptPanel() {
  const { client } = useChatContext();
  const [transcripts, setTranscripts] = useState([]);
  const [notes, setNotes] = useState([]);
  const transcriptEndRef = useRef(null);
  const call = useCall();

  // Read the fixed call ID from env — must match backend PUBLIC_CALL_ID
  const callId = process.env.NEXT_PUBLIC_CALL_ID;

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  useEffect(() => {
    if (!call || !callId) {
      console.warn("⚠️ Call or callId not ready");
      return;
    }

    const channel = client.channel("messaging", callId);
    channel.watch().then(() => {
      console.log("✅ Listening on channel:", callId);
    });

    // Live captions from real participants
    const handleClosedCaption = (event) => {
      if (!event.closed_caption) return;
      setTranscripts((prev) => [
        ...prev,
        {
          type: "caption",
          text: event.closed_caption.text,
          speaker:
            event.closed_caption.user?.name ||
            event.closed_caption.user?.id ||
            "Unknown",
          timestamp: new Date(
            event.closed_caption.start_time
          ).toLocaleTimeString(),
        },
      ]);
    };

    // Messages from the bot (transcripts, notes, Q&A responses)
    const handleNewMessage = (event) => {
      const message = event.message;
      if (message?.user?.id !== "meeting-assistant-bot") return;

      console.log("📨 Bot message:", message.custom?.type, message.text);

      const customType = message?.custom?.type;

      if (customType === "transcript") {
        // Bot-forwarded transcript entry
        setTranscripts((prev) => [
          ...prev,
          {
            type: "transcript",
            text: message.text,
            speaker: message.custom.speaker || "Participant",
            timestamp: new Date(message.created_at).toLocaleTimeString(),
          },
        ]);
      } else if (customType === "notes") {
        // Notes update — replace notes list
        try {
          const parsed = JSON.parse(message.custom.data.NOTES);
          setNotes(Array.isArray(parsed) ? parsed : []);
        } catch (e) {
          console.error("Failed to parse notes:", e);
        }
      } else {
        // Plain text = Q&A response from assistant
        setTranscripts((prev) => [
          ...prev,
          {
            type: "qa",
            text: message.text,
            speaker: "Meeting Assistant",
            timestamp: new Date(message.created_at).toLocaleTimeString(),
          },
        ]);
      }
    };

    call.on("call.closed_caption", handleClosedCaption);
    channel.on("message.new", handleNewMessage);

    return () => {
      call.off("call.closed_caption", handleClosedCaption);
      channel.off("message.new", handleNewMessage);
    };
  }, [call, callId]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-750">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Live Transcript</h3>
              <p className="text-xs text-gray-400 mt-0.5">
                {transcripts.length} {transcripts.length === 1 ? "message" : "messages"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-green-500 font-medium">Live</span>
          </div>
        </div>
      </div>

      {/* Notes panel — visible only when notes exist */}
      {notes.length > 0 && (
        <div className="px-6 py-4 border-b border-gray-700 bg-gray-900/40">
          <p className="text-xs font-semibold text-yellow-400 uppercase tracking-wider mb-2">
            🗒️ Meeting Notes
          </p>
          <ul className="space-y-1">
            {notes.map((note, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className="text-yellow-500 mt-0.5">•</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Transcript list */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 custom-scrollbar">
        {transcripts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 bg-gray-700 rounded-full flex items-center justify-center mb-6">
              <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <p className="text-gray-300 text-lg font-semibold mb-2">Waiting for transcripts...</p>
            <p className="text-gray-500 text-sm max-w-xs">
              Start speaking to see live transcription appear here.
            </p>
          </div>
        ) : (
          <>
            {transcripts.map((item, idx) => (
              <div
                key={idx}
                className={`rounded-xl p-4 shadow-lg border transition-all duration-300 ${
                  item.type === "qa"
                    ? "bg-gradient-to-br from-blue-900/40 to-blue-800/40 border-blue-500/40"
                    : "bg-gradient-to-br from-gray-700 to-gray-750 border-gray-600 hover:border-blue-500/50"
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm shadow ring-2 ${
                    item.type === "qa"
                      ? "bg-gradient-to-br from-blue-400 to-blue-600 ring-blue-400/20"
                      : "bg-gradient-to-br from-blue-500 to-blue-600 ring-blue-500/20"
                  }`}>
                    {item.speaker.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <span className={`font-semibold text-sm ${item.type === "qa" ? "text-blue-300" : "text-blue-400"}`}>
                      {item.speaker}
                      {item.type === "qa" && (
                        <span className="ml-2 text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                          Assistant
                        </span>
                      )}
                    </span>
                    <p className="text-xs text-gray-400 font-mono">{item.timestamp}</p>
                  </div>
                </div>
                <p className="text-gray-100 leading-relaxed text-sm pl-12">{item.text}</p>
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </>
        )}
      </div>
    </div>
  );
}