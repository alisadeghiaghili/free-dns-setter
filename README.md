<div dir="rtl">

# 🌐 Free DNS Setter

> ابزار مدیریت DNS برای کاربران ایرانی — رابط گرافیکی و خط فرمان، ساخته‌شده با Python

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://www.microsoft.com/windows)

---

[English README](README.en.md)

---

## درباره توسعه‌دهنده

**نام:** علی صادقی عقیلی
**گیت‌هاب:** [github.com/alisadeghiaghili](https://github.com/alisadeghiaghili)
**ایمیل:** [alisadeghiaghili@gmail.com](mailto:alisadeghiaghili@gmail.com)

---

## معرفی

Free DNS Setter یک ابزار ویندوزی است که با یک کلیک یا یک دستور، DNS سیستم شما را تغییر می‌دهد.
این برنامه ۹ سرویس‌دهنده DNS را در سه دستهٔ فعال پشتیبانی می‌کند و هم رابط گرافیکی **Tkinter** (راست‌چین) و هم CLI تعاملی مبتنی بر Rich دارد. رابط گرافیکی از کتابخانهٔ استاندارد Python است و dependency خارجی نمی‌خواهد.

---

## ویژگی‌ها

- **۹ سرویس‌دهنده DNS** در سه دستهٔ فعال آماده
- **رابط گرافیکی** — Tkinter با دراپ‌داون راست‌چین و توضیح هر سرویس‌دهنده (بدون dependency خارجی)
- **خط فرمان (CLI)** — منوی تعاملی TUI و دستورات مستقیم برای اسکریپت‌نویسی
- **اسنپ‌شات خودکار DNS** قبل از هر تغییر — بازگشت ایمن به DHCP
- **UAC Elevation** — راه‌اندازی مجدد خودکار با دسترسی Administrator
- بررسی کد بازگشتی WMI — نمایش خطای واقعی به جای شکست بی‌صدا
- تمام IPهای سرویس‌دهنده‌های داخلی **تأییدشدهٔ عمومی** (از طریق PTR / رزولوشن عمومی)
- معماری لایه‌ای (core / ui / cli / utils) — هر لایه مستقل و قابل تست

---

## سرویس‌دهنده‌های DNS

| سرویس‌دهنده | دسته        | Primary          | Secondary         |
|-------------|-------------|------------------|-------------------|
| Shecan      | رفع تحریم   | 178.22.122.100   | 185.51.200.2      |
| Begzar      | رفع تحریم   | 185.55.224.24    | 185.55.226.26     |
| Electro     | رفع تحریم   | 78.157.42.100    | 78.157.42.101     |
| HostIran    | رفع تحریم   | 37.27.81.177     | 5.144.130.130     |
| AsiaTech    | گیمینگ      | 185.98.113.113   | 185.98.114.114    |
| Cloudflare  | عمومی       | 1.1.1.1          | 1.0.0.1           |
| Google      | عمومی       | 8.8.8.8          | 8.8.4.4           |
| Quad9       | عمومی       | 9.9.9.9          | 149.112.112.112   |
| DNS Pro     | عمومی       | 87.107.110.109   | 87.107.110.110    |

> دستهٔ «رفع فیلتر» فعلاً سرویس‌دهندهٔ تأییدشدهٔ عمومی ندارد (403 با IP خصوصی کار نمی‌کرد).
> با پیدا شدن IP عمومی معتبر به‌سادگی اضافه می‌شود.

---

## پیش‌نیازها

- ویندوز ۱۰ یا ۱۱
- Python نسخه ۳.۱۱ به بالا
- دسترسی Administrator

```bash
pip install wmi rich
```
(GUI فقط به `wmi` نیاز دارد؛ `rich` برای CLI است. `Tkinter` همراه خود Python است.)

---

## نحوه استفاده

### رابط گرافیکی (GUI)

```bash
python -m dns_changer.main
```

> **حتماً به عنوان Administrator اجرا کنید.** در صورت نبود دسترسی، خودکار از طریق UAC دوباره باز می‌شود.

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
│   ├── providers.py         # تعریف سرویس‌دهنده‌ها (برای افزودن، فقط اینجا)
│   ├── adapter.py           # تنها فایلی که با WMI کار می‌کند
│   └── dns_service.py       # منطق اصلی + state machine
├── ui/
│   └── main_window.py       # رابط Tkinter (راست‌چین)
├── cli/
│   └── dns_cli.py           # CLI تعاملی و مستقیم
└── utils/
    └── privileges.py        # مدیریت دسترسی Administrator
```

---

## مشارکت در توسعه

۱. ریپازیتوری را Fork کنید: [github.com/alisadeghiaghili/free-dns-setter](https://github.com/alisadeghiaghili/free-dns-setter)
۲. یک branch جدید برای تغییرات خود بسازید
۳. با پیام‌های توصیفی طبق [Conventional Commits](https://www.conventionalcommits.org/) commit کنید
۴. Pull Request ارسال کنید

برای اضافه‌کردن سرویس‌دهنده جدید فقط یک entry به `core/providers.py` اضافه کنید — هیچ فایل دیگری نیاز به تغییر ندارد.

---

## لایسنس

این پروژه تحت مجوز [Apache License 2.0](LICENSE) منتشر شده است.

</div>
