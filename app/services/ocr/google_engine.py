import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from google.cloud import vision

_logger = logging.getLogger(__name__)


@dataclass
class ReceiptLine:
    text: str
    confidence: float
    y_position: float
    x_position: float


class OCRService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def validate_image(self, content_type: str) -> None:
        allowed = ["image/jpeg", "image/png", "image/jpg"]
        if content_type not in allowed:
            raise ValueError("Only JPG, JPEG, PNG images are allowed")

    def process(self, file_bytes: bytes) -> dict:
        image = vision.Image(content=file_bytes)
        response = self.client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"OCR Error: {response.error.message}")

        return self.parse_receipt(response)

    def _extract_structured_lines(self, response) -> List[ReceiptLine]:
        """Extract lines with position data from Vision API response"""
        lines = []

        if not response.full_text_annotation.pages:
            return lines

        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    # Get text from words
                    text = ""
                    vertices = paragraph.bounding_box.vertices
                    y_pos = sum([v.y for v in vertices]) / len(vertices)
                    x_pos = sum([v.x for v in vertices]) / len(vertices)

                    for word in paragraph.words:
                        word_text = "".join([sy.text for sy in word.symbols])
                        text += word_text + " "

                    lines.append(
                        ReceiptLine(
                            text=text.strip(),
                            confidence=paragraph.confidence,
                            y_position=y_pos,
                            x_position=x_pos,
                        )
                    )

        # Sort by Y position (top to bottom)
        lines.sort(key=lambda x: x.y_position)
        return lines

    def _is_price_pattern(self, text: str) -> Optional[float]:
        """Check if text looks like a price and extract it"""
        # Pattern: 123.45, 123.00, 123, 1,234.56
        price_patterns = [
            r"(\d{1,3}(?:,\d{3})*\.?\d{0,2})",
            r"(\d+\.?\d{0,2})",
        ]

        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(",", "")
                    price = float(price_str)
                    if 0.01 <= price <= 999999:  # Reasonable price range
                        return price
                except ValueError:
                    continue
        return None

    def _is_quantity_pattern(self, text: str) -> Optional[int]:
        """Check if text looks like a quantity"""
        # Pattern: 1x, x1, 2, etc.
        qty_patterns = [
            r"^(\d+)\s*[xX×]",
            r"[xX×]\s*(\d+)",
            r"^(\d+)$",
        ]

        for pattern in qty_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    qty = int(match.group(1))
                    if 1 <= qty <= 999:  # Reasonable quantity range
                        return qty
                except ValueError:
                    continue
        return None

    def _find_item_pattern(self, lines: List[ReceiptLine]) -> List[Dict]:
        """Find items using pattern detection"""
        items = []
        i = 0

        while i < len(lines):
            line = lines[i]
            text = line.text.strip()

            # Skip empty or very short lines
            if len(text) < 2:
                i += 1
                continue

            # Check if line contains price-like numbers
            prices_in_line = re.findall(r"\d+\.?\d{0,2}", text)

            if len(prices_in_line) >= 2:
                # Line might contain: [name] [qty] [price] [total]
                # or: [name] [qty] @ [price] [total]

                parts = re.split(r"\s+", text)

                # Try to extract structured data
                item_name = []
                quantity = None
                unit_price = None
                total_price = None

                for part in parts:
                    # Check for quantity
                    qty = self._is_quantity_pattern(part)
                    if qty and quantity is None:
                        quantity = qty
                        continue

                    # Check for price
                    price = self._is_price_pattern(part)
                    if price:
                        if unit_price is None:
                            unit_price = price
                        elif total_price is None:
                            total_price = price
                        continue

                    # Skip common separators
                    if part in ["@", "x", "X", "×", "-", "|"]:
                        continue

                    # Otherwise, it's part of the item name
                    item_name.append(part)

                # Validate we have minimum required fields
                if item_name and unit_price:
                    if quantity is None:
                        quantity = 1
                    if total_price is None:
                        total_price = unit_price * quantity

                    items.append(
                        {
                            "name": " ".join(item_name).strip(),
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "total": total_price,
                        }
                    )

            elif not re.match(r"^[\d\s\.\,\-\/\:\(\)]+$", text):
                # Line is mostly text (potential item name)
                # Look ahead for price in next line
                if i + 1 < len(lines):
                    next_text = lines[i + 1].text.strip()
                    price = self._is_price_pattern(next_text)
                    qty = self._is_quantity_pattern(next_text)

                    if price:
                        items.append(
                            {
                                "name": text,
                                "quantity": qty or 1,
                                "unit_price": price,
                                "total": price * (qty or 1),
                            }
                        )
                        i += 1  # Skip next line

            i += 1

        return items

    def _find_total_amount(
        self,
        lines: List[ReceiptLine],
        items: List[Dict],
    ) -> float:
        """Find total amount using multiple strategies"""

        # Strategy 1: Look for common total keywords
        total_keywords = [
            "total",
            "รวม",
            "ยอดรวม",
            "sum",
            "subtotal",
            "grand total",
            "net",
            "amount",
            "ทั้งหมด",
        ]

        for line in reversed(lines):  # Check from bottom
            text_lower = line.text.lower()
            for keyword in total_keywords:
                if keyword in text_lower:
                    price = self._is_price_pattern(line.text)
                    if price and price > 0:
                        return price

        # Strategy 2: Find largest price in last 20% of receipt
        last_lines = lines[-max(5, len(lines) // 5)]
        prices = []
        for line in last_lines:
            price = self._is_price_pattern(line.text)
            if price:
                prices.append(price)

        if prices:
            max_price = max(prices)
            items_sum = sum(item["total"] for item in items)

            # If max price is close to items sum, use it
            if items_sum > 0 and abs(max_price - items_sum) / items_sum < 0.1:
                return max_price

        # Strategy 3: Sum of items
        if items:
            return sum(item["total"] for item in items)

        return 0.0

    def parse_receipt(self, response) -> dict:
        """Parse receipt using flexible pattern detection"""

        # Extract structured lines with positions
        lines = self._extract_structured_lines(response)

        if not lines:
            # Fallback to simple text
            text = response.full_text_annotation.text
            lines = [
                ReceiptLine(
                    text=line,
                    confidence=1.0,
                    y_position=i,
                    x_position=0,
                )
                for i, line in enumerate(text.split("\n"))
            ]

        # Find items
        items = self._find_item_pattern(lines)

        # Find total
        total_amount = self._find_total_amount(lines, items)

        return {
            "items": items,
            "total_amount": round(total_amount, 2),
            "item_count": len(items),
            "raw_text": (
                response.full_text_annotation.text
                if hasattr(response, "full_text_annotation")
                else ""
            ),
        }
