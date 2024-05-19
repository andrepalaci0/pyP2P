
def format_message(origin, seqno, ttl, operation, arguments):
    return f"{origin} {seqno} {ttl} {operation} {arguments}"
    