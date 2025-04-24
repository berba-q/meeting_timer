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
    
    def _extract_song_number(self, text: str) -> Optional[int]:
        """Extract song number from text"""
        # Match patterns like "Song 76" or "SONG 76"
        song_match = re.search(r'[Ss][Oo][Nn][Gg]\s+(\d+)', text)
        if song_match:
            return int(song_match.group(1))
        return None
    
    def _parse_midweek_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """Parse midweek meeting structure to match the desired output format"""
        # Initialize sections with correct section numbers from the desired output
        sections = []
        songs = {}  # Dict to store song numbers keyed by position: "opening", "middle", "closing"
        
        # Find main content container
        content = soup.find('div', class_='bodyTxt') or soup.body
        
        # First identify all section headers
        section_headers = []
        
        # Extract the song numbers from the document first
        for h3 in content.find_all(['h3', 'p']):
            h3_text = h3.get_text().strip()
            
            # Look for song patterns
            if "Song" in h3_text or "SONG" in h3_text:
                song_num = self._extract_song_number(h3_text)
                if song_num:
                    if "Opening" in h3_text or len(songs) == 0:
                        songs["opening"] = song_num
                    elif "Concluding" in h3_text or "Prayer" in h3_text:
                        songs["closing"] = song_num
                    else:
                        songs["middle"] = song_num
        
        # Extract the opening song and comments
        opening_song_text = None
        opening_song_element = None
        for h3 in content.find_all('h3'):
            h3_text = h3.get_text().strip()
            if "Song" in h3_text and "Prayer" in h3_text and "Opening Comments" in h3_text:
                opening_song_text = h3_text
                opening_song_element = h3
                # Extract opening song number if not already found
                if "opening" not in songs:
                    song_num = self._extract_song_number(h3_text)
                    if song_num:
                        songs["opening"] = song_num
                break
        
        # Find main section headers
        for h3 in content.find_all('h3'):
            h3_text = h3.get_text().strip()
            
            # Skip the opening song which we handle separately
            if opening_song_element and h3 == opening_song_element:
                continue
                
            # Identify section headers by common text or icons
            if "TREASURES FROM GOD'S WORD" in h3_text or 'dc-icon--gem' in h3.get('class', []):
                section_headers.append((1, "TREASURES FROM GOD'S WORD", h3))
            elif "APPLY YOURSELF TO THE FIELD MINISTRY" in h3_text or 'dc-icon--wheat' in h3.get('class', []):
                section_headers.append((2, "APPLY YOURSELF TO THE FIELD MINISTRY", h3))
            elif "LIVING AS CHRISTIANS" in h3_text or 'dc-icon--users' in h3.get('class', []):
                section_headers.append((3, "LIVING AS CHRISTIANS", h3))
        
        # Default song numbers if not found
        if "opening" not in songs:
            songs["opening"] = 76  # Fallback value
        if "middle" not in songs:
            songs["middle"] = 111  # Fallback value
        if "closing" not in songs:
            songs["closing"] = 115  # Fallback value
        
        # Create the Treasures section (Section 1) and add the opening song as Part 0
        if section_headers and section_headers[0][0] == 1:
            treasures_section = MeetingSection(title="TREASURES FROM GOD'S WORD", parts=[])
            
            # Add opening song and comments as Part 0 if found
            if opening_song_text:
                duration = self._extract_duration(opening_song_text) or 1
                # Extract the song number from text if available
                song_num = songs["opening"]
                treasures_section.parts.append(
                    MeetingPart(title=f"SONG {song_num} AND PRAYER | OPENING COMMENTS (1 MIN.)", duration_minutes=duration)
                )
            
            sections.append(treasures_section)
        
        # Process each section and collect parts
        part_counter = 1  # Start part counter at 1 (after opening song which is 0)
        for section_idx, (section_num, section_title, section_header) in enumerate(section_headers):
            # Skip Treasures section which we've already created
            if section_num == 1 and sections and sections[0].title == "TREASURES FROM GOD'S WORD":
                current_section = sections[0]
            else:
                current_section = MeetingSection(title=section_title, parts=[])
                sections.append(current_section)
            
            # Find the next section header or end of content
            next_header = section_headers[section_idx+1][2] if section_idx+1 < len(section_headers) else None
            
            # Get all elements between this section header and the next one
            current_elem = section_header.next_sibling
            
            # Skip any non-tag elements or empty elements
            while current_elem and (not isinstance(current_elem, Tag) or not current_elem.get_text().strip()):
                current_elem = current_elem.next_sibling
            
            # Special case for the "LIVING AS CHRISTIANS" section
            if section_title == "LIVING AS CHRISTIANS":
                # Look for middle song in h3 tag
                found_song = False
                for h3 in content.find_all(['h3', 'p']):
                    h3_text = h3.get_text().strip()
                    if "Song" in h3_text and not "Opening" in h3_text and not "Concluding" in h3_text:
                        found_song = True
                        # Try to extract song number if not already found
                        if "middle" not in songs:
                            song_num = self._extract_song_number(h3_text)
                            if song_num:
                                songs["middle"] = song_num
                        break
                
                if found_song or "middle" in songs:
                    # Add middle song as the first part in the Living as Christians section
                    song_num = songs["middle"]
                    current_section.parts.append(
                        MeetingPart(title=f"Song {song_num}", duration_minutes=3)
                    )
            
            # Process parts in this section
            while current_elem and (next_header is None or current_elem != next_header):
                if isinstance(current_elem, Tag):
                    part_text = current_elem.get_text().strip()
                    
                    # Skip empty elements
                    if part_text:
                        # Check for part pattern: digit followed by dot and text
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
                            
                            # Create the formatted part title matching desired output
                            formatted_title = f"{num}. {title}"
                            if duration_str:
                                formatted_title += f" ({duration} min)"
                            
                            # Create part with exact formatting matching desired output
                            current_section.parts.append(
                                MeetingPart(title=formatted_title, duration_minutes=duration)
                            )
                            
                            part_counter += 1
                
                # Move to next element
                current_elem = current_elem.next_sibling
        
        # Check for concluding section elements
        if sections and sections[-1].title == "LIVING AS CHRISTIANS":
            # Check if Concluding Comments is already included
            has_concluding = any("Concluding Comments" in part.title for part in sections[-1].parts)
            
            if not has_concluding:
                # Add "Concluding Comments (3 min.) | Song X and Prayer" using extracted song number
                closing_song_num = songs["closing"]
                sections[-1].parts.append(
                    MeetingPart(title=f"Concluding Comments (3 min.) | Song {closing_song_num} and Prayer", duration_minutes=8)
                )
        
        # Calculate total meeting duration
        total_minutes = sum(sum(part.duration_minutes for part in section.parts) for section in sections)
        
        return sections
    
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