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
    
    def _extract_duration_and_title(self, element) -> Tuple[int, str]:
        """Extract duration in minutes and title from an element"""
        text = element.get_text().strip()
        
        # Look for patterns like "(10 min.)" or "(10 min)"
        duration_match = re.search(r'\((\d+)\s*min', text)
        if duration_match:
            # Extract the duration in minutes
            return int(duration_match.group(1))
        
        return None
    
    def _parse_midweek_meeting(self, soup: BeautifulSoup) -> List[MeetingSection]:
        """
        Parse midweek meeting using h3>strong numbering and song icons.
        """
        sections_data = {
            "Opening": MeetingSection(title="Opening", parts=[]),
            "Treasures": MeetingSection(title="TREASURES FROM GOD'S WORD", parts=[]),
            "Ministry": MeetingSection(title="APPLY YOURSELF TO THE FIELD MINISTRY", parts=[]),
            "Christians": MeetingSection(title="LIVING AS CHRISTIANS", parts=[])
        }
        ordered_sections = []
        current_section_key = None
        song_count = 0

        # Find the main content container if possible (adjust selector if needed)
        # Using 'body' as a fallback if a specific container isn't obvious
        content_area = soup.find('div', class_='bodyTxt') or soup.body

        # Iterate through direct children or relevant tags within the content area
        # We look for h3 tags (for sections, parts, songs) and p tags (for durations)
        for element in content_area.find_all(['h3', 'p'], recursive=False): # recursive=False might be too strict, adjust if needed

            if element.name == 'h3':
                # Check for Section Headers (using icons as primary identifier)
                if element.select_one("span:contains('TREASURES FROM GOD')") or 'dc-icon--gem' in element.get('class', []):
                    current_section_key = "Treasures"
                    if sections_data[current_section_key] not in ordered_sections:
                         ordered_sections.append(sections_data[current_section_key])
                    continue # Move to next element after identifying header
                elif element.select_one("span:contains('APPLY YOURSELF')") or 'dc-icon--wheat' in element.get('class', []):
                    current_section_key = "Ministry"
                    if sections_data[current_section_key] not in ordered_sections:
                         ordered_sections.append(sections_data[current_section_key])
                    continue
                elif element.select_one("span:contains('LIVING AS CHRISTIANS')") or 'dc-icon--users' in element.get('class', []):
                    current_section_key = "Christians"
                    if sections_data[current_section_key] not in ordered_sections:
                         ordered_sections.append(sections_data[current_section_key])
                    continue

                # Check for Songs (using music icon)
                if 'dc-icon--music' in element.get('class', []):
                    song_count += 1
                    duration, title = self._extract_duration_and_title(element) # Use your existing helper
                    part = MeetingPart(title=title, duration_minutes=duration)

                    if song_count == 1: # Opening Song
                        # Add to Opening section
                        if sections_data["Opening"] not in ordered_sections:
                            ordered_sections.insert(0, sections_data["Opening"])
                        sections_data["Opening"].parts.append(part)
                    elif song_count == 2: # Middle Song (Assume it starts Christians section)
                        current_section_key = "Christians" # Ensure we are in Christians section
                        if sections_data[current_section_key] not in ordered_sections:
                            ordered_sections.append(sections_data[current_section_key])
                        sections_data[current_section_key].parts.append(part)
                    else: # Concluding Song (Assume it's part of Christians)
                        # It might be preceded by concluding comments, handle later if needed
                         if sections_data["Christians"] not in ordered_sections:
                             ordered_sections.append(sections_data["Christians"])
                         sections_data["Christians"].parts.append(part)
                    continue # Move to next element after processing song

                # Check for Numbered Parts (h3 > strong starting with digit.)
                strong_tag = element.find('strong', recursive=False)
                if strong_tag and strong_tag.get_text(strip=True).startswith(tuple(f"{i}." for i in range(1, 15))): # Check for "1.", "2.", etc.
                    part_title = element.get_text(strip=True)
                    part_duration = 0 # Default duration

                    # Find duration in the *next* sibling 'p' tag
                    next_sibling = element.find_next_sibling()
                    while next_sibling:
                        if next_sibling.name == 'p':
                            duration = self._extract_duration_from_text(next_sibling.get_text())
                            if duration is not None:
                                part_duration = duration
                                break # Found duration
                        # Stop searching if we hit another h3, assuming it's the next part/section
                        if next_sibling.name == 'h3':
                             break
                        next_sibling = next_sibling.find_next_sibling()

                    # Add the part to the current section if identified
                    if current_section_key:
                        if sections_data[current_section_key] not in ordered_sections:
                             ordered_sections.append(sections_data[current_section_key]) # Ensure section is added if it wasn't already
                        sections_data[current_section_key].parts.append(
                            MeetingPart(title=part_title, duration_minutes=part_duration)
                        )
                    else:
                        print(f"Warning: Found numbered part '{part_title}' but no current section context.")

                # Handle specific non-numbered parts like 'Concluding Comments' if needed
                elif "Concluding Comments" in element.get_text():
                     # Assume 3 mins default or extract if pattern exists
                     duration, title = self._extract_duration_and_title(element)
                     if current_section_key == "Christians":
                          sections_data[current_section_key].parts.append(
                               MeetingPart(title=title, duration_minutes=duration)
                          )


        # Filter out sections that ended up empty
        final_sections = [sec for sec in ordered_sections if sec.parts]
        
        return final_sections
    
    def _extract_duration_and_title(self, element: Tag) -> Tuple[int, str]:
        """Extract duration in minutes and title from an element (Keep your existing refined version)"""
        text = element.get_text(strip=True)
        duration = 5 # Default fallback
        title = text

        # Look for patterns like "(10 min.)" or "(10 min)"
        duration_match = re.search(r'\((\d+)\s*min', text)
        if duration_match:
            duration = int(duration_match.group(1))
            # Remove the duration part from the title
            title = re.sub(r'\(\d+\s*min\.*\)\s*$', '', text, flags=re.IGNORECASE).strip()
        else:
            # Handle defaults based on keywords more robustly
            lower_text = text.lower()
            if "song" in lower_text and "prayer" in lower_text:
                duration = 5 # Opening/Concluding songs often grouped with prayer
            elif "song" in lower_text:
                 duration = 3 # Midweek songs often ~3 mins
            elif "opening comments" in lower_text:
                 duration = 1
            elif "bible reading" in lower_text:
                 duration = 4
            elif "concluding comments" in lower_text:
                 duration = 3
            elif "spiritual gems" in lower_text or "digging for spiritual gems" in lower_text:
                 duration = 10
            elif "congregation bible study" in lower_text:
                 duration = 30
            # Add more specific keyword checks if needed for Ministry parts

        # Clean up title (remove potential numbering if captured accidentally, etc.)
        title = re.sub(r'^\d+\.\s*', '', title).strip() # Remove leading "1. " etc.

        return duration, title
    
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