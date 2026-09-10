import time
import json
import streamlit as st
import ollama
from knowledge_base import IT_KNOWLEDGE_BASE, search_knowledge_base
from tools import create_ticket, get_all_tickets, get_ticket, escalate_ticket, run_system_diagnostics

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AI IT Helpdesk Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (CSS)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Container padding */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 950px;
    }

    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #6366f1 100%);
        border-radius: 14px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1.2rem;
        color: white;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.15);
    }

    .hero-title {
        font-size: 1.7rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .hero-subtitle {
        color: #e0e7ff;
        font-size: 0.9rem;
        margin-top: 0.25rem;
        margin-bottom: 0.5rem;
    }

    .badge-chip {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-size: 0.73rem;
        font-weight: 600;
        color: white;
        margin-right: 0.35rem;
    }

    /* RAG & Tool Execution Badges inside Chat */
    .rag-badge {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 0 6px 6px 0;
        padding: 0.45rem 0.75rem;
        font-size: 0.82rem;
        color: #1e40af;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .tool-badge {
        background: #ecfdf5;
        border-left: 4px solid #10b981;
        border-radius: 0 6px 6px 0;
        padding: 0.45rem 0.75rem;
        font-size: 0.82rem;
        color: #065f46;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    /* Ticket Card */
    .ticket-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.9rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Persona System Prompt
IT_AGENT_SYSTEM_PROMPT = """
You are an expert, proactive AI IT Helpdesk Support Specialist for enterprise users.
You have direct access to:
1. An indexed IT Knowledge Base (RAG) containing official Standard Operating Procedures (SOPs).
2. Live host diagnostic tools (Disk, Network reachability, Memory).
3. Incident Ticket Management tools (Create ticket, Escalate).

Instructions:
- Always answer promptly, politely, and professionally.
- If the user says a greeting (like 'hi', 'hello'), greet them warmly and ask how you can assist with their IT or computer issues today.
- When Knowledge Base SOP context is supplied, provide the official solution cleanly formatted with numbered steps, bullet points, and copyable commands.
- Mention the source SOP ID (e.g. `[KB-NET-001]`).
- If diagnostics results are present, explain the status clearly in plain English.
- If a ticket was created, confirm the Ticket ID clearly for the user.
""".strip()


def check_ollama_status():
    """Verify Ollama connection."""
    try:
        response = ollama.list()
        models = []
        if isinstance(response, dict) and "models" in response:
            models = [m["name"] if isinstance(m, dict) else m.model for m in response["models"]]
        elif hasattr(response, "models"):
            models = [m.model if hasattr(m, "model") else str(m) for m in response.models]
        return True, models
    except Exception as e:
        return False, str(e)


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

is_connected, model_info = check_ollama_status()

# Sidebar: Navigation & Controls
with st.sidebar:
    st.markdown("### 🛡️ Helpdesk Navigation")
    nav_mode = st.radio(
        "View Section",
        ["💬 Support Chat", "🎫 Incident Tickets", "📚 Knowledge Base", "💻 System Diagnostics"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Engine Settings")

    if is_connected:
        st.success("🟢 **Ollama Connected**", icon="✅")
        available_models = model_info if isinstance(model_info, list) else []
        default_index = 0
        for idx, name in enumerate(available_models):
            if "qwen" in name.lower():
                default_index = idx
                break
        selected_model = st.selectbox("AI Model", options=available_models, index=default_index)
    else:
        st.error("🔴 **Ollama Offline**")
        selected_model = "qwen2.5:latest"

    st.markdown("---")
    st.markdown("### 📊 Helpdesk Stats")
    all_tickets = get_all_tickets()
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Open Tickets", len([t for t in all_tickets if t.get("status") != "Resolved"]))
    with c2:
        st.metric("KB Articles", len(IT_KNOWLEDGE_BASE))

    st.markdown("---")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05, help="Lower = more deterministic technical advice.")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()


# Render Hero Banner
st.markdown(
    f"""
    <div class="hero-banner">
        <h1 class="hero-title">
            <span>🛡️</span> AI IT Helpdesk Agent
        </h1>
        <p class="hero-subtitle">
            Autonomous Technical Support & Incident Resolution • <strong>Agent + RAG + Diagnostics</strong>
        </p>
        <div>
            <span class="badge-chip">🔒 100% Local</span>
            <span class="badge-chip">🧠 {selected_model}</span>
            <span class="badge-chip">📚 RAG Active (9 SOPs)</span>
            <span class="badge-chip">⚙️ Tools Enabled</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================== VIEW 1: SUPPORT CHAT ====================
if nav_mode == "💬 Support Chat":
    # Shortcut Chips
    st.markdown("<small>💡 **Quick IT Issues (Click to solve):**</small>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)

    if b1.button("🔑 Password / Lockout", use_container_width=True):
        st.session_state.pending_prompt = "My Active Directory corporate account is locked and password expired. How do I unlock it?"
        st.rerun()

    if b2.button("🌐 Wi-Fi No Internet", use_container_width=True):
        st.session_state.pending_prompt = "My Wi-Fi is connected but says 'No Internet Access'. What are the troubleshooting steps?"
        st.rerun()

    if b3.button("🖨️ Printer Offline", use_container_width=True):
        st.session_state.pending_prompt = "The office network printer is offline and print jobs are stuck in queue."
        st.rerun()

    if b4.button("💻 Run Diagnostics", use_container_width=True):
        st.session_state.pending_prompt = "My laptop is freezing and running slow. Please run a system diagnostic scan and advise."
        st.rerun()

    st.markdown("---")

    # 1. Display Existing Chat Messages
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "🧑‍💻" if role == "user" else "🛡️"
        with st.chat_message(role, avatar=avatar):
            if "tools_executed" in msg and msg["tools_executed"]:
                for t in msg["tools_executed"]:
                    if "RAG" in t or "SOP" in t:
                        st.markdown(f'<div class="rag-badge">{t}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="tool-badge">{t}</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])
            if "elapsed_time" in msg:
                st.caption(f"⚡ *Resolved in {msg['elapsed_time']:.2f}s using {msg.get('model', selected_model)}*")

    # 2. Get User Input (from Chat Input OR Quick Button)
    chat_prompt = st.chat_input("Describe your technical issue or type 'create ticket', 'run diagnostics'...")
    user_prompt = st.session_state.pending_prompt or chat_prompt

    if user_prompt:
        st.session_state.pending_prompt = None

        # Append & Render User Message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_prompt)

        # Assistant Processing
        with st.chat_message("assistant", avatar="🛡️"):
            tools_executed = []
            rag_context_text = ""

            # Only run RAG if prompt is more than a simple greeting
            is_simple_greeting = user_prompt.strip().lower() in ["hi", "hii", "hello", "hey", "good morning", "good evening", "how are you"]

            if not is_simple_greeting:
                # Step 1: RAG Search
                rag_results = search_knowledge_base(user_prompt, top_k=2)
                if rag_results:
                    rag_context_text = "### RELEVANT IT KNOWLEDGE BASE ARTICLES (RAG):\n"
                    for r in rag_results:
                        rag_context_text += f"\n--- [{r['id']}] {r['title']} ---\n{r['content']}\n"
                        tools_executed.append(f"🔍 **RAG Knowledge Base:** Retrieved SOP `[{r['id']}] {r['title']}` (Score: {r['score']})")

                # Step 2: System Diagnostics Tool Check
                diag_data = None
                if any(k in user_prompt.lower() for k in ["diagnostic", "diagnostics", "slow", "freeze", "cpu", "ram", "bsod", "health check"]):
                    diag_data = run_system_diagnostics()
                    tools_executed.append(f"💻 **Diagnostics Tool:** {diag_data.get('health_summary')}")

                # Step 3: Ticket Creation Tool Check
                ticket_info = None
                if any(k in user_prompt.lower() for k in ["create ticket", "open ticket", "raise ticket", "log ticket", "create a ticket"]):
                    prio = "High" if any(p in user_prompt.lower() for p in ["urgent", "critical", "broken", "outage"]) else "Medium"
                    ticket_info = create_ticket(
                        title=user_prompt[:60],
                        description=user_prompt,
                        category=rag_results[0]["category"] if rag_results else "General IT Support",
                        priority=prio,
                    )
                    tools_executed.append(f"🎫 **Ticket Tool:** Created Incident **{ticket_info['ticket_id']}** (Priority: {ticket_info['priority']})")
            else:
                diag_data = None
                ticket_info = None

            # Render Badges
            for t in tools_executed:
                if "RAG" in t or "SOP" in t:
                    st.markdown(f'<div class="rag-badge">{t}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="tool-badge">{t}</div>', unsafe_allow_html=True)

            # Build enriched context
            agent_ctx = IT_AGENT_SYSTEM_PROMPT
            if rag_context_text:
                agent_ctx += f"\n\n{rag_context_text}"
            if diag_data:
                agent_ctx += f"\n\n### LIVE HOST DIAGNOSTICS RESULTS:\n{json.dumps(diag_data, indent=2)}"
            if ticket_info:
                agent_ctx += f"\n\n### TICKET CONFIRMATION:\nTicket ID: {ticket_info['ticket_id']}, Priority: {ticket_info['priority']}, Status: Open"

            # Construct message list (limit history to last 10 messages for speed)
            chat_ctx = [{"role": "system", "content": agent_ctx}]
            for msg in st.session_state.messages[-10:]:
                chat_ctx.append({"role": msg["role"], "content": msg["content"]})

            # Real-time streaming placeholder
            message_placeholder = st.empty()
            full_response = ""
            start_t = time.time()

            try:
                stream = ollama.chat(
                    model=selected_model,
                    messages=chat_ctx,
                    stream=True,
                    options={"temperature": temperature, "num_predict": 2048},
                )
                for chunk in stream:
                    # Safe extraction across Pydantic object and dict
                    delta = ""
                    if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                        delta = chunk.message.content or ""
                    elif isinstance(chunk, dict):
                        delta = chunk.get("message", {}).get("content", "")
                    
                    full_response += delta
                    message_placeholder.markdown(full_response + " ▌")

                elapsed = time.time() - start_t
                message_placeholder.markdown(full_response)
                st.caption(f"⚡ *Resolved in {elapsed:.2f}s using {selected_model}*")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "tools_executed": tools_executed,
                    "elapsed_time": elapsed,
                    "model": selected_model,
                })
            except Exception as e:
                err_text = f"❌ **Error generating response:** `{str(e)}`"
                message_placeholder.markdown(err_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_text,
                    "tools_executed": tools_executed,
                })


# ==================== VIEW 2: INCIDENT TICKETS ====================
elif nav_mode == "🎫 Incident Tickets":
    st.markdown("### 🎫 Incident Support Ticket Management")
    st.caption("View all recorded support incidents or submit a new ticket.")

    with st.expander("➕ Submit a New Support Ticket", expanded=False):
        with st.form("manual_ticket_form"):
            t_title = st.text_input("Incident Title", placeholder="e.g. Dual monitor not detecting after dock update")
            t_cat = st.selectbox("Category", ["Network & VPN", "Account & Security", "Hardware & Peripherals", "System & Performance", "General IT"])
            t_prio = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            t_desc = st.text_area("Issue Description", placeholder="Explain what happened and what steps were attempted...")
            submit_btn = st.form_submit_button("Create Ticket", use_container_width=True)

            if submit_btn:
                if t_title.strip():
                    new_t = create_ticket(t_title, t_desc, t_cat, t_prio)
                    st.success(f"🎉 Created Incident Ticket **{new_t['ticket_id']}** successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please enter an incident title.")

    # List tickets
    tickets = get_all_tickets()
    if tickets:
        for t in tickets:
            p_badge = {
                "Critical": "🔴 CRITICAL",
                "High": "🟠 HIGH",
                "Medium": "🟡 MEDIUM",
                "Low": "🟢 LOW",
            }.get(t.get("priority", "Medium"), "⚪")

            with st.container():
                st.markdown(
                    f"""
                    <div class="ticket-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <span style="font-size: 1.05rem; font-weight: 700; color: #1E293B;">{t['ticket_id']} — {t['title']}</span>
                            <span style="font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; background: #F1F5F9;">{p_badge}</span>
                        </div>
                        <p style="color: #64748B; font-size: 0.88rem; margin: 0.3rem 0;">{t['description']}</p>
                        <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.5rem;">
                            Category: <strong>{t.get('category')}</strong> | Assigned: <strong>{t.get('assigned_to')}</strong> | Created: {t.get('created_at')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No tickets created yet. Use the form above or ask the AI Chatbot to raise a ticket!")


# ==================== VIEW 3: KNOWLEDGE BASE ====================
elif nav_mode == "📚 Knowledge Base":
    st.markdown("### 📚 Official IT Knowledge Base (9 SOP Guides)")
    st.caption("Browse standard operating procedures and self-help articles.")

    search_kw = st.text_input("🔍 Search Knowledge Base Articles...", placeholder="e.g. VPN, DNS, password reset, printer, BSOD")

    if search_kw.strip():
        docs_to_show = search_knowledge_base(search_kw.strip(), top_k=6)
    else:
        docs_to_show = IT_KNOWLEDGE_BASE

    for doc in docs_to_show:
        with st.expander(f"📄 **[{doc['id']}] {doc['title']}** — `{doc['category']}`"):
            st.markdown(f"**Summary:** {doc['summary']}")
            st.markdown("---")
            st.markdown(doc["content"])


# ==================== VIEW 4: SYSTEM DIAGNOSTICS ====================
elif nav_mode == "💻 System Diagnostics":
    st.markdown("### 💻 Live Host System Health Diagnostics")
    st.caption("Check live hardware, disk space, and network connectivity status.")

    if st.button("🚀 Run Live System Health Check", use_container_width=True):
        with st.spinner("Running diagnostic scan..."):
            diag = run_system_diagnostics()
            st.success(diag.get("health_summary"))

            d1, d2, d3 = st.columns(3)
            with d1:
                st.metric("Free Disk (Drive C:)", f"{diag.get('disk', {}).get('free_gb', 'N/A')} GB", f"{diag.get('disk', {}).get('free_pct', '')}% free")
            with d2:
                st.metric("Network Connectivity", diag.get("network", {}).get("status", "Online"), diag.get("network", {}).get("target", "Google DNS"))
            with d3:
                st.metric("OS Platform", diag.get("architecture", "x64"), diag.get("os_platform", "Windows"))

            st.markdown("#### Diagnostic Scan Results:")
            st.json(diag)
