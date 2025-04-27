"""
Test script for the improved MeetingScraper.
This tests both midweek and weekend meeting extraction.
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# Add the parent directory to sys.path so we can import modules from there
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.utils.scraper import MeetingScraper
from src.models.meeting import MeetingType

def test_live_scraper():
    """Test the scraper with live URLs from wol.jw.org"""
    print("Testing MeetingScraper with live URLs...\n")
    
    # Create scraper
    scraper = MeetingScraper()
    
    # Get current meeting URLs
    try:
        print("Fetching meeting URLs from wol.jw.org...")
        meeting_links = scraper.get_current_meeting_urls()
        
        print(f"Found URLs:")
        for meeting_type, url in meeting_links.items():
            print(f"- {meeting_type.value}: {url}")
        
        # Test both meeting types
        for meeting_type, url in meeting_links.items():
            print(f"\n\n--- TESTING {meeting_type.value.upper()} MEETING EXTRACTION ---")
            print(f"URL: {url}")
            
            try:
                # Fetch and parse the meeting
                meeting = scraper.scrape_meeting(url, meeting_type)
                
                # Print meeting details
                print(f"Meeting Title: {meeting.title}")
                print(f"Meeting Date: {meeting.date.strftime('%Y-%m-%d')}")
                print(f"Meeting Type: {meeting.meeting_type.value}")
                print(f"Total Duration: {meeting.total_duration_minutes} minutes")
                
                # Print sections and parts
                print("\nMeeting Structure:")
                for i, section in enumerate(meeting.sections):
                    print(f"\nSection {i+1}: {section.title} ({section.total_duration_minutes} min)")
                    for j, part in enumerate(section.parts):
                        print(f"  Part {j+1}: {part.title} ({part.duration_minutes} min)")
                
                # Special tests for weekend meeting
                if meeting_type == MeetingType.WEEKEND:
                    # Check for Watchtower title
                    watchtower_parts = [part for section in meeting.sections 
                                        for part in section.parts 
                                        if "watchtower" in part.title.lower() and "song" not in part.title.lower()]
                    
                    if watchtower_parts:
                        print("\nWatchtower Study Information:")
                        print(f"Title: {watchtower_parts[0].title}")
                        print(f"Duration: {watchtower_parts[0].duration_minutes} min")
                    
                    # Check for songs
                    song_parts = [part for section in meeting.sections 
                                  for part in section.parts 
                                  if "song" in part.title.lower()]
                    
                    if song_parts:
                        print("\nSongs Information:")
                        for i, part in enumerate(song_parts):
                            print(f"Song {i+1}: {part.title}")
                
            except Exception as e:
                print(f"Error scraping {meeting_type.value} meeting: {str(e)}")
        
        print("\n--- TEST SUMMARY ---")
        print(f"Successfully tested {len(meeting_links)} meeting types from live URLs")
        print("Testing completed!")
        
    except Exception as e:
        print(f"Error in testing: {str(e)}")

if __name__ == "__main__":
    test_live_scraper()