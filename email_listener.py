"""
Lightweight IMAP Listener for coordinate ingestion and auto-reply.
Zero-cost, uses standard library imaplib/email.
"""
import imaplib
import email
from email.header import decode_header
import os
from route_optimizer import RouteOptimizer


def check_mailbox(host, user, password):
    opt = RouteOptimizer()
    mail = imaplib.IMAP4_SSL(host)
    mail.login(user, password)
    mail.select("INBOX")

    status, messages = mail.search(None, "(UNSEEN)")
    if status != "OK":
        return

    for num in messages[0].split():
        res, msg_data = mail.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                sender = msg.get("From")
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                try:
                    coords = opt.parse_coordinates(body)
                    optimized = opt.optimize_route(coords)
                    map_url = opt.generate_google_maps_url(optimized)
                    print(f"Processed route for {sender}: {map_url}")
                except Exception as e:
                    print(f"Error processing message from {sender}: {e}")

    mail.close()
    mail.logout()


if __name__ == "__main__":
    # Example placeholder execution
    pass
