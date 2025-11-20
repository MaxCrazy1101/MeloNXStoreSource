import requests
import json
from datetime import datetime


def generate_sidestore_json():
    # ---------------- Configuration Area ----------------
    # Repository Configuration
    GITLAB_DOMAIN = "git.ryujinx.app"
    PROJECT_PATH = "melonx/emu"
    PRIVATE_TOKEN = None  # Enter Token if it is a private repository

    # SideStore/AltStore Base Metadata (Hardcoded based on your sample)
    sidestore_data = {
        "name": "MeloNX Releases",
        "subtitle": "Release builds from MelonX",
        "description": "Automatic hourly feed of MeloNX release builds.",
        "iconURL": "https://raw.githubusercontent.com/MaxCrazy1101/MeloNXStoreSource/main/icon.png",
        "tintColor": "#2ECC71",
        "apps": [
            {
                "name": "MeloNX",
                "bundleIdentifier": "com.stossy11.MeloNX",
                "developerName": "MeloNX Team",
                "subtitle": "The most advanced Nintendo Switch emulator for iOS",
                "localizedDescription": "The most advanced Nintendo Switch emulator for iOS. Built on the Ryujinx core...",
                "iconURL": "https://raw.githubusercontent.com/MaxCrazy1101/MeloNXStoreSource/main/icon.png",
                "category": "games",
                "versions": [],  # We will populate this dynamically
            }
        ],
    }
    # ----------------------------------------

    # 1. Request GitLab API
    encoded_path = PROJECT_PATH.replace("/", "%2F")
    url = f"https://{GITLAB_DOMAIN}/api/v4/projects/{encoded_path}/releases"

    headers = {}
    if PRIVATE_TOKEN:
        headers["PRIVATE-TOKEN"] = PRIVATE_TOKEN

    print(f"Fetching release information from {GITLAB_DOMAIN}...")

    try:
        # Get all release info (Default 20 items, add per_page param if more are needed)
        response = requests.get(url, headers=headers, params={"per_page": 50})
        response.raise_for_status()
        releases = response.json()

        processed_versions = []

        # 2. Iterate through each Release
        for release in releases:
            tag_name = release.get("tag_name")
            description = release.get("description", "No description provided")
            released_at_raw = release.get("released_at")

            # Format date: 2025-11-02T07:17:43.000-06:00 -> 2025-11-02
            try:
                date_obj = datetime.fromisoformat(released_at_raw)
                date_str = date_obj.strftime("%Y-%m-%d")
            except:
                date_str = released_at_raw[:10]

            # 3. Find IPA download link
            download_url = None

            # Check Assets -> Links
            assets = release.get("assets", {}).get("links", [])
            for asset in assets:
                asset_url = asset.get("url", "")
                asset_name = asset.get("name", "").lower()
                # Logic: If name contains ipa or url ends with ipa
                if asset_name.endswith(".ipa") or asset_url.endswith(".ipa"):
                    download_url = asset_url
                    break

            # If no IPA found, skip this version (SideStore requires a download link)
            if not download_url:
                print(f"Skipping version {tag_name}: IPA file not found")
                continue

            # 4. Construct Version object
            version_obj = {
                "version": tag_name,
                # "buildVersion": tag_name,
                "buildVersion": "1",
                "date": date_str,
                "localizedDescription": description,
                "downloadURL": download_url,
                "size": 0,  # API list usually doesn't return file size, SideStore allows 0 (or client detects it)
            }

            processed_versions.append(version_obj)

        # Populate apps[0]['versions'] with processed version list
        sidestore_data["apps"][0]["versions"] = processed_versions

        # 5. Save as JSON file
        output_file = "MeloNX.json"  # Ensure filename is fixed
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sidestore_data, f, indent=2, ensure_ascii=False)

        print(f"\nSuccess! File generated: {output_file}")
        print(f"Total {len(processed_versions)} versions included.")

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    generate_sidestore_json()
