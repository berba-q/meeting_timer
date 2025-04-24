"""
Web scraper for fetching meeting data from wol.jw.org
"""
import re
import requests
from bs4 import BeautifulSoup, Tag
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
    
    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in minutes from text"""
        # Look for pattern like "(10 min)" or "(10 min.)" or "10 min"
        duration_match = re.search(r'(?:\()?(\d+)\s*min\.?(?:\))?', text, re.IGNORECASE)
        if duration_match:
            return int(duration_match.group(1))
        return None
    
    def _parse_midweek_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse midweek meeting structure"""
        sections = []
        current_section = None
        
        # Find main content container
        content = soup.find('div', class_='bodyTxt') or soup.body
        
        # First identify all section headers
        section_headers = []
        for h3 in content.find_all('h3'):
            h3_text = h3.get_text().strip()
            
            # Identify section headers by common text or icons
            if "TREASURES FROM GOD'S WORD" in h3_text or 'dc-icon--gem' in h3.get('class', []):
                section_headers.append(("TREASURES FROM GOD'S WORD", h3))
            elif "APPLY YOURSELF TO THE FIELD MINISTRY" in h3_text or 'dc-icon--wheat' in h3.get('class', []):
                section_headers.append(("APPLY YOURSELF TO THE FIELD MINISTRY", h3))
            elif "LIVING AS CHRISTIANS" in h3_text or 'dc-icon--users' in h3.get('class', []):
                section_headers.append(("LIVING AS CHRISTIANS", h3))
            elif "Song" in h3_text and "Prayer" in h3_text and 'dc-icon--music' in h3.get('class', []):
                # This is likely the opening - create an opening section
                if not sections:
                    opening_section = MeetingSection(title="Opening", parts=[])
                    
                    # Extract duration from text if present, default to 5 minutes
                    duration = self._extract_duration(h3_text) or 5
                    
                    opening_section.parts.append(
                        MeetingPart(title=h3_text, duration_minutes=duration)
                    )
                    sections.append(opening_section)
        
        # Process each section and collect parts
        for i, (section_title, section_header) in enumerate(section_headers):
            section = MeetingSection(title=section_title, parts=[])
            
            # Find the next section header or end of content
            next_header = section_headers[i+1][1] if i+1 < len(section_headers) else None
            
            # Get all elements between this section header and the next one
            current_elem = section_header.next_sibling
            
            # Skip any non-tag elements or empty elements
            while current_elem and (not isinstance(current_elem, Tag) or not current_elem.get_text().strip()):
                current_elem = current_elem.next_sibling
            
            # Process each paragraph in the section
            while current_elem and (next_header is None or current_elem != next_header):
                if isinstance(current_elem, Tag):
                    part_text = current_elem.get_text().strip()
                    
                    # Skip empty elements
                    if part_text:
                        # Try to identify part type and extract duration
                        if current_elem.name == 'p':
                            # Look for numbering pattern: "1. What Makes..."
                            part_match = re.match(r'(\d+)\.\s*(.*?)(?:\s*\((\d+)\s*min\.?\))?$', part_text)
                            if part_match:
                                num, title, duration_str = part_match.groups()
                                
                                # If duration is in the title, use it
                                if duration_str:
                                    duration = int(duration_str)
                                else:
                                    # Try to extract from text or use default
                                    duration = self._extract_duration(part_text)
                                    
                                    # If still no duration, use defaults based on part types
                                    if duration is None:
                                        if "Bible Reading" in title:
                                            duration = 4
                                        elif "Congregation Bible Study" in title:
                                            duration = 30
                                        elif any(keyword in title.lower() for keyword in ["demonstration", "video"]):
                                            duration = 5
                                        else:
                                            duration = 10  # Default duration
                                
                                # Create part
                                section.parts.append(
                                    MeetingPart(title=f"{num}. {title}", duration_minutes=duration)
                                )
                        
                        # Check for song entries
                        elif current_elem.name == 'h3' and ("Song" in part_text):
                            duration = self._extract_duration(part_text) or 3  # Default 3 minutes for songs
                            section.parts.append(
                                MeetingPart(title=part_text, duration_minutes=duration)
                            )
                
                # Move to next element
                current_elem = current_elem.next_sibling
            
            # Add section if it has parts
            if section.parts:
                sections.append(section)
        
        # Check for concluding section if not already included
        if sections and "LIVING AS CHRISTIANS" in sections[-1].title:
            # Check if Concluding Comments or Concluding Song is already included
            has_concluding = any("Concluding" in part.title for part in sections[-1].parts)
            
            if not has_concluding:
                # Hardcode the concluding parts at the end
                sections[-1].parts.append(
                    MeetingPart(title="Concluding Comments", duration_minutes=3)
                )
                sections[-1].parts.append(
                    MeetingPart(title="Concluding Song and Prayer", duration_minutes=5)
                )
        
        # If still empty (parsing failed), create a skeleton with default structure
        if not sections:
            sections = self._create_default_midweek_structure()
        
        return sections
    
    def _create_default_midweek_structure(self) -> List[MeetingSection]:
        """Create a default midweek meeting structure when parsing fails"""
        return [
            MeetingSection(
                title="Opening",
                parts=[
                    MeetingPart(title="Song and Prayer", duration_minutes=5),
                    MeetingPart(title="Opening Comments", duration_minutes=1)
                ]
            ),
            MeetingSection(
                title="TREASURES FROM GOD'S WORD",
                parts=[
                    MeetingPart(title="1. Main Talk", duration_minutes=10),
                    MeetingPart(title="2. Digging for Spiritual Gems", duration_minutes=10),
                    MeetingPart(title="3. Bible Reading", duration_minutes=4)
                ]
            ),
            MeetingSection(
                title="APPLY YOURSELF TO THE FIELD MINISTRY",
                parts=[
                    MeetingPart(title="4. First Return Visit", duration_minutes=5),
                    MeetingPart(title="5. Second Return Visit", duration_minutes=5),
                    MeetingPart(title="6. Bible Study", duration_minutes=5)
                ]
            ),
            MeetingSection(
                title="LIVING AS CHRISTIANS",
                parts=[
                    MeetingPart(title="7. First Part", duration_minutes=15),
                    MeetingPart(title="8. Congregation Bible Study", duration_minutes=30),
                    MeetingPart(title="9. Concluding Comments", duration_minutes=3),
                    MeetingPart(title="10. Concluding Song and Prayer", duration_minutes=5)
                ]
            )
        ]
    
    def _parse_weekend_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse weekend meeting structure"""
        # Look for Watchtower title
        watchtower_title = ""
        
        # Try to find Watchtower title in a strong tag
        for strong in soup.find_all('strong'):
            text = strong.get_text().strip()
            if len(text) > 10 and ("—" in text or "Jehovah" in text or "God" in text):
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
                if "Study Article" in text or "Watchtower Study" in text:
                    watchtower_title = text
                    break
        
        # Create default title if we still couldn't find one
        if not watchtower_title:
            watchtower_title = "Watchtower Study"
        
        # Try to find public talk title
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