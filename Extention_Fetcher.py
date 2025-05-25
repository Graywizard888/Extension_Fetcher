import requests
import re
import urllib.parse
import os

CURRENT_VERSION = "1.1.0"

def check_for_updates():
    """Check GitHub releases for newer version and update if available"""
    try:
        print("Checking for updates...")
        script_name = os.path.basename(__file__)
        api_url = "https://api.github.com/repos/Graywizard888/Extension_Fetcher/releases/latest"
        
        
        response = requests.get(api_url, headers={'User-Agent': 'ExtensionFetcher'}, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_tag = release_data['tag_name'].lstrip('v')
        current_version = CURRENT_VERSION.lstrip('v')

        
        current_tuple = tuple(map(int, current_version.split('.')))
        latest_tuple = tuple(map(int, latest_tag.split('.')))
        
        if latest_tuple <= current_tuple:
            print("You're using the latest version.")
            return

        print(f"\nNew version {release_data['tag_name']} available!")
        print(f"Release notes: {release_data['html_url']}")
        
        
        asset = next((a for a in release_data['assets'] if a['name'] == script_name), None)
        if not asset:
            print("Update failed: No matching asset found in release.")
            return

        confirm = input("Would you like to update now? (y/N): ").strip().lower()
        if confirm != 'y':
            return

        print("Downloading update...")
        temp_path = f"{__file__}.tmp"
        
        
        dl_response = requests.get(asset['browser_download_url'], stream=True)
        dl_response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in dl_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        
        os.replace(temp_path, __file__)
        print("Update successful! Please restart the script.")
        exit(0)

    except requests.exceptions.RequestException as e:
        print(f"Update check failed: {str(e)}")
    except Exception as e:
        print(f"Error during update: {str(e)}")

def sanitize_filename(name):
    """Clean special characters from filename"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_extension_name(headers):
    """Extract filename from Content-Disposition header"""
    content_disp = headers.get("Content-Disposition", "")
    match = re.findall(r"filename\*?=([^;]+)", content_disp, flags=re.IGNORECASE)
    if match:
        filename = urllib.parse.unquote(match[-1]).strip(' "\'')
        if filename.lower().endswith(".crx"):
            filename = filename[:-4]
        return filename
    return None

def main():
    check_for_updates()
    
    extension_id = input("Enter Edge extension ID: ").strip()
    
    ext_dir = os.path.join(
        os.path.expanduser("~"),
        "storage",  
        "shared",  
        "Extension"  
    )
    os.makedirs(ext_dir, exist_ok=True)

    download_url = (
        f"https://edge.microsoft.com/extensionwebstorebase/v1/crx"
        f"?response=redirect&prod=chromiumcrx&prodchannel=&"
        f"x=id%3D{extension_id}%26installsource%3Dondemand%26uc"
    )

    try:
        with requests.get(download_url, stream=True, allow_redirects=True) as response:
            response.raise_for_status()

            filename = get_extension_name(response.headers) or extension_id
            clean_name = sanitize_filename(filename) + ".crx"
            file_path = os.path.join(ext_dir, clean_name)

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rDownload progress: {percent:.2f}%", end='')
                        else:
                            print(f"\rDownloaded: {downloaded} bytes", end='')
                print()

            print(f"Download successful: {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"\nDownload failed: {e}")
    except PermissionError:
        print(f"\nError: Permission denied. Grant storage access to Termux first!")
        print("Run this command in Termux: termux-setup-storage")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
