"""Chat page: typed + spoken input, answer, sources, intent, status, escalation indicators."""
from __future__ import annotations

import uuid

import streamlit as st

from src.safety.escalation import GENERAL_EMERGENCY_NOTE
from src.voice.speech_input import render_mic_widget
from src.voice.speech_output import offline_tts_available, render_speech_controls, speak_offline

EXAMPLES = ["What are your opening hours?", "How do I request a repeat prescription?",
            "Do you have wheelchair access?", "I'd like to speak to a person"]
INPUT_LABEL = "Your message"


def _init_state(ctx):
    ss = st.session_state
    ss.setdefault("session_id", uuid.uuid4().hex)
    ss.setdefault("messages", [])
    ss.setdefault("last", None)
    if "conversation_id" not in ss:
        ss.conversation_id = None
        if ctx.convs is not None:
            try:
                ss.conversation_id = ctx.convs.start(ss.session_id)
            except Exception:  # noqa: BLE001
                ctx.db_error = "Could not create a conversation record; messages will not be saved."


def _history(ctx):
    ss = st.session_state
    if ctx.convs is not None and ss.conversation_id is not None:
        try:
            return ctx.convs.history(ss.conversation_id)
        except Exception:  # noqa: BLE001
            pass
    return [(m["role"], m["content"]) for m in ss.messages[-12:]]


def _send(ctx, text: str):
    ss = st.session_state
    with st.spinner("Thinking..."):
        resp = ctx.service.handle(text, _history(ctx), ss.conversation_id)
    ss.messages.append({"role": "user", "content": text})
    ss.messages.append({"role": "assistant", "content": resp.answer})
    ss.last = resp
    if resp.persist_error:
        st.warning(resp.persist_error)


def _badge(label, value, color):
    st.markdown(f"<span class='qa-badge' style='background:{color}'>{label}: {value}</span>", unsafe_allow_html=True)


def _details(resp):
    st.markdown("#### Response details")
    if resp is None:
        st.caption("Ask a question to see the detected intent, sources and request status here.")
        return
    mode_txt = {"live": "Live LLM", "demo": "Demo mode (no LLM)", "rule": "Fixed safety/fallback text"}[resp.answer_mode]
    mode_col = {"live": "#13A89E", "demo": "#E0A100", "rule": "#5b6b82"}[resp.answer_mode]
    _badge("Intent", resp.intent.label, "#0B2545")
    _badge("Answer source", mode_txt, mode_col)
    st.caption(f"Why: {resp.intent.reason}. Rule matches: {resp.intent.rule_matches} ({resp.intent.confidence_note}).")
    st.markdown(f"**Request status:** `{resp.workflow.status}`  \n{resp.workflow.description}")
    if resp.escalation.required:
        st.error(f"Human escalation: YES ({resp.escalation.kind}, simulated)")
    else:
        st.success("Human escalation: not required")
    if resp.llm_error and resp.answer_mode == "demo":
        st.info(f"LLM not used: {resp.llm_error}")
    st.markdown("**Sources**")
    if resp.sources:
        for s in resp.sources:
            with st.expander(f"{s['source']} · {s['chunk_id'].split('::')[-1]} · score {s['score']}"):
                st.write(s["text"])
        st.caption(f"Retrieval: {resp.retrieval_note}")
    else:
        st.caption(f"No source cited. {resp.retrieval_note or 'This reply did not use retrieved documents.'}")
    st.caption(f"Latency: {resp.latency_ms} ms")


def render(ctx):
    _init_state(ctx)
    ss = st.session_state
    st.markdown("## 💬 Chat with Q-assist AI")
    st.info("**Privacy notice:** this is a demo with a fictional clinic. Please do **not** type real names, NHS numbers or "
            "medical details. Obvious identifiers are redacted before saving. Workflows are simulated.")
    if ctx.db_error:
        st.warning(ctx.db_error)
    if not ctx.llm.available:
        st.warning("**Demo mode:** no GEMINI_API_KEY found. Answers are extracted from the sample documents and labelled as such.")

    left, right = st.columns([3, 2], gap="large")
    with left:
        if not ss.messages:
            st.markdown("**Try a question:**")
            cols = st.columns(2)
            for i, ex in enumerate(EXAMPLES):
                if cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True):
                    _send(ctx, ex)
                    st.rerun()
        for m in ss.messages:
            with st.chat_message("user" if m["role"] == "user" else "assistant", avatar="🧑" if m["role"] == "user" else "🩺"):
                st.markdown(m["content"])

        with st.expander("🎤 Voice input (browser-based)", expanded=False):
            st.caption("Speak, check the transcription, edit it in the box below, then press Send. Works best in Chrome/Edge. "
                       "Typing always works.")
            render_mic_widget(INPUT_LABEL)
        with st.form("chat_form", clear_on_submit=True):
            text = st.text_area(INPUT_LABEL, height=90, max_chars=ctx.settings.max_input_chars,
                                placeholder="Type or dictate a question, e.g. 'Are you open on Saturday?'",
                                help="Administrative questions only. In an emergency call 999.")
            c1, c2 = st.columns([1, 1])
            sent = c1.form_submit_button("Send ➤", type="primary", use_container_width=True)
            cleared = c2.form_submit_button("Clear conversation", use_container_width=True,
                                            help="Starts a fresh conversation; earlier messages are no longer used as context.")
        if sent:
            if text.strip():
                _send(ctx, text.strip())
                st.rerun()
            else:
                st.warning("Please type or speak a question first.")
        if cleared:
            if ctx.convs is not None and ss.conversation_id is not None:
                try:
                    ss.conversation_id = ctx.convs.clear(ss.conversation_id, ss.session_id)
                except Exception:  # noqa: BLE001
                    pass
            ss.messages, ss.last = [], None
            st.rerun()

        if ss.last is not None:
            st.markdown("**Speech playback**")
            render_speech_controls(ss.last.answer)
            if offline_tts_available() and st.button("Speak on this computer (offline)", help="Uses pyttsx3 on the machine running the app"):
                if not speak_offline(ss.last.answer):
                    st.warning("Offline speech is not available on this machine.")
    with right:
        _details(ss.last)
        st.caption(GENERAL_EMERGENCY_NOTE)
