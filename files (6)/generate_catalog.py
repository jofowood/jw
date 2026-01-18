#!/usr/bin/env python3
"""
SeaTable Static Catalog Generator

Pulls artwork data and images from SeaTable, generates static HTML catalog
Images are saved with unique filenames to avoid conflicts across multiple views
"""

import requests
import json
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

# Configuration
API_TOKEN = "15d2c34c1ab2c226a629c1dcb9c9e02cffec1376"
SERVER_URL = "https://cloud.seatable.io"
TABLE_NAME = "Works & Exhibits"
VIEW_NAME = "Produced Works"

# Output paths
OUTPUT_DIR = Path("art")
IMAGES_DIR = OUTPUT_DIR / "images"
HTML_FILE = OUTPUT_DIR / "catalog.html"


def get_base_token(api_token):
    """Get temporary base token from API token"""
    response = requests.get(
        f"{SERVER_URL}/api/v2.1/dtable/app-access-token/",
        headers={"Authorization": f"Token {api_token}"}
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"], data["dtable_uuid"]


def get_metadata(base_token, base_uuid):
    """Get base metadata including tables and columns"""
    response = requests.get(
        f"{SERVER_URL}/dtable-server/api/v1/dtables/{base_uuid}/metadata/",
        headers={"Authorization": f"Bearer {base_token}"}
    )
    response.raise_for_status()
    return response.json()["metadata"]


def get_rows(base_token, base_uuid, table_name, view_name=None):
    """Get all rows from a table/view"""
    url = f"{SERVER_URL}/dtable-server/api/v1/dtables/{base_uuid}/rows/"
    params = {"table_name": table_name}
    if view_name:
        params["view_name"] = view_name
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {base_token}"},
        params=params
    )
    response.raise_for_status()
    return response.json()["rows"]


def get_image_filename(image_url):
    """
    Generate unique filename from image URL
    Uses hash of full path to ensure uniqueness across different uploads
    Preserves original extension
    """
    # Parse the URL to get the path
    parsed = urlparse(image_url)
    path = unquote(parsed.path)
    
    # Get original filename and extension
    original_filename = Path(path).name
    extension = Path(original_filename).suffix
    
    # Create hash of full path (includes UUID, date, etc)
    # This ensures same image = same filename, different images = different filenames
    path_hash = hashlib.md5(path.encode()).hexdigest()[:12]
    
    # Return: hash + extension (e.g., "a1b2c3d4e5f6.jpg")
    return f"{path_hash}{extension}"


def download_image(image_url, api_token, output_path):
    """Download image from SeaTable to output path"""
    # Skip if already exists
    if output_path.exists():
        print(f"  ✓ Already exists: {output_path.name}")
        return True
    
    # Extract path from URL for download link API
    parsed = urlparse(image_url)
    path = unquote(parsed.path)
    
    # Get download link
    response = requests.get(
        f"{SERVER_URL}/api/v2.1/dtable/app-download-link/",
        headers={"Authorization": f"Token {api_token}"},
        params={"path": path.split("/asset/")[1]}  # Path after /asset/uuid/
    )
    response.raise_for_status()
    download_url = response.json()["download_link"]
    
    # Download the file
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"  ✓ Downloaded: {output_path.name}")
    return True


def find_image_column(columns):
    """Find the first image column in the table"""
    for col in columns:
        if col["type"] == "image":
            return col["name"]
    return None


def generate_html(rows, image_column, columns):
    """Generate HTML catalog page matching existing style"""
    
    # Find specific columns by name
    column_map = {col['name']: col for col in columns}
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artwork Catalog</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 30px;
            font-weight: 300;
            text-align: center;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .artwork-card {
            background: #f9f9f9;
            border-radius: 2px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s;
        }
        
        .artwork-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .artwork-image {
            width: 100%;
            height: 300px;
            background: #f9f9f9;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .artwork-image img {
            max-width: 100%;
            max-height: 300px;
            width: auto;
            height: auto;
            object-fit: contain;
            display: block;
        }
        
        .artwork-info {
            padding: 20px;
        }
        
        .artwork-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #222;
        }
        
        .artwork-meta {
            font-size: 0.9rem;
            color: #666;
            line-height: 1.6;
        }
        
        .artwork-meta div {
            margin-bottom: 4px;
        }
        
        .inv-number {
            font-family: monospace;
            color: #999;
            font-size: 0.85rem;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Artwork Catalog</h1>
        <div class="grid">
"""
    
    for row in rows:
        # Get images
        images = row.get(image_column, [])
        if not images:
            continue
        
        # Use first image
        image_url = images[0] if isinstance(images, list) else images
        image_filename = get_image_filename(image_url)
        
        # Extract common fields (using flexible name matching)
        title = None
        inventory = None
        series = None
        year = None
        edition = None
        
        for key, value in row.items():
            if value:
                key_lower = key.lower()
                if 'title' in key_lower or 'name' in key_lower:
                    title = value
                elif 'inventory' in key_lower or 'inv' in key_lower:
                    inventory = value
                elif 'collection' in key_lower or 'series' in key_lower:
                    series = value
                elif 'year' in key_lower or 'date' in key_lower:
                    # Extract year from date if needed
                    year = str(value).split('-')[0] if '-' in str(value) else value
                elif 'edition' in key_lower and 'desc' not in key_lower:
                    edition = value
        
        title = title or 'Untitled'
        
        # Build card HTML
        html += f"""            <div class="artwork-card">
                <div class="artwork-image">
                    <img src="images/{image_filename}" alt="{title}">
                </div>
                <div class="artwork-info">
                    <div class="artwork-title">{title}</div>
                    <div class="artwork-meta">
"""
        
        if inventory:
            html += f"""                        <div class="inv-number">{inventory}</div>\n"""
        if series:
            html += f"""                        <div><strong>Series:</strong> {series}</div>\n"""
        if year:
            html += f"""                        <div><strong>Year:</strong> {year}</div>\n"""
        if edition:
            html += f"""                        <div><strong>Edition:</strong> {edition}</div>\n"""
        
        html += """                    </div>
                </div>
            </div>
"""
    
    html += """        </div>
    </div>
</body>
</html>"""
    
    return html


def main():
    print("SeaTable Static Catalog Generator")
    print("=" * 50)
    
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    # Get base token
    print("\n1. Authenticating with SeaTable...")
    base_token, base_uuid = get_base_token(API_TOKEN)
    print(f"   ✓ Connected to base: {base_uuid[:8]}...")
    
    # Get metadata
    print("\n2. Loading base structure...")
    metadata = get_metadata(base_token, base_uuid)
    tables = metadata["tables"]
    
    # Select table
    table = tables[0] if not TABLE_NAME else next(t for t in tables if t["name"] == TABLE_NAME)
    print(f"   ✓ Using table: {table['name']}")
    
    # Find image column
    image_column = find_image_column(table["columns"])
    if not image_column:
        print("   ✗ No image column found!")
        return
    print(f"   ✓ Image column: {image_column}")
    
    # Get metadata columns (non-image columns to display)
    all_columns = [col for col in table["columns"] 
                       if col["type"] not in ["image", "file", "long-text")]
    
    # Get rows
    print(f"\n3. Loading rows from view: {VIEW_NAME}...")
    rows = get_rows(base_token, base_uuid, table["name"], VIEW_NAME)
    print(f"   ✓ Found {len(rows)} rows")
    
    # Download images
    print(f"\n4. Downloading images to {IMAGES_DIR}...")
    image_count = 0
    for i, row in enumerate(rows, 1):
        images = row.get(image_column, [])
        if not images:
            continue
        
        # Get first image
        image_url = images[0] if isinstance(images, list) else images
        image_filename = get_image_filename(image_url)
        output_path = IMAGES_DIR / image_filename
        
        print(f"   [{i}/{len(rows)}] {row.get('Name', row.get('Title', 'Untitled'))}")
        download_image(image_url, API_TOKEN, output_path)
        image_count += 1
    
    print(f"\n   ✓ Processed {image_count} images")
    
    # Generate HTML
    print(f"\n5. Generating {HTML_FILE}...")
    html = generate_html(rows, image_column, all_columns)
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"   ✓ Catalog generated!")
    
    print(f"\n✓ Complete!")
    print(f"\nNext steps:")
    print(f"  1. Review the generated catalog: {HTML_FILE}")
    print(f"  2. Commit to git: git add art/")
    print(f"  3. Push to GitHub: git push")
    print(f"\nYour catalog will be live at:")
    print(f"  https://jofowood.github.io/art/catalog.html")


if __name__ == "__main__":
    main()
