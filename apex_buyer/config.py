import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def _get_int_list(name: str) -> list[int]:
    raw = os.getenv(name, "")
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _require(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name} (см. .env.example)")
    return value


TOKEN = _require("BOT_TOKEN")
ADMIN_IDS = _get_int_list("ADMIN_IDS")

PROXY = os.getenv("PROXY", "")

BUYBACK_RATES = {
    "dns_eco": 750,
    "dns_pro": 1500,
    "dns_vip": 5248,
    "proxy_ipv4": 400,
    "proxy_ipv6": 250,
    "proxy_mobile": 1000,
    "cert_clean": 1000,
    "cert_express": 1500,
    "cert_trb": 2000,
    "dns_filter": 400,
    "dns_swap": 1700,
}
