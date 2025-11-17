#!/usr/bin/env python3
"""
Simple test to launch a visible browser in VNC
"""
import os
import asyncio
from playwright.async_api import async_playwright

async def launch_visible_browser():
    """Launch a visible Chromium browser on VNC display"""
    # Set DISPLAY for VNC
    os.environ['DISPLAY'] = ':0'
    
    print("🎬 Launching visible browser on VNC...")
    print(f"📺 DISPLAY = {os.environ.get('DISPLAY')}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        print("✅ Browser launched successfully!")
        
        page = await browser.new_page()
        print("📄 New page created")
        
        # Navigate to Google
        print("🔍 Navigating to Google...")
        await page.goto('https://www.google.com')
        print("✅ Loaded Google!")
        
        # Search for something
        await page.fill('textarea[name="q"]', '5 SHOT FIREARMS YUMA AZ')
        await page.press('textarea[name="q"]', 'Enter')
        print("🔍 Performed search")
        
        # Wait to see results
        await asyncio.sleep(5)
        
        print("✅ Demo complete! Closing browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(launch_visible_browser())
