import datetime

def log_audit_trail(ticket_id, entry_type, content):
    """Writes agentic decisions and tool interactions to a ticket-specific log file."""
    log_dir = os.path.join(ORCHESTRATOR_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(log_dir, f"{ticket_id}_audit.log")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{entry_type.upper()}]\n{content}\n" + "-"*40 + "\n")