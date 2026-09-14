"""
DNS provider definitions.
Adding a new provider = one new entry in DNS_PROVIDERS. Nothing else changes.

Categories
----------
- anti_sanction : رفع تحریم (دسترسی به سایت‌های خارجی که ایران را بلاک کرده‌اند)
- anti_filter   : رفع فیلتر (دسترسی به سایت‌های فیلترشده داخل ایران)
- gaming        : کاهش پینگ و رفع محدودیت بازی‌های آنلاین
- general       : DNS عمومی با سرعت و امنیت بالا
"""

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    ANTI_SANCTION = "رفع تحریم"  # unblocks sites that geo-block Iran
    ANTI_FILTER = "رفع فیلتر"  # bypasses Iran's internal filtering
    GAMING = "گیمینگ"  # low-ping + unblocked game servers
    GENERAL = "عمومی"  # speed / privacy / reliability


@dataclass(frozen=True)
class DNSProvider:
    name: str
    primary: str
    secondary: str
    category: Category
    description: str = ""

    @property
    def servers(self) -> list[str]:
        return [self.primary, self.secondary]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# تمام providerهایی که برای کاربران ایرانی کاربرد دارند
# ---------------------------------------------------------------------------
DNS_PROVIDERS: dict[str, DNSProvider] = {
    # ── رفع تحریم (Anti-Sanction) ──────────────────────────────────────────
    "Shecan": DNSProvider(
        name="Shecan",
        primary="178.22.122.100",
        secondary="185.51.200.2",
        category=Category.ANTI_SANCTION,
        description="shecan.ir — محبوب‌ترین DNS رفع تحریم ایران",
    ),
    "Begzar": DNSProvider(
        name="Begzar",
        primary="185.55.224.24",
        secondary="185.55.226.26",
        category=Category.ANTI_SANCTION,
        description="begzar.ir — جایگزین شکن با پوشش وسیع",
    ),
    "Electro": DNSProvider(
        name="Electro",
        primary="78.157.42.100",
        secondary="78.157.42.101",
        category=Category.ANTI_SANCTION,
        description="electrotm.org — سریع و پایدار برای سایت‌های تحریم‌شده",
    ),
    "HostIran": DNSProvider(
        name="HostIran",
        primary="37.27.81.177",
        secondary="5.144.130.130",
        category=Category.ANTI_SANCTION,
        description="hostiran.net — DNS داخلی با قابلیت رفع تحریم",
    ),
    # ── گیمینگ (Gaming) ────────────────────────────────────────────────────
    # NB: 403 (10.202.10.202/.102) و Radar Game (10.202.10.10/.11) از IP
    # خصوصی (RFC1918) استفاده می‌کردند که به‌عنوان DNS عمومی کار نمی‌کند؛
    # تا زمانی که IP عمومی واقعی‌شان تأیید نشود حذف شدند.
    "AsiaTech": DNSProvider(
        name="AsiaTech",
        primary="185.98.113.113",
        secondary="185.98.114.114",
        category=Category.GAMING,
        description="asiatech.ir — مناسب گیمینگ و استفاده عمومی",
    ),
    # ── عمومی (General) ────────────────────────────────────────────────────
    "Cloudflare": DNSProvider(
        name="Cloudflare",
        primary="1.1.1.1",
        secondary="1.0.0.1",
        category=Category.GENERAL,
        description="cloudflare.com — سریع‌ترین DNS عمومی جهان",
    ),
    "Google": DNSProvider(
        name="Google",
        primary="8.8.8.8",
        secondary="8.8.4.4",
        category=Category.GENERAL,
        description="google.com — پایدارترین DNS عمومی",
    ),
    "Quad9": DNSProvider(
        name="Quad9",
        primary="9.9.9.9",
        secondary="149.112.112.112",
        category=Category.GENERAL,
        description="quad9.net — DNS با محافظت در برابر بدافزار",
    ),
    "DNS Pro": DNSProvider(
        name="DNS Pro",
        primary="87.107.110.109",
        secondary="87.107.110.110",
        category=Category.GENERAL,
        description="dnspro.ir — DNS عمومی داخلی (recursive1/2.dnspro.ir)",
    ),
}


def providers_by_category() -> dict[Category, list[DNSProvider]]:
    """Providers grouped by category — useful for building categorised UIs."""
    result: dict[Category, list[DNSProvider]] = {c: [] for c in Category}
    for p in DNS_PROVIDERS.values():
        result[p.category].append(p)
    return result
