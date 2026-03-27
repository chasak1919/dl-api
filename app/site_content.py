from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import Request


SITE_NAME = "OdeGate Media Downloader"
SITE_DESCRIPTION = (
    "YouTube, Instagram, TikTok va boshqa platformalardan video, audio, subtitle hamda rasm "
    "variantlarini tez ko'rsatadigan professional downloader sahifasi."
)
TELEGRAM_URL = "https://t.me/+QEtQD5HYHUUyM2Ey"


@dataclass(frozen=True)
class FaqItem:
    question: str
    answer: str


@dataclass(frozen=True)
class ProviderPage:
    key: str
    slug: str
    label: str
    hero_title: str
    hero_description: str
    meta_title: str
    meta_description: str
    badge: str
    placeholder: str
    example_url: str
    accent_start: str
    accent_end: str
    glow_tint: str
    summary: str
    features: tuple[str, ...]
    faq: tuple[FaqItem, ...]
    keywords: tuple[str, ...]


PLATFORM_PAGES: tuple[ProviderPage, ...] = (
    ProviderPage(
        key="youtube",
        slug="youtube-video-downloader",
        label="YouTube",
        hero_title="YouTube video, audio va subtitle variantlarini bitta sahifada toping",
        hero_description=(
            "YouTube havolasini kiriting va mavjud MP4 sifatlari, audio-only formatlar hamda subtitleni "
            "bir necha soniyada ko'ring."
        ),
        meta_title="YouTube Video Downloader | MP4, audio va subtitle yuklab olish",
        meta_description=(
            "SEO-friendly YouTube downloader sahifasi. Havolani kiriting, mavjud MP4 sifatlari, audio-only "
            "variantlari va subtitle fayllarini ko'ring."
        ),
        badge="YouTube downloader",
        placeholder="https://www.youtube.com/watch?v=...",
        example_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        accent_start="#ff5f45",
        accent_end="#ffb347",
        glow_tint="rgba(255, 95, 69, 0.28)",
        summary=(
            "YouTube sahifasi MP4 formatlari, audio-only variantlari va subtitle ro'yxatini ko'rsatishga "
            "ixtisoslashgan."
        ),
        features=(
            "Mavjud MP4 sifatlarini alohida ko'rsatadi.",
            "Audio-only variantlarni bitrate bilan chiqaradi.",
            "Subtitle mavjud bo'lsa til va formatini beradi.",
        ),
        faq=(
            FaqItem(
                question="YouTube linklari nega ba'zida proxy bilan ochiladi?",
                answer=(
                    "Ayrim media havolalari vaqtinchalik imzolangan bo'ladi. Shunda sayt server orqali stream "
                    "qilib beradi va yuklab olish barqaror qoladi."
                ),
            ),
            FaqItem(
                question="Hamisha barcha sifatlar chiqadimi?",
                answer=(
                    "Yo'q. Sahifa faqat API topgan va ayni vaqtda mavjud formatlarni ko'rsatadi."
                ),
            ),
        ),
        keywords=("youtube downloader", "youtube mp4", "youtube audio", "youtube subtitle"),
    ),
    ProviderPage(
        key="instagram",
        slug="instagram-downloader",
        label="Instagram",
        hero_title="Instagram reels, post va carousel rasmlarini qulay ajrating",
        hero_description=(
            "Instagram havolasini kiriting va agar mavjud bo'lsa video, carousel rasmlar va boshqa media "
            "variantlarini ko'ring."
        ),
        meta_title="Instagram Downloader | Reels, post va carousel yuklab olish",
        meta_description=(
            "Instagram reels, post va carousel media variantlarini ko'rsatadigan professional downloader "
            "sahifasi. Mavjud video va rasmlarni bitta oynada ko'ring."
        ),
        badge="Instagram downloader",
        placeholder="https://www.instagram.com/p/XXXXXXXXXXX/",
        example_url="https://www.instagram.com/p/Cu3uouoI3W5/",
        accent_start="#ff7a59",
        accent_end="#ff2d95",
        glow_tint="rgba(255, 84, 118, 0.24)",
        summary=(
            "Instagram sahifasi reels, oddiy post va carousel ichidagi rasmlarni bir xil natija panelida "
            "ko'rsatadi."
        ),
        features=(
            "Carousel ichidagi rasmlar alohida preview va download havolalari bilan chiqadi.",
            "Agar video mavjud bo'lsa sifat variantlari ko'rsatiladi.",
            "Private yoki login talab qilinadigan postlarda aniq xato kodi chiqadi.",
        ),
        faq=(
            FaqItem(
                question="Instagram posti topilmasa nima bo'ladi?",
                answer="Sahifa xatolik kartasida izoh va error code ko'rsatadi, server esa qulab tushmaydi.",
            ),
            FaqItem(
                question="Carousel rasm postlari qo'llab-quvvatlanadimi?",
                answer="Ha. Agar postda rasmlar bo'lsa ular images bo'limida alohida ko'rsatiladi.",
            ),
        ),
        keywords=("instagram downloader", "instagram reels", "instagram carousel", "instagram post"),
    ),
    ProviderPage(
        key="tiktok",
        slug="tiktok-video-downloader",
        label="TikTok",
        hero_title="TikTok media variantlarini tez toping va yuklab olish tugmalarini oling",
        hero_description=(
            "TikTok URL kiriting va mavjud video variantlari, audio hamda subtitle bo'lsa shu sahifada "
            "darhol ko'ring."
        ),
        meta_title="TikTok Video Downloader | Video, audio va subtitle ko'rish",
        meta_description=(
            "TikTok media variantlari uchun chiroyli va SEO-friendly downloader sahifasi. Havola kiriting "
            "va mavjud video, audio va subtitle natijalarini oling."
        ),
        badge="TikTok downloader",
        placeholder="https://www.tiktok.com/@user/video/1234567890",
        example_url="https://www.tiktok.com/@scout2015/video/6718335390845095173",
        accent_start="#1ee3cf",
        accent_end="#ff4365",
        glow_tint="rgba(30, 227, 207, 0.2)",
        summary=(
            "TikTok sahifasi mavjud video variantlari va audio natijalarini tez ko'rsatadigan tezkor "
            "UI bilan tayyorlangan."
        ),
        features=(
            "Watermarksiz variant topilsa shu havola ustun ko'rsatiladi.",
            "Audio-only format mavjud bo'lsa alohida blokda chiqadi.",
            "Xato holatida code va tushunarli izoh beriladi.",
        ),
        faq=(
            FaqItem(
                question="TikTok natijalari nega ba'zan vaqtinchalik havola bilan keladi?",
                answer=(
                    "Ba'zi CDN havolalari imzolangan bo'ladi. Shunda sayt stream proxy orqali faylni uzatadi."
                ),
            ),
            FaqItem(
                question="Subtitle bo'lsa qayerda chiqadi?",
                answer="Agar subtitle topilsa u alohida subtitles bo'limida ko'rsatiladi.",
            ),
        ),
        keywords=("tiktok downloader", "tiktok video", "tiktok audio", "tiktok subtitle"),
    ),
    ProviderPage(
        key="facebook",
        slug="facebook-video-downloader",
        label="Facebook",
        hero_title="Facebook videolarini umumiy extractor orqali ajrating",
        hero_description=(
            "Facebook havolalarini ham shu interfeysda tekshirib, mavjud sifatlar va media variantlarini "
            "ko'rishingiz mumkin."
        ),
        meta_title="Facebook Video Downloader | Mavjud sifatlarni ko'rish",
        meta_description=(
            "Facebook video downloader sahifasi. Havolani kiriting va mavjud MP4, audio yoki boshqa media "
            "variantlarini ko'ring."
        ),
        badge="Facebook downloader",
        placeholder="https://www.facebook.com/watch/?v=...",
        example_url="https://www.facebook.com/watch/?v=10153231379946729",
        accent_start="#4d8dff",
        accent_end="#7cc5ff",
        glow_tint="rgba(77, 141, 255, 0.22)",
        summary=(
            "Facebook sahifasi generic extractor bilan ishlaydi va topilgan formatlarni shu UI da "
            "standart ko'rinishda beradi."
        ),
        features=(
            "Formatlar bir xil JSON contract asosida ko'rsatiladi.",
            "Proxy talab qilinsa stream endpoint avtomatik ishlatiladi.",
            "Error code va foydalanuvchi uchun sodda xabar mavjud.",
        ),
        faq=(
            FaqItem(
                question="Facebook uchun ham alohida sahifa nega kerak?",
                answer="Bu SEO va foydalanuvchi tajribasi uchun. Har platforma o'ziga mos meta va matn oladi.",
            ),
            FaqItem(
                question="Barcha havolalar ishlaydimi?",
                answer="Sahifa extractor topgan natijani ko'rsatadi. Private yoki cheklangan media alohida xato beradi.",
            ),
        ),
        keywords=("facebook downloader", "facebook video", "facebook mp4"),
    ),
    ProviderPage(
        key="x",
        slug="x-video-downloader",
        label="X / Twitter",
        hero_title="X va Twitter videolarini shu interfeysda yuklab olishga tayyorlang",
        hero_description=(
            "X yoki Twitter havolasini kiriting va mavjud video variantlari, audio yoki subtitle "
            "topilsa bitta natija kartasida ko'ring."
        ),
        meta_title="X Video Downloader | Twitter media linklari uchun tezkor sahifa",
        meta_description=(
            "X va Twitter media uchun SEO-friendly downloader sahifasi. Havolani kiritib, mavjud media "
            "variantlarini ko'ring."
        ),
        badge="X downloader",
        placeholder="https://x.com/username/status/1234567890",
        example_url="https://x.com/Interior/status/463440424141459456",
        accent_start="#dfe5f2",
        accent_end="#8aa0c2",
        glow_tint="rgba(138, 160, 194, 0.22)",
        summary=(
            "X sahifasi ham ayni extractor oqimi bilan ishlaydi va result panelni barcha platformalar bilan "
            "bir xil tutadi."
        ),
        features=(
            "Minimal, tez va bir xil natija kartasi beradi.",
            "Mavjud bo'lsa bir nechta sifatni ko'rsatadi.",
            "API docs va Telegram promo sahifaning o'zida qoladi.",
        ),
        faq=(
            FaqItem(
                question="X sahifasi nimasi bilan foydali?",
                answer="Alohida landing sahifa bo'lgani uchun SEO va ijtimoiy preview sifatliroq chiqadi.",
            ),
            FaqItem(
                question="Audio yoki subtitle bo'lmasa-chi?",
                answer="Sahifa faqat mavjud bo'limlarni ko'rsatadi va qolganlarini yashiradi.",
            ),
        ),
        keywords=("x downloader", "twitter downloader", "twitter video"),
    ),
)


def list_platform_pages() -> tuple[ProviderPage, ...]:
    return PLATFORM_PAGES


def get_platform_page(page_slug: str) -> ProviderPage | None:
    for page in PLATFORM_PAGES:
        if page.slug == page_slug:
            return page
    return None


def build_home_context(request: Request) -> dict[str, Any]:
    canonical_url = str(request.url_for("home_page"))
    return {
        "site_name": SITE_NAME,
        "site_description": SITE_DESCRIPTION,
        "platform_pages": PLATFORM_PAGES,
        "telegram_url": TELEGRAM_URL,
        "api_docs_url": "/docs",
        "api_schema_url": "/openapi.json",
        "body_class": "theme-home",
        "accent_start": "#53c5ff",
        "accent_end": "#ffd66b",
        "glow_tint": "rgba(83, 197, 255, 0.22)",
        "seo": {
            "title": "OdeGate Media Downloader | YouTube, Instagram, TikTok va boshqa platformalar",
            "description": SITE_DESCRIPTION,
            "keywords": ", ".join(
                (
                    "media downloader",
                    "youtube downloader",
                    "instagram downloader",
                    "tiktok downloader",
                    "video audio subtitle",
                )
            ),
            "canonical_url": canonical_url,
            "og_image": str(request.url_for("static", path="og-card.svg")),
        },
        "structured_data": json.dumps(
            [
                {
                    "@context": "https://schema.org",
                    "@type": "WebSite",
                    "name": SITE_NAME,
                    "url": canonical_url,
                    "description": SITE_DESCRIPTION,
                },
                {
                    "@context": "https://schema.org",
                    "@type": "ItemList",
                    "name": "Supported platform pages",
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": index,
                            "url": str(request.url_for("platform_page", page_slug=page.slug)),
                            "name": page.meta_title,
                        }
                        for index, page in enumerate(PLATFORM_PAGES, start=1)
                    ],
                },
            ],
            ensure_ascii=False,
        ),
        "panel_badge": "All-in-one downloader",
        "panel_title": "Bitta havola kiriting va tayyor yuklab olish variantlarini oling",
        "panel_description": (
            "Sifatlar, audio, subtitles va rasmlar shu oynada chiqadi. Agar xatolik bo'lsa, sahifa "
            "tushunarli xabar va error code ko'rsatadi."
        ),
        "panel_placeholder": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "panel_example_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }


def build_platform_context(request: Request, page: ProviderPage) -> dict[str, Any]:
    canonical_url = str(request.url_for("platform_page", page_slug=page.slug))
    faq_entities = [
        {
            "@type": "Question",
            "name": item.question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.answer,
            },
        }
        for item in page.faq
    ]
    structured_data = [
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": page.meta_title,
            "url": canonical_url,
            "description": page.meta_description,
        },
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": page.meta_title,
            "applicationCategory": "MultimediaApplication",
            "operatingSystem": "Web",
            "description": page.summary,
            "url": canonical_url,
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities,
        },
    ]

    return {
        "site_name": SITE_NAME,
        "site_description": SITE_DESCRIPTION,
        "platform_pages": PLATFORM_PAGES,
        "telegram_url": TELEGRAM_URL,
        "api_docs_url": "/docs",
        "api_schema_url": "/openapi.json",
        "body_class": f"theme-{page.key}",
        "accent_start": page.accent_start,
        "accent_end": page.accent_end,
        "glow_tint": page.glow_tint,
        "seo": {
            "title": page.meta_title,
            "description": page.meta_description,
            "keywords": ", ".join(page.keywords),
            "canonical_url": canonical_url,
            "og_image": str(request.url_for("static", path="og-card.svg")),
        },
        "structured_data": json.dumps(structured_data, ensure_ascii=False),
        "page": page,
        "panel_badge": page.badge,
        "panel_title": page.hero_title,
        "panel_description": page.hero_description,
        "panel_placeholder": page.placeholder,
        "panel_example_url": page.example_url,
    }
