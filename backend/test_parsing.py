from bs4 import BeautifulSoup
import json

# Import your backend parsing function
from main import parse_products


# 1. MOCK HTML for Amazon (simulate ScraperAPI response)
mock_amazon_html = """
<div class="s-result-item">
    <a class="a-link-normal" href="/dp/B08N5XSG8Z">
        <img src="https://m.media-amazon.com/images/I/71TPda7cwUL._SX679_.jpg"/>
        Apple 2024 MacBook Air Laptop with M3 chip
    </a>
</div>

<div class="s-result-item">
    <a class="a-link-normal" href="/dp/B09V5X8S7T">
        <img src="https://m.media-amazon.com/images/I/71f5Eu5lJSL._SX679_.jpg"/>
        Dell XPS 13 Plus Laptop, Intel Core i7
    </a>
</div>
"""


# 2. MOCK HTML for Flipkart
mock_flipkart_html = """
<a href="/p/flipkart-laptop-123">
    <img src="https://example.com/image1.jpg">
    ASUS VivoBook 16 Thin and Light Laptop
</a>

<a href="/p/flipkart-laptop-456">
    <img src="https://example.com/image2.jpg">
    Acer Aspire 5 Gaming Laptop
</a>
"""


# 3. MOCK HTML for Myntra
mock_myntra_html = """
<a href="https://www.myntra.com/dress">
    <img src="https://example.com/dress.jpg">
    Women Red Printed Dress
</a>

<a href="https://www.myntra.com/shoes">
    <img src="https://example.com/shoes.jpg">
    Men Black Sneakers
</a>
"""


print("=== TESTING AMAZON PARSER ===")
amazon_results = parse_products(mock_amazon_html, "Amazon")
print(json.dumps(amazon_results, indent=4))


print("\n=== TESTING FLIPKART PARSER ===")
flipkart_results = parse_products(mock_flipkart_html, "Flipkart")
print(json.dumps(flipkart_results, indent=4))


print("\n=== TESTING MYNTRA PARSER ===")
myntra_results = parse_products(mock_myntra_html, "Myntra")
print(json.dumps(myntra_results, indent=4))
