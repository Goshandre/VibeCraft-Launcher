# VibeCraft Launcher — Beta 1.5.49

A purple/blue Windows desktop prototype for Minecraft: Java Edition.

## Music menu\n- Includes a playlist UI and cover art based on the user's screenshots.\n- Track titles are catalog entries only; no copyrighted audio is bundled. Select local audio files you own or are licensed to use.\n- Playback uses pygame when available.\n\n## Branding\n- `vibecraft_icon.png` is the launcher artwork.\n- `vibecraft_icon.ico` is used for the Windows EXE build.\n\n## What works in this prototype
- Downloads the official Minecraft Java version manifest and lists available versions.
- Downloads the selected version's game files using `minecraft-launcher-lib`.
- Saves a local path to a user-selected PNG skin.
- Checks GitHub Releases for a newer launcher version after you configure `GITHUB_REPO`.
- Has a purple/blue UI and Windows `.exe` build scripts.

## Not finished yet (important)
- Microsoft/Xbox/Minecraft authentication is **not implemented**.
- The Play button is intentionally blocked until legitimate account authentication and ownership checks are implemented.
- A saved PNG path does not upload or apply a skin to an online Minecraft profile.
- GitHub updater only opens the release page; it does not replace the running EXE automatically.
- Windows 8.1 compatibility is not guaranteed. Modern Python versions and current Minecraft versions may not support Windows 8.1.

This is an independent community project and is not affiliated with Mojang or Microsoft. It does not bypass Minecraft ownership checks.

## Requirements
- Windows 10/11 recommended
- Python 3.11 or newer
- Internet connection for downloading game files

## Run from source
1. Extract this ZIP to a folder.
2. Install Python from the official Python website and enable **Add Python to PATH**.
3. Double-click `install_dependencies.bat`.
4. Double-click `run.bat`.

## Build an EXE
Double-click `build_exe.bat`. If successful, the EXE will be in `dist\\VibeCraftLauncher.exe`.
Building an EXE is not the same as creating a signed installer.

## Publish on GitHub (beginner-friendly)
1. Sign in at https://github.com.
2. Click **+** → **New repository**.
3. Repository name: `VibeCraft-Launcher`. Choose Public or Private, then **Create repository**.
4. On the new repository page choose **Add file** → **Upload files**.
5. Upload the files inside this project folder (not the ZIP itself), then click **Commit changes**.
6. In `vibecraft.py`, change `GITHUB_REPO = "YOUR_GITHUB_NAME/VibeCraft-Launcher"` to your GitHub username/repository, then upload/commit that edit.
7. For updates, open **Releases** → **Create a new release**, use a tag like `v1.5.49-beta`, add release notes, and attach a built EXE or installer.
8. Keep secrets, passwords, OAuth client secrets, and access tokens out of source code and GitHub.

Official GitHub help: https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories

## Next development stage
Implement Microsoft Device Code OAuth + Xbox Live/XSTS + Minecraft Services entitlement/profile validation, then use the authenticated session to launch the game. This must be tested with a Microsoft account that owns Java Edition. Do not ask users for their Microsoft passwords inside this app.
