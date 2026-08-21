class ServerNotFoundError(Exception):
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        super().__init__(f"server not found: {ip}:{port}")
