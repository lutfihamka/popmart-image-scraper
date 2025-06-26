# Pop Mart Image Scraper

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A Python script to download high-resolution Pop Mart product images from [The Toy Pool](https://thetoypool.com/pop-mart/all/) with intelligent naming.

## 🔍 New Filename Format
```
[<character>] <series> - <main_name> (<small_text>).jpg
```
**Example:**
```
[Oipippi] Joyfulness Series - Hiding Myself (2024, Secret Figure).jpg
[Dimoo] Space Travel Series - Astronaut (2023 Special Edition).jpg
```

## ✨ Features
- **Smart Naming**: Automatic filename generation with character-first format
- **High-Resolution**: Downloads from original source URLs
- **Reliable Downloads**: 3 retry attempts per image with 30s timeout
- **Progress Tracking**: Real-time logging with success/failure reports
- **Duplicate Prevention**: Skips existing files automatically

## 🛠 Installation
```bash
pip install requests beautifulsoup4
```

## 🚀 Usage
```bash
python pop_mart_scraper.py
```

**Menu Options:**
1. **Download ALL images** - Full scraping session
2. **Test single download** - Verify with one image first
3. **Exit**

## 📂 Sample Output Structure
```
pop_mart_images/
├── [Oipippi] Joyfulness Series - Hiding Myself (2024, Secret Figure).jpg
├── [Dimoo] Space Travel Series - Astronaut (2023 Special Edition).jpg
└── [Molly] Sweet Home Series - Birthday Girl (2022 Blind Box).jpg
```

## ⚠️ Troubleshooting
**Common Issues:**
- Timeout errors: Automatically retries 3 times
- Invalid filenames: Automatic special character removal
- Network issues: Check `pop_mart_scraper.log` for details

**Pro Tip:**  
Always run the single-image test first to verify your setup!

## 📜 License
MIT License - Free for personal/non-commercial use