#!/usr/bin/env python3
"""
Publish article (PNG cards) to Xiaohongshu draft box.
Uses the browser CDP connection (port 9333) to automate uploading.

Usage:
  echo '{"title":"...","images":["/path/1.png","/path/2.png"],"description":"..."}' | python3 publish_xiaohongshu.py
"""
import json, sys, time, os
from pathlib import Path
from typing import List

XHS_CREATOR_URL = "https://creator.xiaohongshu.com"
XHS_UPLOAD_URL = "https://creator.xiaohongshu.com/publish/publish?type=image"


def wait_for_page(browser_type: str = None, timeout: int = 5):
    """Wait for page to load/stabilize"""
    time.sleep(timeout)


def publish_to_xiaohongshu(title: str, image_paths: List[str], description: str = "",
                           tags: List[str] = None):
    """
    Publish images to Xiaohongshu drafts.
    
    Args:
        title: Article title
        image_paths: List of PNG paths (absolute)
        description: Text description
        tags: List of tags
    """
    from playwright.sync_api import sync_playwright
    
    tags = tags or []
    
    # Connect to the VNC Chrome via CDP
    cdp_url = "http://localhost:9333"
    
    print(f"📸 Connecting to Chrome at {cdp_url}...", flush=True)
    
    with sync_playwright() as p:
        # Connect to existing browser
        browser = p.chromium.connect_over_cdp(cdp_url)
        
        # Check existing pages
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = browser.new_context()
        
        # Use existing page or create new one
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = context.new_page()
        
        # Check if we're already logged in by visiting creator page
        print(f"🔍 Checking login status...", flush=True)
        page.goto(f"{XHS_CREATOR_URL}/publish/publish?type=image", 
                   wait_until='networkidle', timeout=30000)
        time.sleep(3)
        
        # Check for login redirect
        current_url = page.url
        if "login" in current_url or "sign" in current_url:
            print("❌ Not logged in! Need to login first.", flush=True)
            return {"success": False, "error": "not_logged_in", "url": current_url}
        
        print(f"✅ Logged in! Current URL: {current_url}", flush=True)
        
        # Upload images
        print(f"📤 Uploading {len(image_paths)} images...", flush=True)
        
        # Find file input element and upload
        uploaded = []
        for img_path in image_paths:
            abs_path = str(Path(img_path).absolute())
            if not os.path.exists(abs_path):
                print(f"⚠️ File not found: {abs_path}", flush=True)
                continue
            
            try:
                # Find file input elements
                file_inputs = page.locator('input[type="file"]')
                count = file_inputs.count()
                print(f"Found {count} file input(s)", flush=True)
                
                if count > 0:
                    file_input = file_inputs.first
                    file_input.set_input_files(abs_path)
                    print(f"  ✅ Uploaded: {Path(abs_path).name}", flush=True)
                    uploaded.append(abs_path)
                    time.sleep(2)  # Wait for upload processing
                else:
                    print(f"  ⚠️ No file input found on page", flush=True)
            except Exception as e:
                print(f"  ❌ Failed to upload {Path(abs_path).name}: {e}", flush=True)
        
        if not uploaded:
            print("❌ No images were uploaded", flush=True)
            return {"success": False, "error": "upload_failed"}
        
        # Wait for uploads to process
        time.sleep(3)
        
        # Fill in title
        print(f"✏️ Filling in title...", flush=True)
        try:
            title_input = page.locator('input[placeholder*="标题"], input[placeholder*="title"], [class*="title"] input')
            if title_input.count() > 0:
                title_input.first.fill(title[:20])  # XHS title limit
                print(f"  ✅ Title set: {title[:20]}", flush=True)
        except Exception as e:
            print(f"  ⚠️ Could not set title: {e}", flush=True)
        
        # Fill in description
        if description:
            print(f"✏️ Filling in description...", flush=True)
            try:
                desc_input = page.locator(
                    '[placeholder*="正文"], [placeholder*="description"], '
                    '[contenteditable="true"], [class*="ql-editor"], '
                    '[class*="editor"] div[contenteditable]'
                )
                if desc_input.count() > 0:
                    desc_input.first.fill(description)
                    print(f"  ✅ Description set", flush=True)
            except Exception as e:
                print(f"  ⚠️ Could not set description: {e}", flush=True)
        
        # Add tags
        if tags:
            print(f"🏷️ Adding tags...", flush=True)
            for tag in tags[:5]:
                try:
                    tag_input = page.locator('input[placeholder*="话题"], [class*="tag"] input')
                    if tag_input.count() > 0:
                        tag_input.first.fill(tag)
                        time.sleep(0.5)
                        tag_input.first.press("Enter")
                        print(f"  ✅ Tag added: {tag}", flush=True)
                except Exception as e:
                    print(f"  ⚠️ Could not add tag {tag}: {e}", flush=True)
        
        # Save as draft (don't publish directly)
        print(f"💾 Saving as draft...", flush=True)
        try:
            # Look for draft/save button
            draft_btn = page.locator(
                'button:has-text("存草稿"), button:has-text("草稿"), '
                'button:has-text("save"), [class*="draft"] button, '
                'button:has-text("暂存")'
            )
            if draft_btn.count() > 0:
                draft_btn.first.click()
                print(f"  ✅ Saved as draft!", flush=True)
                time.sleep(3)
            else:
                print(f"  ⚠️ Draft button not found, checking page...", flush=True)
        except Exception as e:
            print(f"  ⚠️ Could not save draft: {e}", flush=True)
        
        # Take a confirmation screenshot
        try:
            screenshot_path = f"/tmp/xhs_publish_{int(time.time())}.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}", flush=True)
        except Exception as e:
            print(f"  ⚠️ Screenshot failed: {e}", flush=True)
        
        print(f"\n✅ Publishing flow complete!", flush=True)
        return {
            "success": True,
            "uploaded": len(uploaded),
            "draft_url": page.url,
        }


if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = publish_to_xiaohongshu(
        title=data.get("title", ""),
        image_paths=data.get("images", []),
        description=data.get("description", ""),
        tags=data.get("tags", []),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
