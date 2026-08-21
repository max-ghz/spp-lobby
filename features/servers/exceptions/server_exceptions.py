class ServerNotFoundError(Exception):
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        super().__init__(f"server not found: {ip}:{port}")


class ServerLimitExceededError(Exception):
    def __init__(self, ip: str) -> None:
        self.ip = ip
        super().__init__(f"server limit exceeded for ip: {ip}")


class RateLimitExceededError(Exception):
    def __init__(self, ip: str, retry_after_seconds: float) -> None:
        self.ip = ip
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limit exceeded for ip: {ip}, retry after {retry_after_seconds:.1f}s")
