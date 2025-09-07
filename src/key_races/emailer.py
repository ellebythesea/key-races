import os
import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Optional


def _get(env_or_value: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
    if not env_or_value:
        return fallback
    return env_or_value


def send_email(
    smtp_cfg: Dict[str, str],
    recipients: List[str],
    subject: str,
    body_text: str,
):
    host = _get(smtp_cfg.get("host"), os.getenv("SMTP_HOST"))
    # Robustly coerce port, default to 587 if missing/invalid
    port_raw = smtp_cfg.get("port") or os.getenv("SMTP_PORT") or 587
    try:
        port = int(port_raw) if str(port_raw).lower() != "none" else 587
    except Exception:
        port = 587
    user = _get(smtp_cfg.get("user"), os.getenv("SMTP_USER"))
    password = _get(smtp_cfg.get("password"), os.getenv("SMTP_PASSWORD"))
    sender = _get(smtp_cfg.get("from"), os.getenv("SMTP_FROM"))
    starttls = smtp_cfg.get("starttls", True)

    if not (host and port and user and password and sender):
        raise RuntimeError("SMTP config incomplete: require host, port, user, password, from")

    msg = MIMEText(body_text)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP(host, port) as server:
        if starttls:
            server.starttls()
        server.login(user, password)
        server.sendmail(sender, recipients, msg.as_string())
