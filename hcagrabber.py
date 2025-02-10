import os
import re
import requests
from tqdm import tqdm

# Optional spinner using yaspin
try:
    from yaspin import yaspin
    spinner_available = True
except ImportError:
    spinner_available = False

def sanitize_filename(filename):
    """Remove characters that are not allowed in file names."""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

# API endpoint
api_url = "https://www.adlis.hcamazighite.dz/api/api/books/getAllFiles"

try:
    response = requests.get(api_url)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching data from API: {e}")
    exit(1)

try:
    files_list = response.json()
except ValueError as e:
    print(f"Error parsing JSON: {e}")
    exit(1)

print("JSON response:")
for idx, item in enumerate(files_list, start=1):
    print(f"Item {idx}: {item}")

# Filter items that have a valid PDF URL.
files_to_download = [item for item in files_list 
                     if item.get("link") and ".pdf" in item.get("link").lower()]
num_files = len(files_to_download)
print(f"Found {num_files} files to download.\n")

# Create a directory to store downloaded PDFs
download_dir = "pdf_downloads"
os.makedirs(download_dir, exist_ok=True)

# Loop over each file and download if needed
for idx, item in enumerate(files_to_download):
    pdf_url = item.get("link")
    title = item.get("title", "untitled")
    pub_year = item.get("publication_year", "unknown")
    safe_title = sanitize_filename(title)
    new_filename = f"{safe_title} {pub_year}.pdf"
    filepath = os.path.join(download_dir, new_filename)
    
    remaining = num_files - (idx + 1)
    print(f"\nDownloading file {idx+1}/{num_files} (Remaining: {remaining}): {new_filename}")
    
    # Check if file exists and compare file sizes.
    if os.path.exists(filepath):
        try:
            head_response = requests.head(pdf_url)
            head_response.raise_for_status()
            remote_size = int(head_response.headers.get("content-length", 0))
            local_size = os.path.getsize(filepath)
            if local_size == remote_size:
                print("File already downloaded (sizes match), skipping.")
                continue
            else:
                print(f"Local file size ({local_size} bytes) does not match remote size ({remote_size} bytes); re-downloading.")
        except requests.RequestException as e:
            print(f"HEAD request failed for {pdf_url}: {e}")
            # Proceed with download in case HEAD request is unsupported
     
    try:
        # Optionally use a spinner for initialization
        if spinner_available:
            with yaspin(text="Initializing download...", color="cyan") as spinner:
                spinner.write("Starting download...")
                spinner.stop()  # Stop spinner before progress bar begins
        
        with requests.get(pdf_url, stream=True) as pdf_response:
            pdf_response.raise_for_status()
            total_size = int(pdf_response.headers.get("content-length", 0))
            with open(filepath, "wb") as f, tqdm(
                total=total_size, unit='iB', unit_scale=True, desc=new_filename
            ) as bar:
                for chunk in pdf_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
    except requests.RequestException as e:
        print(f"Failed to download {pdf_url}: {e}\n")
        continue

print("\nAll downloads completed.")
