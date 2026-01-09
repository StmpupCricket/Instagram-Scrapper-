import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import time

def scrape_instagram_videos(username, max_scrolls=10):
    """Scrape video links from Instagram profile"""
    
    videos_data = {
        "profile": f"@{username}",
        "scraped_at": datetime.now().isoformat(),
        "total_videos": 0,
        "videos": []
    }
    
    with sync_playwright() as p:
        # Launch browser in GitHub Actions compatible mode
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        
        try:
            # Go to profile page
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"Accessing: {profile_url}")
            page.goto(profile_url, wait_until='networkidle', timeout=60000)
            time.sleep(5)
            
            # Handle login popup if appears
            try:
                not_now_btn = page.locator('button:has-text("Not Now")')
                if not_now_btn.count() > 0:
                    not_now_btn.first.click()
                    time.sleep(2)
            except:
                pass
            
            # Scroll to load content
            print("Scrolling to load videos...")
            video_urls_set = set()
            
            for i in range(max_scrolls):
                # Find all video elements
                video_elements = page.locator('video').all()
                
                for idx, video in enumerate(video_elements):
                    try:
                        src = video.get_attribute('src')
                        if src and src not in video_urls_set:
                            # Try to get post URL
                            parent_link = video.locator('xpath=ancestor::a[contains(@href, "/p/")]')
                            post_url = None
                            if parent_link.count() > 0:
                                href = parent_link.get_attribute('href')
                                if href:
                                    post_url = f"https://www.instagram.com{href}" if href.startswith('/') else href
                            
                            video_data = {
                                "url": src,
                                "post_url": post_url,
                                "scraped_at": datetime.now().isoformat()
                            }
                            videos_data["videos"].append(video_data)
                            video_urls_set.add(src)
                            print(f"Found video {len(video_urls_set)}: {src[:80]}...")
                    except:
                        continue
                
                # Scroll down
                page.evaluate("""
                    window.scrollBy(0, window.innerHeight * 2);
                """)
                time.sleep(3)  # Increased delay for Instagram
                
                # Check if we've reached the end
                new_height = page.evaluate("document.body.scrollHeight")
                current_pos = page.evaluate("window.scrollY + window.innerHeight")
                
                if current_pos >= new_height - 100:
                    print("Reached end of page")
                    break
                
                print(f"Scroll {i+1}/{max_scrolls} complete")
            
            videos_data["total_videos"] = len(videos_data["videos"])
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            
        finally:
            browser.close()
    
    return videos_data

def main():
    # Configuration
    INSTAGRAM_USERNAME = "t20worldcup"  # Without @ symbol
    
    print("Starting Instagram video scraper...")
    print(f"Target profile: @{INSTAGRAM_USERNAME}")
    
    # Run scraper
    results = scrape_instagram_videos(INSTAGRAM_USERNAME, max_scrolls=15)
    
    # Save results
    output_dir = "../data"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "videos.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nScraping complete!")
    print(f"Total videos found: {results['total_videos']}")
    print(f"Results saved to: {output_file}")
    
    # Also create a simple text file with just URLs
    if results["videos"]:
        txt_file = os.path.join(output_dir, "video_links.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            for video in results["videos"]:
                f.write(f"{video['url']}\n")
        print(f"URLs also saved to: {txt_file}")

if __name__ == "__main__":
    main()
