# SeaTable Static Catalog Generator

Generates a static HTML catalog from your SeaTable "Works & Exhibits" database.

## Features

- ✅ Downloads images from SeaTable and stores them locally
- ✅ Unique filenames prevent overwrites across multiple views
- ✅ Generates clean, responsive HTML catalog  
- ✅ Perfect for GitHub Pages
- ✅ Works with multiple catalog pages sharing the same images

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Generator

```bash
python3 generate_catalog.py
```

The script is pre-configured with:
- **Table:** "Works & Exhibits"
- **View:** "Produced Works"
- **Output:** `art/catalog.html`

### 3. Deploy to GitHub

```bash
cd art
git add .
git commit -m "Update catalog"
git push
```

Your catalog will be live at: `https://jofowood.github.io/art/catalog.html`

## What It Does

1. Connects to your SeaTable base using the configured API token
2. Pulls data from "Works & Exhibits" table, "Produced Works" view
3. Downloads images to `art/images/` with unique hash-based filenames
4. Generates `art/catalog.html` with your artwork
5. Ready to commit and push!

## Image Filename Strategy

Images are saved with hash-based filenames (e.g., `a1b2c3d4e5f6.jpg`):
- **Same image = same filename** → won't re-download
- **Different image = different filename** → no conflicts  
- Perfect for multiple catalog pages sharing images

## Creating Additional Catalogs

To create catalogs from different views (e.g., "Habit Pattern" series):

1. Copy the script to a new file (e.g., `generate_habit_pattern.py`)
2. Update these lines:
   ```python
   VIEW_NAME = "Habit Pattern View"  # Change to your view name
   HTML_FILE = OUTPUT_DIR / "habit-pattern.html"  # Different output file
   ```
3. Run the new script
4. Images are automatically shared between catalogs!

## Customization

Open `generate_catalog.py` and modify:

```python
# Change the view
VIEW_NAME = "Your View Name"

# Change output filename  
HTML_FILE = OUTPUT_DIR / "your-catalog.html"

# Change output directory
OUTPUT_DIR = Path("your-directory")
```

## Troubleshooting

**"No image column found"**
- The table needs an Image column type

**Images not downloading**
- Verify API token has read permissions
- Check that the base/view is accessible

**Want to regenerate everything?**
```bash
rm -rf art/images/*
python3 generate_catalog.py
```
