import csv
import re
from playwright.async_api import async_playwright
import asyncio
import time

class SupplierSearchTool:
    def __init__(self):
        self.csv_path = "suppliers.csv"

    def parse_rfx(self, rfx_path: str) -> str:
        """Extract product details from rfx.md to form a search query."""
        with open(rfx_path, 'r') as f:
            content = f.read()
        
        quantity_match = re.search(r"Quantity:\s*(\d+)\s*units", content, re.IGNORECASE)
        item_match = re.search(r"Type:\s*([A-Za-z\s\/]+)", content, re.IGNORECASE)
        specs_match = re.search(r"Specifications:\s*-.*?-.*?\n\s*-.*?\n\s*-.*?\n\s*-.*?\n", content, re.IGNORECASE | re.DOTALL)
        
        quantity = quantity_match.group(1) if quantity_match else "50"
        item = item_match.group(1).strip() if item_match else "computers"
        specs = specs_match.group(0).replace("Specifications:", "").strip().replace("\n", " ").replace("- ", "") if specs_match else "standard business specs"
        
        query = f"{item} {specs}"
        return query

    async def scrape_alibaba(self, query: str) -> list:
        """Scrape Alibaba for product/supplier details using Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            search_url = f"https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText={query.replace(' ', '+')}"
            await page.goto(search_url, timeout=60000)
            await page.wait_for_load_state("networkidle")

            cards = await page.locator('div[data-spm-anchor-id*="product"]').all()
            suppliers = []

            for card in cards[:10]:  # limit to first 5 products
                try:
                    name = await card.locator("h2 > a").inner_text()
                    price = await card.locator("div.price").inner_text()
                    price = float(re.findall(r"\d+[,.]?\d*", price)[0].replace(",", ""))
                    rating_elem = await card.locator('span.star-level').all_inner_text()
                    rating = float(rating_elem[0]) if rating_elem else 0.0
                    reviews_elem = await card.locator('span.review-num').all_inner_text()
                    reviews = int(re.findall(r"\d+", reviews_elem[0])[0]) if reviews_elem else 0
                    delivery = "10-20 days"
                    verified = bool(await card.locator("span.verified-icon").count())

                    supplier = {
                        "name": name,
                        "price": price,
                        "reviews": reviews,
                        "rating": rating,
                        "estimated_delivery_time": delivery,
                        "verified_status": verified,
                        "phone": "7010030190",
                        "email": "22b143@psgitech.ac.in" if len(suppliers) % 2 == 0 else "sanjithkaran22@gmail.com"
                    }
                    suppliers.append(supplier)

                except Exception as e:
                    print(f"Skipping card due to error: {e}")
                    continue

            await browser.close()
            return suppliers

    def save_to_csv(self, suppliers: list) -> None:
        """Save supplier data to a CSV file."""
        headers = ["name", "price", "reviews", "rating", "estimated_delivery_time", "verified_status", "email", "phone"]
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(suppliers)

    def run(self, rfx_path: str) -> str:
        """Main method to execute the supplier search and data storage process."""
        query = self.parse_rfx(rfx_path)
        suppliers = asyncio.run(self.scrape_alibaba(query))
        self.save_to_csv(suppliers)
        return f"Supplier data saved to {self.csv_path}"
