# 🛡️ AI Phishing Email Detector

An intelligent automation agent that uses AI vision models to detect and delete phishing emails from your Gmail spam folder. The agent analyzes email screenshots using advanced reasoning models to identify sophisticated phishing attempts.

## ✨ Features

- 🤖 **Automated Detection**: AI-powered analysis of email content
- 🎯 **High Accuracy**: Detects domain typosquatting, credential harvesting, and brand impersonation
- 🔒 **Safe Operation**: Only processes emails already in spam folder
- 📸 **Visual Analysis**: Screenshot-based detection catches visual phishing tricks
- 🔍 **Detailed Reasoning**: Provides explanation for each decision
- ⚡ **Background Operation**: Works independently while you continue other tasks

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8+
- NVIDIA GPU with 6GB+ VRAM (recommended) or CPU
- Google Chrome browser

### Installation

1. **Install Python dependencies:**

```bash
pip install selenium transformers torch pillow qwen-vl-utils accelerate
```

2. **Install CUDA-enabled PyTorch (for GPU acceleration):**

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. **Clone the repository:**

```bash
git clone https://github.com/yourusername/ai-phishing-detector
cd ai-phishing-detector
```

### Setup Chrome for Remote Debugging

**Step 1:** Close all Chrome windows

```powershell
taskkill /F /IM chrome.exe /T
```

**Step 2:** Wait a moment

```powershell
Start-Sleep -Seconds 3
```

**Step 3:** Start Chrome with debugging enabled

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

> **Note:** The `--user-data-dir` flag creates a separate Chrome profile for automation.

**Step 4:** Verify Chrome is ready

You should see:
- A new Chrome window opens
- Message: "Chrome is being controlled by automated test software"
- Login to Gmail in this window

**Step 5:** Verify debugging port is open

```powershell
netstat -an | Select-String "9222"
```

Expected output:
```
TCP    127.0.0.1:9222         0.0.0.0:0              LISTENING
```

### Running the Detector

```bash
python simple_phishing_detector.py
```

The agent will:
1. Load the AI model (first run downloads ~4GB)
2. Connect to your Chrome session
3. Navigate to your spam folder
4. Process each email automatically

While it runs, you can:
- ✅ Continue working in other applications
- ✅ Browse in a different Chrome window
- ✅ The agent works independently in the background

## ⚙️ Configuration

Edit `simple_phishing_detector.py` to adjust settings:

```python
# Confidence threshold (0.0 to 1.0)
# Higher = fewer false positives, might miss some phishing
# Lower = catches more phishing, more false positives
CONFIDENCE_THRESHOLD = 0.75  # Default: 75%

# Screenshot directory
SCREENSHOT_DIR = "./phishing_screenshots"
```

## 🧠 How It Works

1. **Opens Email**: Clicks each email in spam folder
2. **Captures Screenshot**: Takes full-page screenshot of email content
3. **AI Analysis**: Qwen2-VL reasoning model analyzes:
   - Domain typosquatting (paypa1.com vs paypal.com)
   - Credential harvesting attempts
   - Urgent/threatening language
   - Brand impersonation
   - Suspicious links and buttons
4. **Decision**: Makes DELETE or KEEP decision with confidence score
5. **Action**: Automatically executes the decision
6. **Repeat**: Moves to next email

## 📝 Example Output

```
EMAIL 1/5
From: security@paypa1.com
Subject: Urgent: Account Suspended

Analysis Result:
  Phishing: True
  Confidence: 95%
  Reasoning: Domain typosquatting detected (paypa1.com), 
             urgent language, credential request form

ACTION: DELETE (phishing detected)
  ✓ Located email in list
  ✓ Clicked Delete
  ✅ Email deleted permanently
```

## ⚠️ Important Notes

### False Positives

The 2B model may occasionally mark legitimate emails as phishing (~10-20% rate). To reduce false positives:

- **Increase confidence threshold**: Set to 0.85 or 0.90
- **Use larger model**: Qwen2-VL-7B (requires 16GB GPU)
- **Use API-based alternatives**: Gemini 2.5 Flash, DeepSeek v3

### API Alternatives

Don't have a GPU? Use these API-based reasoning models:

- **Gemini 2.5 Flash** (Google): Free tier available
- **DeepSeek v3** (DeepSeek): Open-source, affordable
- **GPT-4 Vision** (OpenAI): High accuracy, paid

Replace the `analyze_with_local_model()` function with API calls.

### Security

- ✅ The agent only works on emails already marked as spam
- ✅ It never touches your inbox directly
- ✅ All processing happens locally (for local model)
- ✅ Screenshots saved for audit trail

## 🛠️ Troubleshooting

### Chrome connection fails

**Error:** `No browser contexts found`

**Solution:** Make sure Chrome is running with debugging enabled (see Setup step 3)

### Model won't load

**Error:** `CUDA out of memory`

**Solution:** Your GPU doesn't have enough VRAM. Either:
- Use CPU mode (slower but works)
- Close other GPU-intensive applications
- Use a smaller model

### No emails detected

**Error:** `Found 0 emails`

**Solution:**
- Verify you're logged into Gmail
- Check that you're viewing the spam folder
- Ensure you have emails in spam

## 📚 Technical Details

- **Model**: Qwen/Qwen2-VL-2B-Instruct
- **Framework**: PyTorch + Transformers
- **Automation**: Selenium WebDriver
- **Browser**: Chrome with remote debugging

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Support for other email providers (Outlook, Yahoo, etc.)
- Better false positive handling
- Multi-language support
- Batch processing optimization

## 📄 License

MIT License - feel free to use and modify

## ⚠️ Disclaimer

This tool is for educational and personal use. Always review deleted emails periodically. The AI may make mistakes. Use at your own risk.

---

**Star ⭐ this repo if you found it useful!**
