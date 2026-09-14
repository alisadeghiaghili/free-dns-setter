<div dir="rtl">

# 🌐 DNS Changer

> ابزار مدیریت DNS برای کاربران ایرانی — رابط گرافیکی و خط فرمان، ساخته‌شده با Python

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://www.microsoft.com/windows)

---

[English README](README.en.md)

---

## درباره توسعه‌دهنده

**نام:** علی صادقی آقیلی
**گیت‌هاب:** [github.com/alisadeghiaghili](https://github.com/alisadeghiaghili)
**ایمیل:** [alisadeghiaghili@gmail.com](mailto:alisadeghiaghili@gmail.com)

---

## معرفی

DNS Changer یک ابزار ویندوزی است که با یک کلیک یا یک دستور، DNS سیستم شما را تغییر می‌دهد.
این برنامه ۱۰ سرویس‌دهنده DNS را در چهار دسته پشتیبانی می‌کند و هم رابط گرافیکی PyQt5 و هم CLI تعاملی مبتنی بر Rich دارد.

---

## ویژگی‌ها

- **۱۰ سرویس‌دهنده DNS** در چهار دسته آماده
- **رابط گرافیکی** — PyQt5 با منوی دسته‌بندی‌شده و توضیح هر سرویس‌دهنده
- **خط فرمان (CLI)** — منوی تعاملی TUI و دستورات مستقیم برای اسکریپت‌نویسی
- **اسنپ‌شات خودکار DNS** قبل از هر تغییر — بازگشت ایمن به DHCP
- **UAC Elevation** — راه‌اندازی مجدد خودکار با دسترسی Administrator
- بررسی کد بازگشتی WMI — نمایش خطای واقعی به جای شکست بی‌صدا
- معماری لایه‌ای (core / ui / cli / utils) — هر لایه مستقل و قابل تست

---

## سرویس‌دهنده‌های DNS

| سرویس‌دهنده | دسته        | Primary          | Secondary         |
|-------------|-------------|------------------|-------------------|
| Shecan      | رفع تحریم   | 178.22.122.100   | 185.51.200.2      |
| Begzar      | رفع تحریم   | 185.55.226.26    | 185.55.225.25     |
| Electro     | رفع تحریم   | 78.157.42.100    | 78.157.42.101     |
| HostIran    | رفع تحریم   | 172.29.0.100     | 172.29.2.100      |
| 403         | رفع فیلتر   | 10.202.10.202    | 10.202.10.102     |
| Radar Game  | گیمینگ      | 10.202.10.10     | 10.202.10.11      |
| AsiaTech    | گیمینگ      | 185.98.113.113   | 185.98.114.114    |
| Cloudflare  | عمومی       | 1.1.1.1          | 1.0.0.1           |
| Google      | عمومی       | 8.8.8.8          | 8.8.4.4           |
| Quad9       | عمومی       | 9.9.9.9          | 149.112.112.112   |

---

## پیش‌نیازها

- ویندوز ۱۰ یا ۱۱
- Python نسخه ۳.۱۱ به بالا
- دسترسی Administrator

```bash
pip install PyQt5 rich
```

---

## نحوه استفاده

### رابط گرافیکی (GUI)

```bash
python -m dns_changer.main
```

یا فایل اجرایی آماده را دانلود کنید:
[دانلود DNS Changer (exe)](https://github.com/alisadeghiaghili/ShecanDNSSetter/releases/download/pre-release/dnsSetter.exe)

> **حتماً به عنوان Administrator اجرا کنید.**

### خط فرمان (CLI)

```bash
# منوی تعاملی
python -m dns_changer.cli.dns_cli

# دستورات مستقیم
python -m dns_changer.cli.dns_cli list              # نمایش همه سرویس‌دهنده‌ها
python -m dns_changer.cli.dns_cli status            # وضعیت DNS فعلی
python -m dns_changer.cli.dns_cli set Shecan        # فعال‌کردن یک سرویس‌دهنده
python -m dns_changer.cli.dns_cli reset             # بازگشت به DHCP
```

---

## ساختار پروژه

```
dns_changer/
├── main.py                  # نقطه ورود GUI
├── core/
│   ├── providers.py         # تعریف سرویس‌دهنده‌ها
│   ├── adapter.py           # تنها فایلی که با WMI کار می‌کند
│   └── dns_service.py       # منطق اصلی + state machine
├── ui/
│   └── main_window.py       # رابط PyQt5
├── cli/
│   └── dns_cli.py           # CLI تعاملی و مستقیم
└── utils/
    └── privileges.py        # مدیریت دسترسی Administrator
```

---

## مشارکت در توسعه

۱. ریپازیتوری را Fork کنید: [github.com/alisadeghiaghili/ShecanDNSSetter](https://github.com/alisadeghiaghili/ShecanDNSSetter)
۲. یک branch جدید برای تغییرات خود بسازید
۳. با پیام‌های توصیفی طبق [Conventional Commits](https://www.conventionalcommits.org/) commit کنید
۴. Pull Request ارسال کنید

برای اضافه‌کردن سرویس‌دهنده جدید فقط یک خط به `core/providers.py` اضافه کنید — هیچ فایل دیگری نیاز به تغییر ندارد.

---

## لایسنس

این پروژه تحت مجوز [Apache License 2.0](LICENSE) منتشر شده است.

</div>
