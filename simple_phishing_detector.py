"""
Gmail Phishing Detector - Analyzes spam emails and removes phishing attempts
Uses local Qwen2-VL model for image analysis with GPU acceleration
"""

import time
import json
import os
from PIL import Image
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# Configuration
CHROME_DEBUG_PORT = 9222
CONFIDENCE_THRESHOLD = 0.80
SCREENSHOT_DIR = "./phishing_screenshots"
MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

print("\n" + "="*70)
print("AUTOMATED PHISHING DETECTOR v2.0")
print("="*70)

# Load AI model
print("\n[1/4] Loading AI model...")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    device_map = "cuda:0"
    torch_dtype = torch.float16
else:
    print("  Using CPU (slower)")
    device_map = "cpu"
    torch_dtype = torch.float32

model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch_dtype,
    device_map=device_map,
    trust_remote_code=True
)
processor = AutoProcessor.from_pretrained(MODEL_NAME, trust_remote_code=True)
print("  Model loaded successfully")

# Connect to Chrome
print("\n[2/4] Connecting to Chrome...")
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", f"localhost:{CHROME_DEBUG_PORT}")
driver = webdriver.Chrome(options=chrome_options)
print(f"  Connected: {driver.current_url}")

# Navigate to spam folder
print("\n[3/4] Opening spam folder...")
driver.get('https://mail.google.com/mail/u/0/#spam')
time.sleep(3)

# Get emails from spam folder only
time.sleep(2)
all_emails = driver.find_elements(By.CSS_SELECTOR, 'tr.zA')

# Filter only valid/visible emails
emails = []
for email in all_emails:
    try:
        if email.is_displayed() and email.size['height'] > 20:
            text = email.text
            if text and len(text) > 5:
                emails.append(email)
    except:
        pass

print(f"  Found {len(emails)} emails\n")

if len(emails) == 0:
    print("Spam folder is empty!")
    exit()

# Create screenshot directory
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Statistics
stats = {'processed': 0, 'deleted': 0, 'moved': 0, 'skipped': 0}

def quick_phishing_check(sender, subject):
    """Quick rule-based check for obvious phishing"""
    score = 0
    flags = []
    
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    
    # Critical flags
    if "simulation" in subject_lower or "do not click" in subject_lower:
        score += 50
        flags.append("🚨 SIMULATION/TEST EMAIL")
    
    if "facebo." in sender_lower or "faceb0ok" in sender_lower:
        score += 40
        flags.append("🚨 FAKE FACEBOOK DOMAIN")
    
    if "paypa1" in sender_lower or "paypa" in sender_lower and "paypal" not in sender_lower:
        score += 40
        flags.append("🚨 FAKE PAYPAL DOMAIN")
    
    # Moderate flags
    prize_words = ["you've won", "claim your prize", "congratulations you", "winner"]
    if any(word in subject_lower for word in prize_words):
        score += 25
        flags.append("⚠️  Prize/lottery language")
    
    urgent_words = ["urgent", "immediate", "suspended", "verify now", "act now"]
    if any(word in subject_lower for word in urgent_words):
        score += 20
        flags.append("⚠️  Urgency tactics")
    
    return score, flags

print("[4/4] Processing emails...\n")
print("="*70)

# Process each email
for i, email_row in enumerate(emails):
    print(f"\nEMAIL {i+1}/{len(emails)}")
    print("-"*70)
    
    try:
        # Extract sender and subject
        text = email_row.text
        lines = text.split('\n')
        sender = lines[0] if len(lines) > 0 else "Unknown"
        subject = lines[1] if len(lines) > 1 else "No subject"
        
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        
        # Quick phishing check
        rule_score, rule_flags = quick_phishing_check(sender, subject)
        if rule_score > 0:
            print(f"\n🔍 Quick Scan Score: {rule_score}/100")
            for flag in rule_flags:
                print(f"   {flag}")
        
        # Open email to view full content
        print("\nOpening email...")
        email_row.click()
        time.sleep(5)
        
        # Take screenshot of opened email
        print("Capturing screenshot...")
        screenshot = driver.get_screenshot_as_png()
        
        # Save screenshot
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f"{SCREENSHOT_DIR}/email_{i+1}_{ts}.png"
        with open(path, 'wb') as f:
            f.write(screenshot)
        print(f"Saved: {path}")
        
        # Analyze with AI
        print("Analyzing with AI...")
        image = Image.open(io.BytesIO(screenshot))
        
        # Build detailed prompt
        prompt = f"""CRITICAL PHISHING ANALYSIS

Sender: {sender}
Subject: {subject}

Examine this email screenshot VERY CAREFULLY and look for these SPECIFIC indicators:

🔴 DEFINITE PHISHING (mark confidence 0.95):
- Contains words "SIMULATION" or "DO NOT CLICK" anywhere
- Sender domain is "Facebo." or "faceb0ok" instead of "facebook.com"
- Sender has "paypa1" or misspelled PayPal
- Subject says "You've Won" or "Claim Prize" + suspicious link
- Fake urgent account warnings with login links

🟡 SUSPICIOUS (mark confidence 0.75-0.85):
- Generic greetings with urgent action requests
- Misspelled company names
- Threatening account closure language
- Links that don't match claimed sender

🟢 LEGITIMATE (mark confidence 0.20-0.40):
- Real company newsletters (LinkedIn, Maven, Pinterest, Google)
- Proper company domains matching sender name
- Professional formatting
- Real unsubscribe links

ANALYZE THE IMAGE and respond with JSON:
{{
  "isPhishing": true or false,
  "confidence": 0.0 to 1.0,
  "reasoning": "What you see in the image that led to this conclusion"
}}

CRITICAL: Look at the ACTUAL email content in the screenshot. If you see "SIMULATION" text, it's phishing!"""

        # Prepare for model
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }]
        
        text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(text=[text_input], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
        inputs = inputs.to(model.device)
        
        # Generate analysis with higher temperature for variety
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=512, temperature=0.5, do_sample=True)
        
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
        response_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        
        # Parse JSON
        response_text = response_text.strip()
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        try:
            analysis = json.loads(response_text)
        except:
            print("  ⚠️  AI response parsing failed, using rule-based decision")
            if rule_score >= 50:
                analysis = {"isPhishing": True, "confidence": 0.90, "reasoning": f"Rule-based: {', '.join(rule_flags)}"}
            else:
                analysis = {"isPhishing": False, "confidence": 0.60, "reasoning": "Parse error - conservative approach"}
        
        # Get AI analysis
        is_phishing = analysis.get('isPhishing', False)
        ai_confidence = analysis.get('confidence', 0)
        reasoning = analysis.get('reasoning', 'N/A')
        
        # OVERRIDE: If rules strongly indicate phishing, force it
        if rule_score >= 50:
            if not is_phishing:
                print(f"  🔧 OVERRIDE: Rules detected strong phishing signals")
                is_phishing = True
                ai_confidence = max(ai_confidence, 0.90)
                reasoning = f"Rule override + {reasoning}"
            else:
                # Boost confidence if both agree
                ai_confidence = min(0.95, ai_confidence + 0.10)
        
        # Display results
        print(f"\n📊 Final Analysis:")
        print(f"  Phishing: {'YES' if is_phishing else 'NO'}")
        print(f"  Confidence: {ai_confidence*100:.0f}%")
        print(f"  Reasoning: {reasoning}")
        
        # Return to spam folder FIRST
        print("\nReturning to spam folder...")
        driver.get('https://mail.google.com/mail/u/0/#spam')
        time.sleep(3)
        
        # Now take action on the email from the spam list
        if is_phishing and ai_confidence >= CONFIDENCE_THRESHOLD:
            print(f"\n🗑️  ACTION: DELETE (phishing: {ai_confidence*100:.0f}% confidence)")
            
            try:
                # Find the email row again in spam list
                emails = driver.find_elements(By.CSS_SELECTOR, 'tr.zA')
                
                # Find matching email by sender/subject
                found = False
                for email_row in emails:
                    try:
                        row_text = email_row.text
                        if sender in row_text and subject[:20] in row_text:
                            found = True
                            
                            # Hover over the row to reveal delete button
                            actions = ActionChains(driver)
                            actions.move_to_element(email_row).perform()
                            time.sleep(1)
                            
                            # Find delete button in the row
                            delete_btn = email_row.find_element(By.CSS_SELECTOR, '[data-tooltip*="Delete"]')
                            delete_btn.click()
                            print("  ✓ Deleted")
                            time.sleep(1)
                            
                            # Confirm if needed
                            try:
                                confirm = driver.find_element(By.XPATH, '//button[contains(text(), "Delete forever")]')
                                confirm.click()
                            except:
                                pass
                            
                            stats['deleted'] += 1
                            time.sleep(2)
                            break
                    except:
                        continue
                
                if not found:
                    print("  ⚠️  Could not locate email")
                    stats['skipped'] += 1
                        
            except Exception as e:
                print(f"  ❌ Delete failed: {e}")
                stats['skipped'] += 1
        
        else:
            action_reason = "safe" if not is_phishing else f"low confidence {ai_confidence*100:.0f}%"
            print(f"\n📥 ACTION: MOVE TO INBOX ({action_reason})")
            
            try:
                emails = driver.find_elements(By.CSS_SELECTOR, 'tr.zA')
                
                found = False
                for email_row in emails:
                    try:
                        row_text = email_row.text
                        if sender in row_text and subject[:20] in row_text:
                            found = True
                            
                            # Click to select
                            email_row.click()
                            time.sleep(1)
                            
                            # Find "Remove label Spam" button
                            not_spam_btn = driver.find_element(By.CSS_SELECTOR, '[aria-label*="Remove label Spam"]')
                            driver.execute_script("arguments[0].click();", not_spam_btn)
                            print("  ✓ Moved to inbox")
                            
                            stats['moved'] += 1
                            time.sleep(2)
                            break
                    except:
                        try:
                            # Try keyboard shortcut
                            actions = ActionChains(driver)
                            actions.send_keys('!').perform()
                            print("  ✓ Moved to inbox (shortcut)")
                            found = True
                            stats['moved'] += 1
                            time.sleep(2)
                            break
                        except:
                            continue
                
                if not found:
                    print("  ⚠️  Could not locate email")
                    stats['skipped'] += 1
                        
            except Exception as e:
                print(f"  ❌ Move failed: {e}")
                stats['skipped'] += 1
        
        stats['processed'] += 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        stats['skipped'] += 1
        continue

# Final statistics
print("\n" + "="*70)
print("📊 FINAL RESULTS")
print("="*70)
print(f"Emails Processed:      {stats['processed']}")
print(f"Phishing Deleted:      {stats['deleted']}")
print(f"Safe (Moved to Inbox): {stats['moved']}")
print(f"Skipped/Errors:        {stats['skipped']}")
print("="*70)
print(f"\n✓ Done! Screenshots saved in: {SCREENSHOT_DIR}")
