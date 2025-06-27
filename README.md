# Pop Mart Image Scraper

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A comprehensive Python tool to scrape Pop Mart product data from [The Toy Pool](https://thetoypool.com/pop-mart/all/) with multiple export options.

## 🔍 Filename Format (Image Downloads)
```
[<character>] <series> - <main_name> (<small_text>).jpg
```
**Example:**
```
[Oipippi] Joyfulness Series - Hiding Myself (2024, Secret Figure).jpg
[Dimoo] Space Travel Series - Astronaut (2023 Special Edition).jpg
```

## ✨ Features
- **Image Downloads**: High-resolution image downloading with smart naming
- **SQL Export**: Generate MySQL-compatible `.sql` files with metadata
- **Excel Export**: Create `.xlsx` files for easy data analysis
- **Metadata Extraction**: Character, series, year, type classification, and URLs
- **Type Classification**: Auto-detect Normal (0), Secret (2), Super Secret (3) figures
- **Reliable Downloads**: 3 retry attempts per image with 30s timeout
- **Duplicate Prevention**: Skips existing files automatically

## 🗃️ Database Schema
```sql
CREATE TABLE IF NOT EXISTS popmart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `character` VARCHAR(255),
    series VARCHAR(255),
    main_name VARCHAR(255),
    image_url TEXT,           -- High-resolution image URL
    thumbnail_url TEXT,       -- Thumbnail image URL
    `year` INT,               -- Extracted from release info
    `type` TINYINT,           -- 0=normal, 2=secret, 3=super secret
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠 Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install requests beautifulsoup4 pandas openpyxl
```

## 🚀 Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run the scraper
python scrap.py
```

**Menu Options:**
1. **Download ALL images** - Full image scraping session
2. **Test single download** - Verify with one image first
3. **Generate SQL file** - Export metadata to MySQL format
4. **Generate XLSX file** - Export metadata to Excel format
5. **Exit**

## 📂 Output Examples

### Image Downloads
```
pop_mart_images/
├── [Oipippi] Joyfulness Series - Hiding Myself (2024, Secret Figure).jpg
├── [Dimoo] Space Travel Series - Astronaut (2023 Special Edition).jpg
└── [Molly] Sweet Home Series - Birthday Girl (2022 Blind Box).jpg
```

### Data Exports
```
popmart_items.sql     # MySQL database file
popmart_items.xlsx    # Excel spreadsheet
```

## 🎯 Type Classification
- **Type 0 (Normal)**: Regular figures
- **Type 2 (Secret)**: Contains "Secret Figure" in description
- **Type 3 (Super Secret)**: Contains "Super Secret Figure" in description

## ⚠️ Troubleshooting
**Common Issues:**
- Timeout errors: Automatically retries 3 times
- Invalid filenames: Automatic special character removal
- Missing virtual environment: Make sure to activate `venv`

**Dependencies:**
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `openpyxl` - Excel file generation

## 📜 License
MIT License - Free for personal/non-commercial use
