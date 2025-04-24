"""
A direct test script for checking the scraper's ability to parse meeting data.
Run this script directly to test the parsing functions without unit test framework.
"""
import os
import sys
from bs4 import BeautifulSoup
from datetime import datetime

# Add the parent directory to sys.path so we can import modules from there
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.utils.scraper import MeetingScraper
from src.models.meeting import Meeting, MeetingType, MeetingSection, MeetingPart

def main():
    """Main function to test scraper directly"""
    print("Testing meeting scraper directly...")
    
    # Create sample HTML for testing
    midweek_html = """
    <html>
    <body>
        <div class="header">
            <span id="p1" class="pageNumber" aria-hidden="true">APRIL 21-27</span>
        </div>
        
        <div class="bodyTxt">
            <!-- Song and Prayer section -->
            <h3 class="dc-icon--music dc-icon-size--basePlus1 dc-icon-margin-horizontal--8">
                <span id="p3" data-pid="3">Song 76 and Prayer | Opening Comments (1 min.)</span>
            </h3>
            
            <!-- Treasures section -->
            <h3 class="dc-icon--gem dc-icon-layout--top">
                <span>TREASURES FROM GOD'S WORD</span>
            </h3>
            
            <div>
                <p>1. What Makes for a Truly Rich Life? (10 min.)</p>
                <p>2. Diligent Hands Bring Riches (10 min.)</p>
                <p>3. Bible Reading (4 min.) Pr 10:1-19</p>
            </div>
            
            <!-- Ministry section -->
            <h3 class="dc-icon--wheat dc-icon-layout--top">
                <span>APPLY YOURSELF TO THE FIELD MINISTRY</span>
            </h3>
            
            <div>
                <p>4. Starting a Conversation (5 min.)</p>
                <p>5. Initial Call Video (5 min.)</p>
                <p>6. Return Visit (4 min.)</p>
            </div>
            
            <!-- Christians section -->
            <h3 class="dc-icon--users dc-icon-layout--top">
                <span>LIVING AS CHRISTIANS</span>
            </h3>
            
            <div>
                <p>7. "Keep Conquering the Evil With the Good" (15 min.)</p>
                <p>8. Congregation Bible Study (30 min.)</p>
                <p>9. Concluding Comments (3 min.)</p>
                <p>10. Concluding Song and Prayer</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    weekend_html = """
    <html>
    <body>
        <h1>
            <span class="pageNumber">APRIL 21-27</span>
        </h1>
        
        <h3 class="groupTOC">
            <span>Study Article 7: April 21-27, 2025</span>
        </h3>
        
        <p>
            <a class="it" href="/en/wol/d/r1/lp-e/2025291">
                <strong>Jehovah's Forgiveness—What It Means for You</strong>
            </a>
        </p>
        
        <div class="bodyTxt">
            <h3>Public Talk (30 min.)</h3>
            <p>How to Build a Happy Family</p>
            
            <h3>Watchtower Study (60 min.)</h3>
            <p>Jehovah's Forgiveness—What It Means for You</p>
        </div>
    </body>
    </html>
    """
    
    # Create scraper
    scraper = MeetingScraper()
    
    # Test midweek meeting parsing
    print("\n--- TESTING MIDWEEK MEETING PARSING ---")
    midweek_soup = BeautifulSoup(midweek_html, 'html.parser')
    
    # Extract date
    date_text = scraper._extract_date(midweek_soup)
    print(f"Extracted date: {date_text}")
    
    # Parse midweek meeting
    midweek_sections = scraper._parse_midweek_meeting(midweek_soup)
    
    # Print midweek meeting structure
    print(f"\nFound {len(midweek_sections)} sections in midweek meeting:")
    total_minutes = 0
    for i, section in enumerate(midweek_sections):
        section_minutes = sum(part.duration_minutes for part in section.parts)
        total_minutes += section_minutes
        print(f"\nSection {i+1}: {section.title} ({section_minutes} minutes)")
        for j, part in enumerate(section.parts):
            print(f"  Part {j+1}: {part.title} ({part.duration_minutes} min)")
    
    print(f"\nTotal midweek meeting duration: {total_minutes} minutes")
    
    # Test weekend meeting parsing
    print("\n--- TESTING WEEKEND MEETING PARSING ---")
    weekend_soup = BeautifulSoup(weekend_html, 'html.parser')
    
    # Extract date
    date_text = scraper._extract_date(weekend_soup)
    print(f"Extracted date: {date_text}")
    
    # Parse weekend meeting
    weekend_sections = scraper._parse_weekend_meeting(weekend_soup)
    
    # Print weekend meeting structure
    print(f"\nFound {len(weekend_sections)} sections in weekend meeting:")
    total_minutes = 0
    for i, section in enumerate(weekend_sections):
        section_minutes = sum(part.duration_minutes for part in section.parts)
        total_minutes += section_minutes
        print(f"\nSection {i+1}: {section.title} ({section_minutes} minutes)")
        for j, part in enumerate(section.parts):
            print(f"  Part {j+1}: {part.title} ({part.duration_minutes} min)")
    
    print(f"\nTotal weekend meeting duration: {total_minutes} minutes")
    
    print("\nTesting completed successfully!")


def test_with_actual_example():
    """Test with the example shown in your screenshot"""
    print("\n--- TESTING WITH EXAMPLE FROM SCREENSHOT ---")
    
    # Manually create meeting based on your screenshot
    sections = [
        MeetingSection(
            title="TREASURES FROM GOD'S WORD",
            parts=[
                MeetingPart(title="SONG 76 AND PRAYER | OPENING COMMENTS (1 MIN.)", duration_minutes=1),
                MeetingPart(title="1. What Makes for a Truly Rich Life?", duration_minutes=10),
                MeetingPart(title="2. Diligent Hands Bring Riches", duration_minutes=10),
                MeetingPart(title="3. Bible Reading Pr 10:1-19", duration_minutes=4)
            ]
        ),
        MeetingSection(
            title="APPLY YOURSELF TO THE FIELD MINISTRY",
            parts=[
                MeetingPart(title="4. Starting a Conversation", duration_minutes=5),
                MeetingPart(title="5. Initial Call Video", duration_minutes=5),
                MeetingPart(title="6. Return Visit", duration_minutes=4)
            ]
        ),
        MeetingSection(
            title="LIVING AS CHRISTIANS",
            parts=[
                MeetingPart(title="Song 111", duration_minutes=3),
                MeetingPart(title="7. What Blessings Make God's Servants Rich?", duration_minutes=7),
                MeetingPart(title="8. 2025 Update on the Local Design/Construction Program", duration_minutes=8),
                MeetingPart(title="9. Congregation Bible Study", duration_minutes=30),
                MeetingPart(title="Concluding Comments", duration_minutes=3),
                MeetingPart(title="Song 115 and Prayer", duration_minutes=3)
            ]
        )
    ]
    
    # Print meeting structure
    total_minutes = 0
    for i, section in enumerate(sections):
        section_minutes = sum(part.duration_minutes for part in section.parts)
        total_minutes += section_minutes
        print(f"\nSection {i+1}: {section.title} ({section_minutes} minutes)")
        for j, part in enumerate(section.parts):
            print(f"  Part {j+1}: {part.title} ({part.duration_minutes} min)")
    
    print(f"\nTotal manual meeting duration: {total_minutes} minutes")


if __name__ == "__main__":
    main()
    test_with_actual_example()