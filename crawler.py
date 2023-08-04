# simple crawler 

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def clean_text(text):
    cleaned_text = text.strip()
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text

class WebCrawler:
    def __init__(self, url, text_limit):
        self.url = url
        self.text_limit = text_limit

    def collect_texts(self):
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--window-size=1920x1080")

        # Use the Firefox WebDriver
        driver = webdriver.Firefox(options=firefox_options)

        driver.get(self.url)
        driver.implicitly_wait(2)
        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')
        all_text = set()
        content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])

        for tag in content_tags:
            text = tag.get_text()
            if text:
                cleaned_text = clean_text(text)
                if cleaned_text:
                    all_text.add(cleaned_text)

                if len(' '.join(all_text)) >= self.text_limit:
                    break

        return ' '.join(all_text)

if __name__ == "__main__":
    website_url = 'https://scikit-learn.org/stable/about.html'
    crawler = WebCrawler(website_url, text_limit=10000)
    text_content = crawler.collect_texts()
    if text_content:
        print(text_content)


