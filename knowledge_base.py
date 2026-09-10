"""
IT Helpdesk Knowledge Base (RAG Retriever)
Contains indexed Standard Operating Procedures (SOPs) and troubleshooting guides.
"""

import re
import math
from collections import Counter
from typing import List, Dict, Any

# Curated Enterprise IT SOP Articles
IT_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "KB-NET-001",
        "category": "Network & VPN",
        "title": "VPN Connection Failure (Error 800 / 806 / Timeout)",
        "keywords": ["vpn", "cisco", "anyconnect", "error 800", "error 806", "timeout", "tunnel", "remote access"],
        "summary": "Step-by-step resolution for enterprise VPN disconnection and connection handshake timeouts.",
        "content": """
### Diagnostic Steps for VPN Issues:
1. **Verify Internet Connectivity:** Confirm you can access public websites like google.com.
2. **Restart VPN Adapter:**
   - Open Command Prompt as Administrator and run:
     ```cmd
     ipconfig /flushdns
     netsh winsock reset
     ```
   - Restart the machine.
3. **Check Dual Network Adapter Conflicts:**
   - Disable secondary Wi-Fi or Ethernet interfaces so only one active gateway is enabled.
4. **Corporate Firewall / Port 443 / 1194:**
   - If connecting from hotel or public Wi-Fi, toggle 'Use SSL/TLS Fallback' in your VPN client settings.
5. **Reinstall Corporate VPN Profile:**
   - Open VPN client > Settings > Reset Preferences, then re-enter `vpn.corporate.internal`.
        """.strip(),
    },
    {
        "id": "KB-NET-002",
        "category": "Network & VPN",
        "title": "Wi-Fi Connected but 'No Internet Access' / DNS Resolution Failure",
        "keywords": ["wifi", "wi-fi", "no internet", "dns", "gateway", "ip address", "dhcp", "limited connectivity"],
        "summary": "Troubleshooting corporate Wi-Fi authentication and static IP or DNS cache conflicts.",
        "content": """
### Troubleshooting 'No Internet Access':
1. **Release and Renew DHCP Lease:**
   ```cmd
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```
2. **Switch to Corporate DNS:**
   - Ensure DNS is set to automatic (DHCP) or primary enterprise DNS (`10.0.0.10` / `1.1.1.1`).
3. **Toggle Airplane Mode:**
   - Turn Wi-Fi Off for 10 seconds, then reconnect to the corporate SSID (e.g., `CORP-SECURE-5G`).
4. **Forget & Re-authenticate Network:**
   - In Windows Settings > Network > Wi-Fi > Manage Known Networks > Select SSID > Forget. Reconnect and enter domain credentials (`DOMAIN\\Username`).
        """.strip(),
    },
    {
        "id": "KB-SEC-001",
        "category": "Account & Security",
        "title": "Active Directory Account Lockout & Password Reset Policy",
        "keywords": ["password", "reset", "locked", "account lockout", "mfa", "active directory", "credentials", "expired"],
        "summary": "Procedures to unlock domain accounts and self-service password reset (SSPR).",
        "content": """
### Password Reset & Account Unlock Procedure:
1. **Self-Service Password Reset (SSPR):**
   - Navigate to `https://passwordreset.corporate.internal` or Microsoft SSPR portal.
   - Complete multi-factor verification (SMS / Authenticator App prompt).
2. **Automatic Unlock Timer:**
   - Corporate security policy automatically unlocks accounts after 15 minutes of inactivity if no further failed attempts occur.
3. **Cached Credentials Conflict:**
   - If password was changed recently on phone/laptop, update stored credentials in Windows Credential Manager:
     - Open `control keymgr.dll` > Remove old Windows/Office domain credentials.
4. **Tier-1 Helpdesk Immediate Unlock:**
   - If urgent, ask the Helpdesk Agent to trigger a ticket for Active Directory unlock by providing your Employee ID and Manager's name.
        """.strip(),
    },
    {
        "id": "KB-SEC-002",
        "category": "Account & Security",
        "title": "MFA Authenticator Push Notification Not Received",
        "keywords": ["mfa", "2fa", "authenticator", "otp", "push notification", "duo", "microsoft authenticator", "login"],
        "summary": "Fixing MFA synchronization delays and alternative verification methods.",
        "content": """
### MFA Authentication Fixes:
1. **Verify Mobile Device Internet & Time Sync:**
   - Open Authenticator App > Settings > Time sync for codes > Sync now.
2. **Select Alternative Verification Method:**
   - Click "Sign in another way" on the login screen > Choose SMS text code or Phone Call verification.
3. **MFA Session Invalidation:**
   - Clear browser cookies & cache or try an InPrivate/Incognito window.
4. **Hardware Token / Emergency Bypass:**
   - Contact IT Helpdesk to issue a 24-hour temporary bypass code.
        """.strip(),
    },
    {
        "id": "KB-HW-001",
        "category": "Hardware & Peripherals",
        "title": "Network / Office Printer Status is 'Offline' or Job Stuck in Spooler",
        "keywords": ["printer", "offline", "print", "spooler", "paper jam", "print queue", "driver"],
        "summary": "Clearing Windows Print Spooler and reconnecting offline corporate printers.",
        "content": """
### Restoring Offline Printer & Clearing Spooler:
1. **Restart Windows Print Spooler Service:**
   - Open Command Prompt as Administrator:
     ```cmd
     net stop spooler
     del /Q /F /S "%systemroot%\\System32\\Spool\\Printers\\*.*"
     net start spooler
     ```
2. **Verify Printer IP Ping:**
   - In CMD: `ping <printer_ip_address>` (e.g. `ping 192.168.10.50`).
3. **Uncheck 'Use Printer Offline':**
   - Control Panel > Devices and Printers > Right-click Printer > 'See what's printing' > Click 'Printer' menu > Uncheck 'Use Printer Offline'.
4. **Re-add Corporate Follow-Me Printer:**
   - Open Run (`Win + R`) > `\\\\printserver.corporate.internal` > Double click your department queue.
        """.strip(),
    },
    {
        "id": "KB-HW-002",
        "category": "Hardware & Peripherals",
        "title": "Dual External Monitor Display Not Detected / Flickering",
        "keywords": ["monitor", "display", "hdmi", "displayport", "docking station", "screen", "flicker", "second screen"],
        "summary": "Resolving display detection failures with USB-C / Thunderbolt docks.",
        "content": """
### External Monitor Detection Steps:
1. **Restart Display Graphics Driver:**
   - Press `Win + Ctrl + Shift + B` (screen will flash once and beep).
2. **Docking Station Power Cycle:**
   - Unplug USB-C cable from laptop.
   - Disconnect power cord from dock for 15 seconds, reconnect power, then plug back into laptop.
3. **Force Windows Display Detection:**
   - Windows Settings (`Win + I`) > System > Display > Multiple Displays > Click 'Detect'.
4. **Set Display Projection Mode:**
   - Press `Win + P` and ensure mode is set to 'Extend'.
        """.strip(),
    },
    {
        "id": "KB-SYS-001",
        "category": "System & Performance",
        "title": "Laptop Freezing, 100% High CPU / RAM Usage & Slow Performance",
        "keywords": ["slow", "freeze", "high cpu", "ram", "memory leak", "task manager", "lag", "hang"],
        "summary": "Identifying runaway background processes, memory leaks, and disk saturation.",
        "content": """
### Performance Optimization Checklist:
1. **Identify High Resource Consumers:**
   - Press `Ctrl + Shift + Esc` to open Task Manager.
   - Sort by 'CPU' and 'Memory' to spot runaway processes (e.g. Chrome, Teams, Antivirus scans).
2. **End Problematic Background Tasks:**
   - Select hanging process > Click 'End task'.
3. **Clear Windows Temporary Cache:**
   - Press `Win + R` > type `temp` and `%temp%` > Delete non-essential cached files.
4. **Run System File Checker (SFC Scan):**
   ```cmd
   sfc /scannow
   dism /online /cleanup-image /restorehealth
   ```
5. **Check Available Disk Storage:**
   - Ensure `C:\\` drive has at least 15% free disk space for paging file allocation.
        """.strip(),
    },
    {
        "id": "KB-SYS-002",
        "category": "System & Performance",
        "title": "Microsoft Outlook Not Syncing / Crashing / OST File Corruption",
        "keywords": ["outlook", "email", "sync", "ost", "mailbox", "exchange", "office365", "crashing"],
        "summary": "Fixing Microsoft Outlook mailbox synchronization issues and rebuild profile.",
        "content": """
### Outlook Mailbox Repair Steps:
1. **Start Outlook in Safe Mode:**
   - Press `Win + R` > type `outlook.exe /safe`. If it opens cleanly, disable conflicting add-ins.
2. **Perform Send/Receive Update:**
   - Press `F9` or click 'Send/Receive All Folders'.
3. **Rebuild Cached Exchange (.OST) File:**
   - Close Outlook.
   - Navigate to `%localappdata%\\Microsoft\\Outlook`.
   - Rename `*.ost` to `*.ost.bak` and restart Outlook (Outlook will automatically re-download emails from server).
4. **Online Quick Repair:**
   - Settings > Apps > Installed Apps > Microsoft 365 > Modify > Quick Repair.
        """.strip(),
    },
    {
        "id": "KB-SYS-003",
        "category": "System & Performance",
        "title": "Windows Blue Screen (BSOD) & Unexpected Reboot Diagnostic",
        "keywords": ["bsod", "blue screen", "crash", "stop code", "dump", "reboot", "kernel"],
        "summary": "Triaging critical kernel faults, driver exceptions, and hardware memory faults.",
        "content": """
### BSOD Diagnostic Triage:
1. **Record the Stop Code:**
   - Common codes: `CRITICAL_PROCESS_DIED`, `MEMORY_MANAGEMENT`, `DRIVER_IRQL_NOT_LESS_OR_EQUAL`.
2. **Boot into Safe Mode:**
   - Hold `Shift` while clicking 'Restart' > Troubleshoot > Advanced Options > Startup Settings > Restart > Press `4` for Safe Mode.
3. **Check Windows Memory Diagnostic:**
   - Press `Win + R` > type `mdsched.exe` > Select 'Restart now and check for problems'.
4. **Review Minidump Logs:**
   - Open Event Viewer (`eventvwr.msc`) > Windows Logs > System > Filter by Event Level 'Critical' and 'Error' (Source: BugCheck).
5. **Immediate Tier-2 Escalation:**
   - If recurring > 2 times a day, create a Critical ticket for hardware/RAM diagnostic and backup user data.
        """.strip(),
    },
]


def _tokenize(text: str) -> List[str]:
    """Tokenize and lowercase clean words."""
    return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())


def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    RAG Semantic / BM25-style Retriever across the IT Knowledge Base.
    Returns ranked articles with match score and highlights.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    query_tf = Counter(query_tokens)
    ranked_results = []

    for doc in IT_KNOWLEDGE_BASE:
        # Build document text representation
        doc_text = f"{doc['title']} {doc['category']} {' '.join(doc['keywords'])} {doc['summary']} {doc['content']}"
        doc_tokens = _tokenize(doc_text)
        doc_tf = Counter(doc_tokens)

        # Calculate TF-IDF style similarity score
        score = 0.0

        # High priority for title and keyword matches
        title_tokens = set(_tokenize(doc["title"]))
        keyword_tokens = set(_tokenize(" ".join(doc["keywords"])))

        for q_token, q_count in query_tf.items():
            if q_token in doc_tf:
                tf = doc_tf[q_token]
                term_weight = 1.0
                if q_token in title_tokens:
                    term_weight += 3.0
                if q_token in keyword_tokens:
                    term_weight += 2.5
                score += (q_count * tf * term_weight)

        # Keyword direct submatch bonus
        query_lower = query.lower()
        for kw in doc["keywords"]:
            if kw in query_lower:
                score += 5.0

        if score > 0:
            ranked_results.append({
                "id": doc["id"],
                "category": doc["category"],
                "title": doc["title"],
                "summary": doc["summary"],
                "content": doc["content"],
                "score": round(score, 2),
            })

    # Sort descending by score
    ranked_results.sort(key=lambda x: x["score"], reverse=True)
    return ranked_results[:top_k]
