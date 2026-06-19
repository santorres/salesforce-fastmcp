#!/usr/bin/env python3
"""
Markdown Utility Functions for Channel Director Automation

Provides helpers for creating professional Markdown reports.
"""

from datetime import datetime
import json


class MarkdownReport:
    """Helper class for creating Markdown reports."""
    
    def __init__(self, title, subtitle=None):
        """Initialize Markdown report."""
        self.content = []
        self.title = title
        self.subtitle = subtitle
        
        # Add title
        self.add_h1(title)
        
        if subtitle:
            self.add_paragraph(f"*{subtitle}*")
    
    def add_h1(self, text):
        """Add H1 header."""
        self.content.append(f"# {text}\n")
    
    def add_h2(self, text):
        """Add H2 header."""
        self.content.append(f"## {text}\n")
    
    def add_h3(self, text):
        """Add H3 header."""
        self.content.append(f"### {text}\n")
    
    def add_paragraph(self, text):
        """Add paragraph."""
        self.content.append(f"{text}\n")
    
    def add_bullet_list(self, items):
        """Add bullet list."""
        for item in items:
            self.content.append(f"- {item}\n")
        self.content.append("\n")
    
    def add_table(self, headers, data):
        """Add table."""
        # Headers
        self.content.append("| " + " | ".join(str(h) for h in headers) + " |\n")
        
        # Separator
        self.content.append("|" + "|".join(["---"] * len(headers)) + "|\n")
        
        # Data rows
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    values = [str(row.get(h, "—")) for h in headers]
                else:
                    values = [str(v) if v is not None else "—" for v in row]
                self.content.append("| " + " | ".join(values) + " |\n")
        
        self.content.append("\n")
    
    def add_table_from_dict(self, headers, data_list):
        """Add table from list of dicts."""
        if not data_list:
            self.add_paragraph("*No data available*")
            return
        
        # Headers
        self.content.append("| " + " | ".join(headers) + " |\n")
        
        # Separator
        self.content.append("|" + "|".join(["---"] * len(headers)) + "|\n")
        
        # Data rows
        for row in data_list:
            values = []
            for header in headers:
                value = row.get(header) if isinstance(row, dict) else "—"
                values.append(str(value) if value is not None else "—")
            self.content.append("| " + " | ".join(values) + " |\n")
        
        self.content.append("\n")
    
    def add_key_metrics(self, metrics):
        """Add key metrics section."""
        self.add_h2("Key Metrics")
        
        # Create table
        headers = ["Metric", "Value", "Target", "Status"]
        data = []
        
        for metric in metrics:
            data.append([
                metric.get("name", "—"),
                metric.get("value", "—"),
                metric.get("target", "—"),
                metric.get("status", "—")
            ])
        
        self.add_table(headers, data)
    
    def add_summary_box(self, items):
        """Add executive summary box."""
        self.add_h2("Executive Summary")
        for item in items:
            self.add_paragraph(f"- {item}")
        self.content.append("\n")
    
    def add_divider(self):
        """Add horizontal divider."""
        self.content.append("---\n\n")
    
    def add_metadata(self):
        """Add metadata footer."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.content.append(f"*Generated: {timestamp}*\n")
    
    def render(self):
        """Get full Markdown content as string."""
        return "".join(self.content)
    
    def save(self, filepath):
        """Save report to file."""
        with open(filepath, 'w') as f:
            f.write(self.render())
        print(f"✅ Saved Markdown report: {filepath}")


def format_currency(value, currency="EUR"):
    """Format number as currency."""
    if value is None or value == "":
        return "—"
    try:
        if currency == "EUR":
            return f"€{float(value):,.0f}"
        else:
            return f"${float(value):,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value):
    """Format number as percentage."""
    if value is None or value == "":
        return "—"
    try:
        pct = float(value)
        if pct < 0:
            return f"{pct:.1f}% ↓"
        elif pct > 0:
            return f"{pct:.1f}% ↑"
        else:
            return f"{pct:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def get_status_indicator(value, target=None):
    """Get status indicator based on value vs target."""
    if value is None or target is None:
        return "—"
    
    try:
        v = float(value)
        t = float(target)
        pct = (v / t) * 100
        
        if pct >= 100:
            return f"✅ {pct:.0f}%"
        elif pct >= 75:
            return f"⚠️ {pct:.0f}%"
        else:
            return f"🚨 {pct:.0f}%"
    except (ValueError, TypeError):
        return "—"


def safe_get(obj, key, default=None):
    """Safely get value from dict or nested dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def load_json_data(json_str):
    """Load and parse JSON data."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# END OF MARKDOWN UTILS
# ═══════════════════════════════════════════════════════════════════════════
