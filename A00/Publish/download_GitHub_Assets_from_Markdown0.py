import os
import re
import requests
from pathlib import Path

#
# GitHub asset mass downloader
# Circulstances / why created:
#    Use the online github editor to create pages
#    And pasted images into GitHub that create asset
#    images outside the git checkin / project files.
#    This Python app downloads these out-of-project
#    files for local ussage.
#

# LICENSE: Public Domain. No rights reserved.
# 2026-01-09

# Tip / Warning:
#     Assumes run directory context is directory before
#     local git folder of project.


# App Configuration
SOURCE_DIRECTORY = "./April14_2025"  # Folder containing .md files
DOWNLOAD_DIRECTORY = "./April14_2025_assets" # Where images will be saved

# WARNING: only looking ofr image assets in this format
# Regex to match GitHub user-attachment URLs specifically inside <img> tags
# This RegEx captures the full URL from the src attribute
ASSET_REGEX = r'<img [^>]*src="(https://github\.com/user-attachments/assets/[a-f0-9-]+)"'
# Broad RegEx to find ANY GitHub asset URL regardless of surrounding tags
UNIVERSAL_ASSET_REGEX = r'https://github\.com/user-attachments/assets/[a-f0-9-]+'

def download_asset(url, save_path):
    """Downloads a file from a URL to a local path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded: {save_path.name}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    # Create download directory if it doesn't exist
    Path(DOWNLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
    
    # Walk through the file tree recursively to find all .md files
    md_files = list(Path(SOURCE_DIRECTORY).rglob("*.md"))
    print(f"Found {len(md_files)} markdown files. Scanning for assets...")

    for md_path in md_files:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find all matching asset URLs in the current file
            matches = re.findall(ASSET_REGEX, content)
            
            for url in matches:
                # Use the UUID from the URL as the filename to ensure uniqueness
                asset_id = url.split('/')[-1]
                # this assumes all are PNG, is that true? JPG ?
                save_path = Path(DOWNLOAD_DIRECTORY) / f"{asset_id}.png"
                
                # for repeat runs of this app, only download asset one time
                if not save_path.exists():
                    download_asset(url, save_path)
                else:
                    print(f"Skipping already downloaded: {asset_id}")


    # Second pass
    # Search for any assets not in img patterns

    for md_path in md_files:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 1. Identify what the FIRST loop would have caught
            img_tag_matches = set(re.findall(ASSET_REGEX, content))
            
            # 2. Identify ALL asset URLs in the file
            all_matches = set(re.findall(UNIVERSAL_ASSET_REGEX, content))
            
            # 3. Calculate the difference (Missed = All - Tagged)
            missed_assets = all_matches - img_tag_matches
            
            if missed_assets:
                print(f"\n[!] Missed assets found in {md_path.name}:")
                for missed_url in missed_assets:
                    print(f"  - {missed_url}")
                    # ToDo: download here?


if __name__ == "__main__":
    main()
