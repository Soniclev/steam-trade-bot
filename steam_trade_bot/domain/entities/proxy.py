from dataclasses import dataclass
from enum import Enum
import urllib.parse


class ProxyProtocolEnum(Enum):
    HTTP = "HTTP"
    SOCKS4 = "SOCKS4"
    SOCKS5 = "SOCKS5"


@dataclass(frozen=True)
class Proxy:
    protocol: ProxyProtocolEnum
    host: str
    port: int
    login: str | None
    password: str | None

    @staticmethod
    def create(s: str):
        result = urllib.parse.urlsplit(s)
        protocol = result.scheme
        if protocol == "https":
            protocol = "http"

        return Proxy(protocol=ProxyProtocolEnum(protocol.upper()), host=result.hostname,
                     port=result.port,
                     login=result.username, password=result.password)

    def __str__(self):
        login_password = f"{self.login}:{self.password}@" if self.login and self.password else ""
        return f"{self.protocol.value.lower()}://{login_password}{self.host}:{self.port}"
