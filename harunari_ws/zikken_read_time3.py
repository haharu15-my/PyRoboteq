def parse_tm(tm_str):
    """
    TMフォーマット: TM=TenMs:Sec:Min:Hour:Day:Year
    """
    if tm_str.startswith("TM="):
        tm_str = tm_str[3:]

    parts = tm_str.split(":")
    if len(parts) != 6:
        raise ValueError(f"TMフォーマット異常: {tm_str}")

    ten_ms = int(parts[0])
    sec    = int(parts[1])
    minute = int(parts[2])
    hour   = int(parts[3])
    day    = int(parts[4])

    total_seconds = (
        day * 86400 +
        hour * 3600 +
        minute * 60 +
        sec +
        ten_ms * 0.1
    )
    return total_seconds

