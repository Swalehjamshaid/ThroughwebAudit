# /app/app/audit_categories.py
AUDIT_CATEGORIES = {
    "Performance": {
        "desc": "Measures speed, responsiveness, and optimization using Core Web Vitals.",
        "metrics": ["First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)", "Cumulative Layout Shift (CLS)", "Interaction to Next Paint (INP)", "Time to First Byte (TTFB)"]
    },
    "Security": {
        "desc": "Checks security standards and vulnerability risks.",
        "metrics": ["HTTPS Enabled (SSL/TLS)", "Secure Cookies", "Content Security Policy (CSP) Implemented", "HSTS (HTTP Strict Transport Security)", "X-Frame-Options"]
    },
    "SEO": {
        "desc": "Search engine optimization compliance for indexing and ranking.",
        "metrics": ["Meta Description Present and Unique", "Title Tag Length and Relevance", "XML Sitemap Presence and Validity", "Robots.txt Presence", "Mobile Friendly / Viewport Configured"]
    },
    # ... (Add all 45+ metrics here)
}
