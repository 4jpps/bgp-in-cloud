def run_check(db_core):
    # In a real app, this would perform a file integrity check.
    # For now, it returns a dummy result.
    return {
        "/etc/bird/bird.conf": "OK",
        "/etc/network/interfaces": "MODIFIED",
    }
