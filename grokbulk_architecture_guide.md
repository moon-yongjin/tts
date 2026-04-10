# Grok Bulk Automation: Default Workflow (Pure Extension)

This document defines the **Default Stable Workflow** for Grok video generation, as established in the "3 AM Stable Version" restoration.

> [!IMPORTANT]
> **Priority**: Always use the **Pure Extension Mode** (Non-Bridge) for maximum reliability and simplicity. The Python Bridge server is considered a legacy fallback.

## 🚀 Default Workflow (Pure Extension)

This mode runs entirely within the Chrome extension and does not require a local Python server.

### 1. Preparation
-   **Images**: Ensure your source images are in `~/Downloads/NB2_output`.
-   **Prompts**: Prepare your prompt list in `대본.txt`.

### 2. Execution Steps
1.  **Open Grok**: Navigate to `https://grok.com/imagine/saved`.
2.  **Open Side Panel**: Click the GrokBulk extension icon.
3.  **Load Assets**:
    -   Click **[이미지 폴더 선택]** and select the `/Users/a12/Downloads/NB2_output` directory.
4.  **Load Prompts**:
    -   Copy the contents of `대본.txt` and paste them into the **[프롬프트 입력]** box.
5.  **Run**:
    -   Click **[🎬 연속 생성 가동]**.
    -   The extension will automatically handle: **Upload -> Video Toggle -> Prompt Typing -> Submission**.

---

## 🛠️ Fallback Tools
If the browser extension needs additional HID (Human Interface Device) support or if you prefer a Python-driven approach:

-   **[grok_py_bot.py](file:///Users/a12/projects/tts/grok_py_bot.py)**: A standalone Python script using `pyautogui` for keyboard-level automation. 
    -   Launch via: `그록터보배치.command`
-   **Bridge Server (Legacy)**: `grok_bridge_server.py` can still be used for folder-monitoring automation if needed.

## 📁 Key File Locations
-   **Extension Folder**: `/Users/a12/projects/tts/grok_extension`
-   **Input Folder**: `/Users/a12/Downloads/NB2_output`
-   **Scripts**: `/Users/a12/projects/tts/`
