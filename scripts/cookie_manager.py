from __future__ import annotations

import argparse
import json
import shutil
import webbrowser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Platform:
    key: str
    title: str
    login_url: str
    export_hint: str


PLATFORMS: tuple[Platform, ...] = (
    Platform(
        key="google",
        title="Google / YouTube",
        login_url="https://accounts.google.com/ServiceLogin?service=youtube",
        export_hint="Google/YouTube cookie faylini Netscape cookies.txt yoki JSON formatda export qiling.",
    ),
    Platform(
        key="instagram",
        title="Instagram",
        login_url="https://www.instagram.com/accounts/login/",
        export_hint="Instagram cookie faylini Netscape cookies.txt yoki JSON formatda export qiling.",
    ),
    Platform(
        key="tiktok",
        title="TikTok",
        login_url="https://www.tiktok.com/login",
        export_hint="TikTok cookie faylini Netscape cookies.txt yoki JSON formatda export qiling.",
    ),
)


def main() -> int:
    args = parse_args()
    cookies_dir = args.cookies_dir.resolve()
    cookies_dir.mkdir(parents=True, exist_ok=True)

    print("Cookie Manager CLI")
    print(f"Saqlash papkasi: {cookies_dir}")
    print()

    selected = [platform for platform in PLATFORMS if not args.platforms or platform.key in args.platforms]
    if not selected:
        print("Tanlangan platforma topilmadi.")
        return 1

    for platform in selected:
        process_platform(platform, cookies_dir, no_browser=args.no_browser)
        print()

    print("Jarayon tugadi.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Platformalar bo'yicha cookie fayllarni boshqaradi. "
            "Skript login sahifasini ochadi va siz export qilgan cookie faylni saqlaydi."
        )
    )
    parser.add_argument(
        "--cookies-dir",
        default="cookies",
        type=Path,
        help="Cookie fayllar saqlanadigan papka. Default: ./cookies",
    )
    parser.add_argument(
        "--platforms",
        nargs="*",
        choices=[platform.key for platform in PLATFORMS],
        help="Faqat tanlangan platformalarni yuritish uchun.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Login sahifasini brauzerda avtomatik ochmaslik uchun.",
    )
    return parser.parse_args()


def process_platform(platform: Platform, cookies_dir: Path, *, no_browser: bool) -> None:
    print(f"[{platform.title}]")
    existing = find_existing_cookie(cookies_dir, platform.key)

    if existing:
        print(f"Mavjud cookie fayl: {existing.name}")
        action = ask_choice(
            prompt="Yangilaysizmi yoki o'tkazib yuborasizmi?",
            choices={
                "r": "Refresh",
                "s": "Skip",
                "p": "Path ko'rsatish",
            },
            default="s",
        )
        if action == "p":
            print(f"To'liq manzil: {existing}")
            action = ask_choice(
                prompt="Endi nima qilamiz?",
                choices={"r": "Refresh", "s": "Skip"},
                default="s",
            )
        if action == "s":
            print("Skip qilindi.")
            return

    print(platform.export_hint)
    proceed_manual_login(platform, no_browser=no_browser)

    exported = ask_cookie_file_path(platform)
    cookie_format = detect_cookie_format(exported)
    destination = store_cookie_file(exported, cookies_dir, platform.key, cookie_format)
    print(f"Cookie saqlandi: {destination}")
    print(f"Format: {cookie_format}")


def find_existing_cookie(cookies_dir: Path, platform_key: str) -> Path | None:
    for ext in (".txt", ".json"):
        candidate = cookies_dir / f"{platform_key}{ext}"
        if candidate.exists():
            return candidate
    return None


def proceed_manual_login(platform: Platform, *, no_browser: bool) -> None:
    print("1. Oddiy brauzeringizda login sahifasi ochiladi.")
    print("2. Login, parol, 2FA va captcha jarayonlarini o'zingiz yakunlaysiz.")
    print("3. Keyin cookie faylni export qilib shu terminalga yo'lini berasiz.")

    if not no_browser:
        try:
            webbrowser.open(platform.login_url, new=2)
            print(f"Brauzer ochildi: {platform.login_url}")
        except Exception as exc:
            print(f"Brauzerni avtomatik ochib bo'lmadi: {exc}")
            print(f"URL ni qo'lda oching: {platform.login_url}")
    else:
        print(f"Brauzer ochilmadi. URL ni qo'lda oching: {platform.login_url}")

    input("Login tugagach va cookie export tayyor bo'lgach Enter bosing...")


def ask_cookie_file_path(platform: Platform) -> Path:
    while True:
        raw = input(f"{platform.title} uchun export qilingan cookie fayl yo'lini kiriting: ").strip().strip('"')
        candidate = Path(raw).expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate
        print("Fayl topilmadi. Qayta urinib ko'ring.")


def detect_cookie_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        validate_json_cookie_file(path)
        return "json"
    validate_netscape_cookie_file(path)
    return "netscape"


def validate_json_cookie_file(path: Path) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON cookie fayli yaroqsiz: {exc}") from exc

    if not isinstance(payload, (list, dict)):
        raise ValueError("JSON cookie fayli list yoki dict bo'lishi kerak.")


def validate_netscape_cookie_file(path: Path) -> None:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    meaningful = [line for line in lines if line.strip()]
    if not meaningful:
        raise ValueError("Cookie fayl bo'sh.")

    first = meaningful[0]
    if first.startswith("# Netscape HTTP Cookie File"):
        return

    for line in meaningful:
        if line.startswith("#"):
            continue
        if len(line.split("\t")) >= 7:
            return

    raise ValueError("Netscape cookies.txt formati aniqlanmadi.")


def store_cookie_file(source: Path, cookies_dir: Path, platform_key: str, cookie_format: str) -> Path:
    extension = ".json" if cookie_format == "json" else ".txt"
    destination = cookies_dir / f"{platform_key}{extension}"
    shutil.copy2(source, destination)
    return destination


def ask_choice(prompt: str, choices: dict[str, str], default: str) -> str:
    options = ", ".join(f"{key}={label}" for key, label in choices.items())
    while True:
        raw = input(f"{prompt} [{options}] (default: {default}): ").strip().lower()
        if not raw:
            return default
        if raw in choices:
            return raw
        print("Noto'g'ri tanlov. Qayta urinib ko'ring.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Xatolik: {exc}")
        raise SystemExit(1)
