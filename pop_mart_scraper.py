import os
import requests
from bs4 import BeautifulSoup
import logging
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class PopMartScraper:
    def __init__(self, base_url, output_dir='pop_mart_images'):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.failed_downloads = []
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': base_url
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_page_content(self, url):
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_year_and_type(self, small_text):
        """Extract year and type from small_text"""
        if not small_text:
            return None, 0
        
        # Extract year (first 4 characters)
        year = small_text[:4] if len(small_text) >= 4 and small_text[:4].isdigit() else None
        
        # Determine type
        small_text_lower = small_text.lower()
        if "super secret" in small_text_lower:
            return year, 3
        elif "secret" in small_text_lower:
            return year, 2
        else:
            return year, 0
    
    def parse_metadata_only(self, html_content):
        """Parse image data for metadata only (no downloading)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        image_containers = soup.find_all('div', class_='data-small-xlong')
        
        metadata_list = []
        
        for container in image_containers:
            try:
                # Get HIGH-RES image URL from <a href>
                a_tag = container.find('a', href=True)
                if not a_tag:
                    continue
                
                img_url = a_tag['href']
                
                # Get THUMBNAIL image URL from <img> tag with class "data-img lazy" inside data-top
                data_top = container.find('div', class_='data-top')
                img_tag = data_top.find('img', class_='data-img lazy') if data_top else None
                
                thumbnail_url = ""
                if img_tag:
                    # Try data-original first, fallback to src if empty
                    if 'data-original' in img_tag.attrs and img_tag['data-original']:
                        thumbnail_url = img_tag['data-original']
                    elif 'src' in img_tag.attrs:
                        thumbnail_url = img_tag['src']
                
                # Get name parts
                data_bottom = container.find('div', class_='data-bottom')
                if not data_bottom:
                    continue
                
                # Extract components
                series_tag = data_bottom.find('a', href=lambda x: x and '/pop-mart/series/' in x)
                series = series_tag.get_text(strip=True) if series_tag else ""
                
                main_name_tag = data_bottom.find('b')
                main_name = main_name_tag.get_text(strip=True) if main_name_tag else ""
                
                character_tag = data_bottom.find('a', href=lambda x: x and '/pop-mart/line/' in x)
                character = character_tag.get_text(strip=True) if character_tag else ""
                
                small_text_tag = data_bottom.find('span', class_='data-smallt')
                small_text = small_text_tag.get_text(strip=True) if small_text_tag else ""
                
                # Extract year and type
                year, item_type = self.extract_year_and_type(small_text)
                
                metadata_list.append({
                    'character': character,
                    'series': series,
                    'main_name': main_name,
                    'image_url': img_url,
                    'thumbnail_url': thumbnail_url,
                    'year': year,
                    'type': item_type,
                    'created_at': datetime.now()
                })
                
            except Exception as e:
                logging.error(f"Error parsing metadata from container: {e}")
                continue
                
        return metadata_list
    
    def generate_sql_file(self, filename='popmart_items.sql'):
        """Generate MySQL SQL file with metadata"""
        logging.info(f"Starting metadata extraction for SQL generation")
        
        html_content = self.get_page_content(self.base_url)
        if not html_content:
            logging.error("Failed to fetch the main page")
            return
        
        metadata_list = self.parse_metadata_only(html_content)
        if not metadata_list:
            logging.warning("No metadata found on the page")
            return
        
        # Generate SQL file
        with open(filename, 'w', encoding='utf-8') as f:
            # Write CREATE TABLE statement
            f.write("""-- PopMart Items Database
-- Generated on {}

CREATE TABLE IF NOT EXISTS popmart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `character` VARCHAR(255),
    series VARCHAR(255),
    main_name VARCHAR(255),
    image_url TEXT,
    thumbnail_url TEXT,
    `year` INT,
    `type` TINYINT COMMENT '0=normal, 2=secret, 3=super secret',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Write INSERT statements
            f.write("-- Insert data\n")
            for item in metadata_list:
                year_value = item['year'] if item['year'] else 'NULL'
                created_at = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                f.write(f"""INSERT INTO popmart_items (`character`, series, main_name, image_url, thumbnail_url, `year`, `type`, created_at) VALUES 
('{self.escape_sql_string(item['character'])}', '{self.escape_sql_string(item['series'])}', '{self.escape_sql_string(item['main_name'])}', '{self.escape_sql_string(item['image_url'])}', '{self.escape_sql_string(item['thumbnail_url'])}', {year_value}, {item['type']}, '{created_at}');
""")
        
        logging.info(f"SQL file generated: {filename} with {len(metadata_list)} records")
        print(f"✅ SQL file created: {filename} ({len(metadata_list)} records)")
    
    def generate_xlsx_file(self, filename='popmart_items.xlsx'):
        """Generate XLSX file with metadata"""
        logging.info(f"Starting metadata extraction for XLSX generation")
        
        html_content = self.get_page_content(self.base_url)
        if not html_content:
            logging.error("Failed to fetch the main page")
            return
        
        metadata_list = self.parse_metadata_only(html_content)
        if not metadata_list:
            logging.warning("No metadata found on the page")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(metadata_list)
        
        # Add auto-increment ID column
        df.insert(0, 'id', range(1, len(df) + 1))
        
        # Save to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        logging.info(f"XLSX file generated: {filename} with {len(metadata_list)} records")
        print(f"✅ XLSX file created: {filename} ({len(metadata_list)} records)")
    
    def escape_sql_string(self, value):
        """Escape single quotes for SQL"""
        if value is None:
            return ""
        return str(value).replace("'", "''")
    
    def parse_image_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        image_containers = soup.find_all('div', class_='data-small-xlong')
        
        image_data = []
        
        for container in image_containers:
            try:
                # Get HIGH-RES image URL from <a href>
                a_tag = container.find('a', href=True)
                if not a_tag:
                    continue
                
                img_url = a_tag['href']
                
                # Get name parts
                data_bottom = container.find('div', class_='data-bottom')
                if not data_bottom:
                    continue
                
                # Extract components for filename
                series_tag = data_bottom.find('a', href=lambda x: x and '/pop-mart/series/' in x)
                series = series_tag.get_text(strip=True) if series_tag else ""
                
                main_name_tag = data_bottom.find('b')
                main_name = main_name_tag.get_text(strip=True) if main_name_tag else ""
                
                character_tag = data_bottom.find('a', href=lambda x: x and '/pop-mart/line/' in x)
                character = character_tag.get_text(strip=True) if character_tag else ""
                
                small_text_tag = data_bottom.find('span', class_='data-smallt')
                small_text = small_text_tag.get_text(strip=True) if small_text_tag else ""
                
                # Construct filename with series first
                filename_parts = []
                if character:
                    filename_parts.append(f"[{character}]")
                if series:
                    filename_parts.append(series)
                if main_name:
                    filename_parts.append(f"- {main_name}")
                if small_text:
                    filename_parts.append(f"({small_text})")

                filename = " ".join(filter(None, filename_parts)) + ".jpg"
                filename = self.sanitize_filename(filename)
                
                image_data.append({
                    'url': img_url,
                    'filename': filename
                })
                
            except Exception as e:
                logging.error(f"Error parsing image container: {e}")
                continue
                
        return image_data
    
    def sanitize_filename(self, filename):
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()
    
    def download_image(self, img_url, filename):
        filepath = os.path.join(self.output_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            logging.info(f"Skipping {filename} - already exists")
            return True
        
        max_attempts = 3
        timeout = 30  # Increased timeout
        
        for attempt in range(max_attempts):
            try:
                response = self.session.get(img_url, stream=True, timeout=timeout)
                response.raise_for_status()
                
                # Verify image content
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    logging.warning(f"URL {img_url} is not an image (Content-Type: {content_type})")
                    return False
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logging.info(f"Successfully downloaded {filename} (attempt {attempt + 1})")
                return True
                
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout on attempt {attempt + 1} for {filename}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retrying
                    continue
                error_msg = f"Timeout after {max_attempts} attempts"
                logging.error(f"Failed to download {filename}: {error_msg}")
                self.failed_downloads.append({
                    'url': img_url,
                    'filename': filename,
                    'error': error_msg
                })
                return False
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Failed to download {img_url}: {error_msg}")
                self.failed_downloads.append({
                    'url': img_url,
                    'filename': filename,
                    'error': error_msg
                })
                return False
    
    def download_single_image(self):
        """Download just one image for testing purposes"""
        html_content = self.get_page_content(self.base_url)
        if not html_content:
            logging.error("Failed to fetch the main page")
            return
        
        image_data = self.parse_image_data(html_content)
        if not image_data:
            logging.warning("No images found on the page")
            return
        
        first_image = image_data[0]
        print(f"\nTest downloading: {first_image['filename']}")
        print(f"From URL: {first_image['url']}")
        
        success = self.download_image(first_image['url'], first_image['filename'])
        if success:
            print("Test download SUCCESSFUL!")
        else:
            print("Test download FAILED (check logs for details)")
    
    def scrape_all_images(self, max_workers=5):
        logging.info(f"Starting scrape of {self.base_url}")
        
        html_content = self.get_page_content(self.base_url)
        if not html_content:
            logging.error("Failed to fetch the main page")
            return
        
        image_data = self.parse_image_data(html_content)
        if not image_data:
            logging.warning("No images found on the page")
            return
        
        logging.info(f"Found {len(image_data)} images to download")
        
        # Reset failed downloads list
        self.failed_downloads = []
        
        # Download images with threading
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for img in image_data:
                futures.append(executor.submit(
                    self.download_image, 
                    img['url'], 
                    img['filename']
                ))
                time.sleep(0.5)  # Rate limiting
            
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
        
        # Print summary
        logging.info(f"\nDownload completed: {success_count}/{len(image_data)} successful")
        if self.failed_downloads:
            logging.warning("Failed downloads:")
            for item in self.failed_downloads:
                logging.warning(f"- {item['filename']}: {item['error']}")

def main():
    print("Pop Mart Image Scraper")
    print("=" * 50)
    
    url = "https://thetoypool.com/pop-mart/all/"
    output_dir = input(f"Enter output directory [default: pop_mart_images]: ") or "pop_mart_images"
    
    scraper = PopMartScraper(url, output_dir)
    
    while True:
        print("\nOptions:")
        print("1. Download ALL images")
        print("2. Try downloading 1 image (test)")
        print("3. Generate SQL file (metadata only)")
        print("4. Generate XLSX file (metadata only)")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            start_time = time.time()
            scraper.scrape_all_images()
            end_time = time.time()
            print(f"\nScraping completed in {end_time - start_time:.2f} seconds")
            input("Press Enter to continue...")
        elif choice == '2':
            scraper.download_single_image()
            input("Press Enter to continue...")
        elif choice == '3':
            start_time = time.time()
            scraper.generate_sql_file()
            end_time = time.time()
            print(f"\nSQL generation completed in {end_time - start_time:.2f} seconds")
            input("Press Enter to continue...")
        elif choice == '4':
            start_time = time.time()
            scraper.generate_xlsx_file()
            end_time = time.time()
            print(f"\nXLSX generation completed in {end_time - start_time:.2f} seconds")
            input("Press Enter to continue...")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
