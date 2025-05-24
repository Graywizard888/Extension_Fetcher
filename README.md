# Extension_Fetcher
Tries to download extension by user specified extension id on Edge add-on store (for now)



Detail :-

Asks for an Edge extension ID (the unique identifier found in extension URLs) for getting Extension I'd search particular extension on Edge add-on store then cheak its url and copy from ex:-https://edge.addon/jshhesokej
(jshhesokej) which is extension id.

Constructs a Microsoft Edge Web Store download URL using the extension ID

Uses streaming download to handle large files efficiently

Implements progress tracking showing either:
Percentage complete (if Content-Length is available)
Bytes downloaded (if size is unknown)

Extracts filename from server headers if available (not working) otherwise extension I'd as file name

Sanitizes filenames by removing special characters

Ensures ".crx" file extension

Creates a "storage/shared/Extension" folder (platform-agnostic path for directly store in internal storage)

Works even if the directory already exists









How to Use :-



termux-setup-storage

clone repo:-

git clone https://github.com/Graywizard888/Extension_Fetcher.git

chmod +x Extension_Fetcher.py

pkg install python

pip install requests

python Extension_Fetcher.py


