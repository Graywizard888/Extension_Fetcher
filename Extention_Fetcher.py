import requests
import re
import urllib.parse
import os

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
    extension_id = input("Enter Edge extension ID: ").strip()
    
    
    ext_dir = os.path.join("storage", "shared", "Extension")
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
        print(f"\nError: Permission denied to write to {ext_dir}")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
