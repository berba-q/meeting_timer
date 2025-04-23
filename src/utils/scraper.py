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

class MeetingScraper:
    """Scraper for fetching meeting data from wol.jw.org"""
    
    BASE_URL = "https://wol.jw.org"
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.session = requests.Session()
        
        # Set language in URL
        lang_code = "r1/lp-e" if language == "en" else language
        self.meetings_url = f"{self.BASE_URL}/{language}/wol/meetings/{lang_code}"
    
    def get_current_meeting_urls(self) -> Dict[MeetingType, str]:
        """Get URLs for the current week's meetings"""
        response = self.session.get(self.meetings_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch meetings page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        meeting_links = {}
        
        # Find all links on the page
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            link_text = link.get_text().strip().lower()
            
            # Skip links without href or text
            if not href or not link_text:
                continue
            
            # Make the URL absolute if it's not already
            if not href.startswith('http'):
                href = f"{self.BASE_URL}{href}"
            
            # Look for specific indicators in the text or href
            is_midweek = any(term in link_text for term in ['life', 'ministry', 'treasures', 'apply yourself'])
            is_weekend = any(term in link_text for term in ['watchtower', 'study article', 'public talk', 'jehovah'])
            
            # Additional check for href patterns
            if '/lf/' in href or '/mwb/' in href:
                is_midweek = True
            if '/w/' in href or '/wp/' in href or '/d/' in href:
                is_weekend = True
                
            # If this link matches a meeting type and we haven't found one yet
            if is_midweek and MeetingType.MIDWEEK not in meeting_links:
                meeting_links[MeetingType.MIDWEEK] = href
            
            if is_weekend and MeetingType.WEEKEND not in meeting_links:
                meeting_links[MeetingType.WEEKEND] = href
        
        # If we couldn't find the links directly, check for strong tags that might contain article titles
        if MeetingType.WEEKEND not in meeting_links:
            # Look for Watchtower study title in a strong tag
            watchtower_titles = soup.find_all('strong')
            for title_elem in watchtower_titles:
                title_text = title_elem.get_text().strip()
                # If this looks like a Watchtower title
                if len(title_text) > 10 and "—" in title_text:
                    # Look for a parent link
                    parent_link = title_elem.find_parent('a')
                    if parent_link and parent_link.has_attr('href'):
                        href = parent_link.get('href')
                        if not href.startswith('http'):
                            href = f"{self.BASE_URL}{href}"
                        meeting_links[MeetingType.WEEKEND] = href
                        break
        
        return meeting_links
    
    def scrape_meeting(self, url: str, meeting_type: MeetingType) -> Meeting:
        """Scrape meeting data from a specific URL"""
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch meeting page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract date information
        date_text = self._extract_date(soup)
        
        # Create title based on meeting type and date
        if meeting_type == MeetingType.MIDWEEK:
            title = f"Midweek Meeting: {date_text}"
        else:
            title = f"Weekend Meeting: {date_text}"
        
        # Parse date
        meeting_date = datetime.now()
        try:
            # Try to extract a date from the date text
            date_match = re.search(r'(\w+)\s+(\d+)(?:\s*-\s*\d+)?(?:,\s*(\d{4}))?', date_text)
            if date_match:
                month, day, year = date_match.groups()
                year = year or str(datetime.now().year)
                date_str = f"{month} {day}, {year}"
                meeting_date = parse_date(date_str)
        except (ValueError, TypeError):
            # If date parsing fails, use current date
            pass
        
        # Extract meeting sections and parts based on meeting type
        if meeting_type == MeetingType.MIDWEEK:
            sections = self._parse_midweek_meeting(soup)
        else:
            sections = self._parse_weekend_meeting(soup)
        
        # Use current time as default start time
        start_time = datetime.now().time()
        
        # Create and return Meeting object
        meeting = Meeting(
            meeting_type=meeting_type,
            title=title,
            date=meeting_date,
            start_time=start_time,
            sections=sections,
            language=self.language
        )
        
        return meeting
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract date information from the page"""
        # Try various selectors that might contain date information
        date_elements = [
            soup.select_one('.pageNumber'),  # Page number span
            soup.select_one('[id*="pageNum"]'),  # Element with pageNum in ID
            soup.select_one('h1'),  # Main heading
            soup.select_one('header h1'),  # Header heading
            soup.find(string=re.compile(r'\w+\s+\d+\s*-\s*\d+'))  # Text with date pattern
        ]
        
        for element in date_elements:
            if element and element.get_text().strip():
                text = element.get_text().strip()
                # Look for date patterns like "April 21-27"
                date_match = re.search(r'\w+\s+\d+\s*-\s*\d+', text)
                if date_match:
                    return date_match.group(0)
        
        # If no date found, return current month and week
        now = datetime.now()
        month = now.strftime("%B")
        day = now.day
        # Calculate the end of the week (day + 6, or end of month)
        end_day = min(day + 6, (now.replace(month=now.month+1, day=1) - timedelta(days=1)).day)
        return f"{month} {day}-{end_day}"
    
    def _extract_duration_and_title(self, element) -> Tuple[int, str]:
        """Extract duration in minutes and title from an element"""
        text = element.get_text().strip()
        
        # Look for patterns like "(10 min.)" or "(10 min)"
        duration_match = re.search(r'\((\d+)\s*min', text)
        if duration_match:
            duration = int(duration_match.group(1))
            # Remove the duration part from the title
            title = re.sub(r'\(\d+\s*min\.*\)', '', text).strip()
        else:
            # Handle special cases
            title = text
            if "song" in text.lower() or "prayer" in text.lower():
                duration = 1  # Default for songs and prayers
            elif "opening comments" in text.lower():
                duration = 1  # Default for opening comments
            elif "bible reading" in text.lower():
                duration = 4  # Default for Bible reading
            elif "concluding comments" in text.lower():
                duration = 3  # Default for concluding comments
            elif "spiritual gems" in text.lower():
                duration = 10  # Default for spiritual gems
            elif "congregation bible study" in text.lower():
                duration = 30  # Default for congregation Bible study
            elif "watchtower study" in text.lower():
                duration = 60  # Default for Watchtower study
            elif "public talk" in text.lower():
                duration = 30  # Default for public talk
            else:
                duration = 5  # Default for other parts
        
        return duration, title
    
    def _parse_midweek_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse midweek meeting structure"""
        sections = []
        current_section = None
        
        # Look for section headers with icon classes
        section_headers = soup.select("h3.dc-icon--gem, h3.dc-icon--wheat, h3.dc-icon--users, h3.dc-icon--music")
        
        # If no headers found with that selector, try more general selectors
        if not section_headers:
            section_headers = soup.select("h3, h2")
        
        for header in section_headers:
            header_text = header.get_text().strip().upper()
            
            # Skip empty headers
            if not header_text:
                continue
            
            # Check for section indicators
            is_section = False
            if any(keyword in header_text for keyword in ["TREASURES", "APPLY YOURSELF", "FIELD MINISTRY", "LIVING AS CHRISTIANS"]):
                is_section = True
            
            # Check for icon classes that indicate sections
            if header.get("class"):
                classes = " ".join(header.get("class"))
                if any(icon in classes for icon in ["dc-icon--gem", "dc-icon--wheat", "dc-icon--users"]):
                    is_section = True
            
            if is_section:
                # Create a new section
                current_section = MeetingSection(
                    title=header_text,
                    parts=[]
                )
                sections.append(current_section)
            elif "SONG" in header_text and "PRAYER" in header_text:
                # Handle opening song and prayer
                opening_section = MeetingSection(
                    title="Opening",
                    parts=[
                        MeetingPart(
                            title=header_text,
                            duration_minutes=1
                        )
                    ]
                )
                sections.append(opening_section)
            elif current_section:
                # This is a part within the current section
                duration, title = self._extract_duration_and_title(header)
                
                # Add the part to the current section
                part = MeetingPart(
                    title=title,
                    duration_minutes=duration
                )
                current_section.parts.append(part)
        
        # Look for parts in paragraphs
        if sections:
            paragraphs = soup.select("p")
            for p in paragraphs:
                p_text = p.get_text().strip()
                
                # Skip empty paragraphs
                if not p_text:
                    continue
                
                # Extract part information
                duration_match = re.search(r'(\d+)\s*min', p_text)
                if duration_match:
                    duration = int(duration_match.group(1))
                    title = re.sub(r'\(\d+\s*min\.*\)', '', p_text).strip()
                    
                    # Simple heuristic to associate with the nearest section
                    # Find position in the list of sections
                    matched_section = None
                    
                    # Check for part number prefixes like "1." to associate with sections
                    part_num_match = re.match(r'^\d+\.', title)
                    if part_num_match and len(sections) >= 1:
                        matched_section = sections[0]  # Usually Treasures section
                    elif "congregation bible study" in title.lower() and len(sections) >= 3:
                        matched_section = sections[2]  # Usually Christians section 
                    elif "concluding comments" in title.lower() and len(sections) >= 3:
                        matched_section = sections[2]  # Usually Christians section
                    elif "bible reading" in title.lower() and len(sections) >= 1:
                        matched_section = sections[0]  # Usually Treasures section
                    elif "initial call" in title.lower() or "return visit" in title.lower() and len(sections) >= 2:
                        matched_section = sections[1]  # Usually Ministry section
                    
                    # If we found a matching section, add the part
                    if matched_section:
                        part = MeetingPart(
                            title=title,
                            duration_minutes=duration
                        )
                        matched_section.parts.append(part)
        
        # If we couldn't extract any sections, create default ones
        if not sections:
            sections = [
                MeetingSection(
                    title="Opening",
                    parts=[
                        MeetingPart(title="Song and Prayer", duration_minutes=5)
                    ]
                ),
                MeetingSection(
                    title="TREASURES FROM GOD'S WORD",
                    parts=[
                        MeetingPart(title="Bible Reading", duration_minutes=4)
                    ]
                ),
                MeetingSection(
                    title="APPLY YOURSELF TO THE FIELD MINISTRY",
                    parts=[
                        MeetingPart(title="Initial Call", duration_minutes=2),
                        MeetingPart(title="Return Visit", duration_minutes=3)
                    ]
                ),
                MeetingSection(
                    title="LIVING AS CHRISTIANS",
                    parts=[
                        MeetingPart(title="Congregation Bible Study", duration_minutes=30),
                        MeetingPart(title="Concluding Comments", duration_minutes=3)
                    ]
                )
            ]
        
        return sections
    
    def _parse_weekend_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse weekend meeting structure"""
        # Look for Watchtower title
        watchtower_title = ""
        
        # Try to find Watchtower title in a strong tag
        for strong in soup.find_all('strong'):
            text = strong.get_text().strip()
            if len(text) > 10 and ("—" in text or "Jehovah" in text):
                watchtower_title = text
                break
        
        # If not found, look for study article
        if not watchtower_title:
            study_header = soup.find(string=re.compile(r'Study Article'))
            if study_header:
                parent = study_header.parent
                if parent:
                    next_a = parent.find_next('a')
                    if next_a:
                        watchtower_title = next_a.get_text().strip()
        
        # If still not found, look for title in h3
        if not watchtower_title:
            for h3 in soup.find_all('h3'):
                text = h3.get_text().strip()
                if "Study Article" in text:
                    watchtower_title = text
                    break
        
        # Create default structure with Watchtower title if found
        if not watchtower_title:
            watchtower_title = "Watchtower Study"
        
        # Try to find meeting parts directly in the HTML
        public_talk_title = "Public Talk"
        public_talk_found = False
        
        # Search for public talk title
        public_headers = soup.find_all(string=re.compile(r'Public Talk'))
        for header in public_headers:
            parent = header.parent
            if parent:
                next_p = parent.find_next('p')
                if next_p:
                    public_talk_title = next_p.get_text().strip()
                    public_talk_found = True
                    break
        
        # Create sections
        sections = [
            MeetingSection(
                title="Public Talk",
                parts=[
                    MeetingPart(title="Opening Prayer", duration_minutes=1),
                    MeetingPart(title=public_talk_title, duration_minutes=30)
                ]
            ),
            MeetingSection(
                title="Watchtower Study",
                parts=[
                    MeetingPart(title=watchtower_title, duration_minutes=60),
                    MeetingPart(title="Concluding Prayer", duration_minutes=1)
                ]
            )
        ]
        
        return sections
    
    def update_meetings(self) -> Dict[MeetingType, Meeting]:
        """Fetch and update all current meetings"""
        try:
            meeting_links = self.get_current_meeting_urls()
            meetings = {}
            
            for meeting_type, url in meeting_links.items():
                try:
                    meeting = self.scrape_meeting(url, meeting_type)
                    meetings[meeting_type] = meeting
                except Exception as e:
                    print(f"Error fetching {meeting_type.value} meeting: {e}")
            
            return meetings
            
        except Exception as e:
            print(f"Error updating meetings: {e}")
            return {}