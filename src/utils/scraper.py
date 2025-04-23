"""
Web scraper for fetching meeting data from wol.jw.org
"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dateutil.parser import parse as parse_date

from src.models.meeting import Meeting, MeetingSection, MeetingPart, MeetingType

#TODO: make a mapping for languages and their meeting paths
class MeetingScraper:
    """Scraper for fetching meeting data from wol.jw.org"""
    
    BASE_URL = "https://wol.jw.org"
    MEETINGS_PATH = "/en/wol/meetings/r1/lp-e"
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.session = requests.Session()
        
        # Set language in URL
        lang_code = language if language != "en" else "r1/lp-e"
        self.meetings_url = f"{self.BASE_URL}/{language}/wol/meetings/{lang_code}"
    
    def get_current_meeting_urls(self) -> Dict[MeetingType, str]:
        """Get URLs for the current week's meetings"""
        response = self.session.get(self.meetings_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch meetings page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        meeting_links = {}
        
        # Find meeting links on the page
        # This will need to be adjusted based on the actual structure of the page
        meeting_items = soup.select(".meetingItems li a")
        
        for item in meeting_items:
            title = item.get_text().strip().lower()
            url = item.get("href")
            
            if url:
                full_url = f"{self.BASE_URL}{url}"
                
                # Determine meeting type from title
                if "treasures" in title or "ministry" in title:
                    meeting_links[MeetingType.MIDWEEK] = full_url
                elif "watchtower" in title or "public" in title:
                    meeting_links[MeetingType.WEEKEND] = full_url
        
        return meeting_links
    
    def scrape_meeting(self, url: str, meeting_type: MeetingType) -> Meeting:
        """Scrape meeting data from a specific URL"""
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch meeting page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract meeting title and date
        header = soup.select_one("header h1")
        title = header.get_text().strip() if header else "Meeting"
        
        # Extract date from the header or content
        date_elem = soup.select_one(".pubDate")
        meeting_date = datetime.now()
        if date_elem:
            date_text = date_elem.get_text().strip()
            try:
                meeting_date = parse_date(date_text)
            except (ValueError, TypeError):
                # If date parsing fails, use current date
                pass
        
        # Extract meeting sections and parts
        sections = []
        
        if meeting_type == MeetingType.MIDWEEK:
            sections = self._parse_midweek_meeting(soup)
        elif meeting_type == MeetingType.WEEKEND:
            sections = self._parse_weekend_meeting(soup)
        
        # Create default time based on meeting type
        start_time = datetime.now().time()
        
        # Create Meeting object
        meeting = Meeting(
            meeting_type=meeting_type,
            title=title,
            date=meeting_date,
            start_time=start_time,
            sections=sections,
            language=self.language
        )
        
        return meeting
    
    def _parse_midweek_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse midweek meeting structure"""
        sections = []
        
        # Find main sections - this will need adjustment based on actual HTML structure
        section_elements = soup.select(".section")
        
        for section_elem in section_elements:
            # Get section title
            section_title_elem = section_elem.select_one("h2")
            section_title = section_title_elem.get_text().strip() if section_title_elem else "Untitled Section"
            
            # Get parts within this section
            parts = []
            part_elements = section_elem.select(".bodyTxt")
            
            for part_elem in part_elements:
                # Extract part title
                part_title_elem = part_elem.select_one("h3, strong")
                part_title = part_title_elem.get_text().strip() if part_title_elem else "Untitled Part"
                
                # Extract duration (in minutes)
                duration = 5  # Default duration
                duration_text = part_elem.get_text()
                duration_match = re.search(r'(\d+)\s*min', duration_text)
                if duration_match:
                    duration = int(duration_match.group(1))
                
                # Create part object
                part = MeetingPart(
                    title=part_title,
                    duration_minutes=duration
                )
                parts.append(part)
            
            # Create section object
            section = MeetingSection(
                title=section_title,
                parts=parts
            )
            sections.append(section)
        
        return sections
    
    def _parse_weekend_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse weekend meeting structure"""
        sections = []
        
        # Weekend meeting typically has Public Talk and Watchtower Study
        
        # Public Talk section
        public_talk_parts = [
            MeetingPart(
                title="Opening Prayer",
                duration_minutes=1
            ),
            MeetingPart(
                title="Public Talk",
                duration_minutes=30
            )
        ]
        
        public_talk_section = MeetingSection(
            title="Public Talk",
            parts=public_talk_parts
        )
        sections.append(public_talk_section)
        
        # Watchtower Study section
        watchtower_parts = [
            MeetingPart(
                title="Watchtower Study",
                duration_minutes=60
            ),
            MeetingPart(
                title="Concluding Prayer",
                duration_minutes=1
            )
        ]
        
        watchtower_section = MeetingSection(
            title="Watchtower Study",
            parts=watchtower_parts
        )
        sections.append(watchtower_section)
        
        return sections
    
    def update_meetings(self) -> Dict[MeetingType, Meeting]:
        """Fetch and update all current meetings"""
        meeting_links = self.get_current_meeting_urls()
        meetings = {}
        
        for meeting_type, url in meeting_links.items():
            try:
                meeting = self.scrape_meeting(url, meeting_type)
                meetings[meeting_type] = meeting
            except Exception as e:
                print(f"Error fetching {meeting_type.value} meeting: {e}")
        
        return meetings