"""
Tests for the web scraper that fetches meeting information.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import os

from src.utils.scraper import MeetingScraper
from src.models.meeting import Meeting, MeetingType


class TestMeetingScraper(unittest.TestCase):
    """Test cases for the MeetingScraper class"""
    
    def setUp(self):
        """Set up test environment"""
        self.scraper = MeetingScraper()
        
        # Load mock HTML responses for testing
        self.mock_dir = os.path.join(os.path.dirname(__file__), 'mock_data')
        os.makedirs(self.mock_dir, exist_ok=True)
        
        # Create path for mock HTML files
        self.meetings_html_path = os.path.join(self.mock_dir, 'meetings.html')
        self.midweek_html_path = os.path.join(self.mock_dir, 'midweek.html')
        self.weekend_html_path = os.path.join(self.mock_dir, 'weekend.html')
        
        # Create the files if they don't exist (with placeholder content)
        if not os.path.exists(self.meetings_html_path):
            with open(self.meetings_html_path, 'w', encoding='utf-8') as f:
                f.write(self._get_mock_meetings_html())
        
        if not os.path.exists(self.midweek_html_path):
            with open(self.midweek_html_path, 'w', encoding='utf-8') as f:
                f.write(self._get_mock_midweek_html())
        
        if not os.path.exists(self.weekend_html_path):
            with open(self.weekend_html_path, 'w', encoding='utf-8') as f:
                f.write(self._get_mock_weekend_html())
    
    def _get_mock_response(self, path):
        """Get mock response from file"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_mock_meetings_html(self):
        """Get mock HTML for meetings page based on actual structure shown in screenshots"""
        return """
        <html>
        <body>
            <!-- Main meetings page with both kinds of meetings -->
            <div class="todayItem">
                <div class="synopsis">
                    <a href="/en/wol/lf/r1/lp-e">
                        <span id="p1" class="pageNumber">APRIL 21-27</span>
                        Life and Ministry Meeting Workbook—2025 | April
                    </a>
                </div>
            </div>
            
            <div class="todayItem">
                <div class="synopsis">
                    <a href="/en/wol/d/r1/lp-e/2025291">
                        <span>Study Article 7: April 21-27, 2025</span>
                        <strong>Jehovah's Forgiveness—What It Means for You</strong>
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_mock_midweek_html(self):
        """Get mock HTML for midweek meeting page based on actual structure shown in screenshots"""
        return """
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
    
    def _get_mock_weekend_html(self):
        """Get mock HTML for weekend meeting page based on actual structure shown in screenshots"""
        return """
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
    
    @patch('requests.Session')
    def test_get_current_meeting_urls(self, mock_session):
        """Test getting current meeting URLs"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.meetings_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting_links = self.scraper.get_current_meeting_urls()
        
        # Check results
        self.assertIn(MeetingType.MIDWEEK, meeting_links)
        self.assertIn(MeetingType.WEEKEND, meeting_links)
        self.assertTrue("wol.jw.org" in meeting_links[MeetingType.MIDWEEK])
        self.assertTrue("wol.jw.org" in meeting_links[MeetingType.WEEKEND])
    
    @patch('requests.Session')
    def test_scrape_midweek_meeting(self, mock_session):
        """Test scraping midweek meeting"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.midweek_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting = self.scraper.scrape_meeting(
            "https://wol.jw.org/en/wol/lf/r1/lp-e", 
            MeetingType.MIDWEEK
        )
        
        # Check meeting properties
        self.assertEqual(meeting.meeting_type, MeetingType.MIDWEEK)
        self.assertTrue("APRIL 21-27" in meeting.title or "April 21-27" in meeting.title)
        
        # Check sections
        self.assertGreaterEqual(len(meeting.sections), 3)
        
        # Verify section titles
        section_titles = [s.title.upper() for s in meeting.sections]
        self.assertTrue(any("TREASURES" in t for t in section_titles))
        self.assertTrue(any("APPLY YOURSELF" in t for t in section_titles))
        self.assertTrue(any("CHRISTIANS" in t for t in section_titles))
        
        # Get Treasures section and check parts
        treasures_sections = [s for s in meeting.sections if "TREASURES" in s.title.upper()]
        self.assertTrue(len(treasures_sections) > 0)
        
        treasures_section = treasures_sections[0]
        part_titles = [p.title for p in treasures_section.parts]
        part_durations = [p.duration_minutes for p in treasures_section.parts]
        
        # Check for Bible Reading part with 4 minutes
        has_bible_reading = False
        for i, title in enumerate(part_titles):
            if "Bible Reading" in title:
                has_bible_reading = True
                self.assertEqual(part_durations[i], 4)
                break
        self.assertTrue(has_bible_reading)
        
        # Check for reasonable total duration (45+ minutes)
        self.assertGreaterEqual(meeting.total_duration_minutes, 45)
    
    @patch('requests.Session')
    def test_scrape_weekend_meeting(self, mock_session):
        """Test scraping weekend meeting"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.weekend_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting = self.scraper.scrape_meeting(
            "https://wol.jw.org/en/wol/d/r1/lp-e/2025291", 
            MeetingType.WEEKEND
        )
        
        # Check meeting properties
        self.assertEqual(meeting.meeting_type, MeetingType.WEEKEND)
        self.assertTrue("APRIL 21-27" in meeting.title or "April 21-27" in meeting.title)
        
        # Check sections
        self.assertEqual(len(meeting.sections), 2)
        
        # Verify section titles
        self.assertEqual(meeting.sections[0].title, "Public Talk")
        self.assertEqual(meeting.sections[1].title, "Watchtower Study")
        
        # Check parts in Watchtower section
        watchtower_section = meeting.sections[1]
        watchtower_parts = watchtower_section.parts
        
        # Find the main Watchtower study part
        main_part = None
        for part in watchtower_parts:
            if "Forgiveness" in part.title:
                main_part = part
                break
        
        # Verify the main part exists and has correct duration
        self.assertIsNotNone(main_part)
        self.assertEqual(main_part.duration_minutes, 60)
        
        # Check total duration is at least 90 minutes
        self.assertGreaterEqual(meeting.total_duration_minutes, 90)
    
    @patch('requests.Session')
    def test_update_meetings(self, mock_session):
        """Test updating all meetings"""
        # Create url maps for the side effect
        url_map = {
            "https://wol.jw.org/en/wol/meetings/r1/lp-e": self._get_mock_response(self.meetings_html_path),
            "https://wol.jw.org/en/wol/lf/r1/lp-e": self._get_mock_response(self.midweek_html_path), 
            "https://wol.jw.org/en/wol/d/r1/lp-e/2025291": self._get_mock_response(self.weekend_html_path)
        }
        
        # Setup a side effect function to return different responses based on URL
        def mock_get(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            # Find the closest match
            matched_key = None
            for key in url_map:
                if key in url:
                    matched_key = key
                    break
            
            if matched_key:
                mock_response.text = url_map[matched_key]
            else:
                # Default fallback
                mock_response.text = ""
                mock_response.status_code = 404
            
            return mock_response
        
        # Configure the mock
        mock_session.return_value.get.side_effect = mock_get
        
        # Call the method
        meetings = self.scraper.update_meetings()
        
        # Check results
        self.assertIn(MeetingType.MIDWEEK, meetings)
        self.assertIn(MeetingType.WEEKEND, meetings)
        
        # Check midweek meeting
        midweek = meetings[MeetingType.MIDWEEK]
        self.assertTrue("APRIL 21-27" in midweek.title or "April 21-27" in midweek.title)
        self.assertGreaterEqual(len(midweek.sections), 3)
        
        # Check for Bible Reading part with correct duration
        bible_reading_found = False
        for section in midweek.sections:
            for part in section.parts:
                if "Bible Reading" in part.title:
                    bible_reading_found = True
                    self.assertEqual(part.duration_minutes, 4)
                    break
            if bible_reading_found:
                break
        
        self.assertTrue(bible_reading_found, "Bible Reading part not found")
        
        # Check weekend meeting
        weekend = meetings[MeetingType.WEEKEND]
        self.assertTrue("APRIL 21-27" in weekend.title or "April 21-27" in weekend.title)
        self.assertEqual(len(weekend.sections), 2)
        
        # Check for Watchtower part with correct title and duration
        watchtower_part_found = False
        for section in weekend.sections:
            if "Watchtower" in section.title:
                for part in section.parts:
                    if "Forgiveness" in part.title:
                        watchtower_part_found = True
                        self.assertEqual(part.duration_minutes, 60)
                        break
            if watchtower_part_found:
                break
        
        self.assertTrue(watchtower_part_found, "Watchtower part not found")
    
    @patch('requests.Session')
    def test_error_handling(self, mock_session):
        """Test error handling for failed requests"""
        # Setup mock response for a failed request
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.return_value.get.return_value = mock_response
        
        # Test for get_current_meeting_urls
        with self.assertRaises(Exception) as context:
            self.scraper.get_current_meeting_urls()
        
        self.assertIn("Failed to fetch meetings page", str(context.exception))
    
    @patch('requests.Session')
    def test_midweek_parts_details(self, mock_session):
        """Test that all midweek meeting parts are correctly extracted with durations"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.midweek_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting = self.scraper.scrape_meeting(
            "https://wol.jw.org/en/wol/lf/r1/lp-e", 
            MeetingType.MIDWEEK
        )
        
        # Count total parts
        total_parts = sum(len(section.parts) for section in meeting.sections)
        
        # Check that we have a reasonable number of parts (at least 8)
        self.assertGreaterEqual(total_parts, 8, f"Only found {total_parts} parts")
        
        # Check for specific parts
        expected_parts = {
            "Bible Reading": 4,
            "Congregation Bible Study": 30,
            "Concluding Comments": 3
        }
        
        found_parts = {}
        
        for section in meeting.sections:
            for part in section.parts:
                for expected_part, expected_duration in expected_parts.items():
                    if expected_part in part.title and expected_part not in found_parts:
                        found_parts[expected_part] = part.duration_minutes
        
        # Check that we found all expected parts with correct durations
        for part_name, expected_duration in expected_parts.items():
            self.assertIn(part_name, found_parts, f"Part '{part_name}' not found")
            self.assertEqual(found_parts[part_name], expected_duration, 
                            f"Part '{part_name}' has duration {found_parts[part_name]}, expected {expected_duration}")
    
    def test_language_setting(self):
        """Test setting different languages"""
        # Create scraper with Spanish language
        es_scraper = MeetingScraper(language="es")
        
        # Check URL has the correct language code
        self.assertEqual(es_scraper.language, "es")
        self.assertTrue("/es/" in es_scraper.meetings_url)


if __name__ == '__main__':
    unittest.main()