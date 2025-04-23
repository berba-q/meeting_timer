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
            with open(self.meetings_html_path, 'w') as f:
                f.write(self._get_mock_meetings_html())
        
        if not os.path.exists(self.midweek_html_path):
            with open(self.midweek_html_path, 'w') as f:
                f.write(self._get_mock_midweek_html())
        
        if not os.path.exists(self.weekend_html_path):
            with open(self.weekend_html_path, 'w') as f:
                f.write(self._get_mock_weekend_html())
    
    def _get_mock_response(self, path):
        """Get mock response from file"""
        with open(path, 'r') as f:
            return f.read()
    
    def _get_mock_meetings_html(self):
        """Get mock HTML for meetings page"""
        return """
        <html>
        <body>
            <div class="meetingItems">
                <ul>
                    <li><a href="/en/wol/dt/r1/lp-e/2023/4/21">Treasures From God's Word</a></li>
                    <li><a href="/en/wol/dt/r1/lp-e/2023/4/23">Watchtower Study</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
    
    def _get_mock_midweek_html(self):
        """Get mock HTML for midweek meeting page"""
        return """
        <html>
        <body>
            <header>
                <h1>Midweek Meeting: April 21-27, 2023</h1>
            </header>
            <div class="pubDate">April 21-27, 2023</div>
            
            <div class="section">
                <h2>Treasures From God's Word</h2>
                <div class="bodyTxt">
                    <h3>Opening Comments</h3>
                    <span>3 min</span>
                </div>
                <div class="bodyTxt">
                    <h3>Spiritual Gems</h3>
                    <span>10 min</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Apply Yourself to the Field Ministry</h2>
                <div class="bodyTxt">
                    <strong>Initial Call</strong>
                    <span>4 min</span>
                </div>
                <div class="bodyTxt">
                    <strong>Return Visit</strong>
                    <span>4 min</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Living as Christians</h2>
                <div class="bodyTxt">
                    <strong>Congregation Bible Study</strong>
                    <span>30 min</span>
                </div>
                <div class="bodyTxt">
                    <strong>Concluding Comments</strong>
                    <span>3 min</span>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_mock_weekend_html(self):
        """Get mock HTML for weekend meeting page"""
        return """
        <html>
        <body>
            <header>
                <h1>Weekend Meeting: April 23, 2023</h1>
            </header>
            <div class="pubDate">April 23, 2023</div>
            
            <div class="section">
                <h2>Public Talk</h2>
                <div class="bodyTxt">
                    <strong>How to Build a Happy Family</strong>
                    <span>30 min</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Watchtower Study</h2>
                <div class="bodyTxt">
                    <strong>Remain "Steadfast as Seeing the One Who Is Invisible"</strong>
                    <span>60 min</span>
                </div>
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
        meeting_urls = self.scraper.get_current_meeting_urls()
        
        # Check results
        self.assertIn(MeetingType.MIDWEEK, meeting_urls)
        self.assertIn(MeetingType.WEEKEND, meeting_urls)
        self.assertTrue(meeting_urls[MeetingType.MIDWEEK].endswith('/2023/4/21'))
        self.assertTrue(meeting_urls[MeetingType.WEEKEND].endswith('/2023/4/23'))
    
    @patch('requests.Session')
    def test_scrape_midweek_meeting(self, mock_session):
        """Test scraping midweek meeting"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.midweek_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting = self.scraper.scrape_meeting("http://example.com/midweek", MeetingType.MIDWEEK)
        
        # Check meeting properties
        self.assertEqual(meeting.meeting_type, MeetingType.MIDWEEK)
        self.assertEqual(meeting.title, "Midweek Meeting: April 21-27, 2023")
        self.assertEqual(meeting.language, "en")
        
        # Check sections and parts
        self.assertEqual(len(meeting.sections), 3)
        self.assertEqual(meeting.sections[0].title, "Treasures From God's Word")
        self.assertEqual(meeting.sections[1].title, "Apply Yourself to the Field Ministry")
        self.assertEqual(meeting.sections[2].title, "Living as Christians")
        
        # Check parts in first section
        self.assertEqual(len(meeting.sections[0].parts), 2)
        self.assertEqual(meeting.sections[0].parts[0].title, "Opening Comments")
        self.assertEqual(meeting.sections[0].parts[0].duration_minutes, 3)
        self.assertEqual(meeting.sections[0].parts[1].title, "Spiritual Gems")
        self.assertEqual(meeting.sections[0].parts[1].duration_minutes, 10)
        
        # Check total duration
        self.assertEqual(meeting.total_duration_minutes, 54)  # 3+10+4+4+30+3 = 54
    
    @patch('requests.Session')
    def test_scrape_weekend_meeting(self, mock_session):
        """Test scraping weekend meeting"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self._get_mock_response(self.weekend_html_path)
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method
        meeting = self.scraper.scrape_meeting("https://wol.jw.org/en/wol/meetings/", MeetingType.WEEKEND)
        
        # Check meeting properties
        self.assertEqual(meeting.meeting_type, MeetingType.WEEKEND)
        self.assertEqual(meeting.title, "Weekend Meeting: April 26, 2025")
        
        # Check sections and parts
        self.assertEqual(len(meeting.sections), 2)
        self.assertEqual(meeting.sections[0].title, "Public Talk")
        self.assertEqual(meeting.sections[1].title, "Watchtower Study")
        
        # Check parts in sections
        self.assertEqual(len(meeting.sections[0].parts), 1)
        self.assertEqual(meeting.sections[0].parts[0].title, "How to Build a Happy Family")
        self.assertEqual(meeting.sections[0].parts[0].duration_minutes, 30)
        
        self.assertEqual(len(meeting.sections[1].parts), 1)
        self.assertEqual(meeting.sections[1].parts[0].title, " Jehovah’s Forgiveness​—What It Means for You")
        self.assertEqual(meeting.sections[1].parts[0].duration_minutes, 60)
        
        # Check total duration
        self.assertEqual(meeting.total_duration_minutes, 90)  # 30+60 = 90
    
    @patch('requests.Session')
    def test_update_meetings(self, mock_session):
        """Test updating all meetings"""
        # Setup mock responses for each request
        def mock_get(url):
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if url == self.scraper.meetings_url:
                mock_response.text = self._get_mock_response(self.meetings_html_path)
            elif "/2025/4/21" in url:
                mock_response.text = self._get_mock_response(self.midweek_html_path)
            elif "/2025/4/27" in url:
                mock_response.text = self._get_mock_response(self.weekend_html_path)
            
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
        self.assertEqual(midweek.title, "Midweek Meeting: April 21-27, 2025")
        self.assertEqual(len(midweek.sections), 3)
        
        # Check weekend meeting
        weekend = meetings[MeetingType.WEEKEND]
        self.assertEqual(weekend.title, "Weekend Meeting: April 26, 2025")
        self.assertEqual(len(weekend.sections), 2)
    
    @patch('requests.Session')
    def test_error_handling(self, mock_session):
        """Test error handling for failed requests"""
        # Setup mock response for a failed request
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.return_value.get.return_value = mock_response
        
        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.scraper.get_current_meeting_urls()
    
    def test_language_setting(self):
        """Test setting different languages"""
        # Create scraper with Spanish language
        es_scraper = MeetingScraper(language="en")
        
        # Check URL has the correct language code
        self.assertEqual(es_scraper.language, "en")
        self.assertTrue("/en/" in es_scraper.meetings_url)


if __name__ == '__main__':
    unittest.main()