"""
Test script for the improved MeetingScraper.
This tests both midweek and weekend meeting extraction.
"""
import os
import sys
from bs4 import BeautifulSoup
import re

# Add the parent directory to sys.path so we can import modules from there
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.utils.scraper import MeetingScraper

def test_meeting_scraper():
    """Test the scraper with sample HTML for both meeting types"""
    print("Testing MeetingScraper with sample HTML...\n")
    
    # Create scraper
    scraper = MeetingScraper()
    
    # ---------- MIDWEEK MEETING TEST ----------
    print("--- TESTING MIDWEEK MEETING EXTRACTION ---")
    
    # Create sample HTML for midweek meeting
    midweek_html = """
    <html>
    <body>
        <div class="bodyTxt">
            <span id="p1" class="pageNumber">APRIL 21-27</span>
            
            <h3 class="dc-icon--music">
                <span>Song 76 and Prayer | Opening Comments (1 min.)</span>
            </h3>
            
            <h3 class="dc-icon--gem">
                <span>TREASURES FROM GOD'S WORD</span>
            </h3>
            
            <h3>
                <strong>1. What Makes for a Truly Rich Life?</strong>
            </h3>
            <p>(10 min.)</p>
            
            <h3>
                <strong>2. Spiritual Gems</strong>
            </h3>
            <p>(10 min.)</p>
            
            <h3>
                <strong>3. Bible Reading</strong>
            </h3>
            <p>(4 min.)</p>
            
            <h3 class="dc-icon--wheat">
                <span>APPLY YOURSELF TO THE FIELD MINISTRY</span>
            </h3>
            
            <h3>
                <strong>4. Starting a Conversation</strong>
            </h3>
            <p>(4 min.) HOUSE TO HOUSE. The person tells you that he is an atheist.</p>
            
            <h3>
                <strong>5. Starting a Conversation</strong>
            </h3>
            <p>(4 min.) INFORMAL WITNESSING. Offer a Bible study.</p>
            
            <h3>
                <strong>6. Following Up</strong>
            </h3>
            <p>(4 min.) INFORMAL WITNESSING. Show the person how to find information that may interest him on jw.org.</p>
            
            <h3 class="dc-icon--users">
                <span>LIVING AS CHRISTIANS</span>
            </h3>
            
            <h3 class="dc-icon--music">
                <strong>Song 111</strong>
            </h3>
            
            <h3>
                <strong>7. What Blessings Make God's Servants Rich?</strong>
            </h3>
            <p>(7 min.) Discussion.</p>
            
            <h3>
                <strong>8. 2025 Update on the Local Design/Construction Program</strong>
            </h3>
            <p>(8 min.)</p>
            
            <h3>
                <strong>9. Congregation Bible Study</strong>
            </h3>
            <p>(30 min.)</p>
            
            <p>Concluding Comments (3 min.) | Song 115 and Prayer</p>
        </div>
    </body>
    </html>
    """
    
    # Parse midweek HTML
    midweek_soup = BeautifulSoup(midweek_html, 'html.parser')
    
    # Test duration extraction for each part
    print("\nTesting duration extraction for midweek meeting parts:")
    for part_num in range(1, 10):
        duration = scraper._find_duration_for_part(part_num, midweek_soup)
        print(f"Part {part_num}: Found duration: {duration} minutes")
    
    # Extract date
    midweek_date = scraper._extract_date(midweek_soup)
    print(f"\nExtracted midweek date: {midweek_date}")
    
    # Parse the midweek meeting
    midweek_sections = scraper._parse_midweek_meeting(midweek_soup)
    
    # Print the parsed structure
    print("\nParsed midweek meeting structure:")
    for i, section in enumerate(midweek_sections):
        print(f"\nSection {i+1}: {section.title}")
        for j, part in enumerate(section.parts):
            print(f"  Part {j}: {part.title}")
    
    # Calculate total duration
    midweek_total = sum(sum(part.duration_minutes for part in section.parts) for section in midweek_sections)
    print(f"\nTotal midweek meeting duration: {midweek_total} minutes")
    
    # ---------- WEEKEND MEETING TEST ----------
    print("\n\n--- TESTING WEEKEND MEETING EXTRACTION ---")
    
    # Create sample HTML for weekend meeting
    weekend_html = """
    <html>
    <body>
        <div class="bodyTxt">
            <span id="p1" class="pageNumber">APRIL 21-27</span>
            
            <h3 class="groupTOC">
                <span>Study Article 7: April 21-27, 2025</span>
            </h3>
            
            <h1>
                <strong>Jehovah's Forgiveness—What It Means for You</strong>
            </h1>
            
            <h3>Public Talk (30 min.)</h3>
            <p>How to Build a Happy Family</p>
            
            <h3>Watchtower Study (60 min.)</h3>
            <p>Jehovah's Forgiveness—What It Means for You</p>
            
            <p>SONG 51</p>
            <p>SONG 77</p>
        </div>
    </body>
    </html>
    """
    
    # Parse weekend HTML
    weekend_soup = BeautifulSoup(weekend_html, 'html.parser')
    
    # Extract date
    weekend_date = scraper._extract_date(weekend_soup)
    print(f"Extracted weekend date: {weekend_date}")
    
    # Find watchtower title
    watchtower_title = ""
    for h1 in weekend_soup.find_all('h1'):
        strong_tags = h1.find_all('strong')
        if strong_tags:
            watchtower_title = strong_tags[0].get_text().strip()
            break
    
    print(f"Extracted watchtower title: {watchtower_title}")
    
    # Find songs
    songs = []
    for el in weekend_soup.find_all(['p', 'strong', 'span']):
        el_text = el.get_text().strip()
        if "SONG" in el_text.upper():
            song_num = scraper._extract_song_number(el_text)
            if song_num:
                songs.append(song_num)
    
    print(f"Extracted songs: {songs}")
    
    # Parse the weekend meeting
    weekend_sections = scraper._parse_weekend_meeting(weekend_soup)
    
    # Print the parsed structure
    print("\nParsed weekend meeting structure:")
    for i, section in enumerate(weekend_sections):
        print(f"\nSection {i+1}: {section.title}")
        for j, part in enumerate(section.parts):
            print(f"  Part {j}: {part.title}")
    
    # Calculate total duration
    weekend_total = sum(sum(part.duration_minutes for part in section.parts) for section in weekend_sections)
    print(f"\nTotal weekend meeting duration: {weekend_total} minutes")
    
    # ---------- SUMMARY ----------
    print("\n--- TEST SUMMARY ---")
    print(f"Midweek meeting: {len(midweek_sections)} sections, {midweek_total} minutes total")
    print(f"Weekend meeting: {len(weekend_sections)} sections, {weekend_total} minutes total")
    print("\nTesting completed successfully!")

if __name__ == "__main__":
    test_meeting_scraper()