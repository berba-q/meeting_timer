"""
Tests for the EPUB scraper's date matching logic in update_meetings_cache.

Verifies the fix for a bug where weekend meetings were not found because the
`contains_current_studies` check used inverted date math. The heading date
(from _extract_heading_date) is the START of the study week, so the correct
check is: week_start <= today <= week_start + 6 days.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.epub_scraper import EPUBMeetingScraper
from src.models.meeting import MeetingType


def _run_fixed_contains_current_studies_check(today, weekend_meeting_dates):
    """
    Replicate the FIXED logic from update_meetings_cache().
    _extract_heading_date returns the START of the study week,
    so week_end = week_start + 6 days.
    """
    contains_current_studies = False
    for meeting_date_str in weekend_meeting_dates:
        week_start = datetime.strptime(meeting_date_str, '%Y-%m-%d')
        week_end = week_start + timedelta(days=6)
        if week_start <= today <= week_end:
            contains_current_studies = True
            break
    return contains_current_studies


class TestMarch1WeekendMeeting(unittest.TestCase):
    """
    Scenario: March 1, 2026 (Sunday). The Watchtower EPUB w_E_202512 contains
    Study Article 51 for "February 23 - March 1, 2026".
    _extract_heading_date returns "2026-02-23" (the start of the range).
    """

    # The w_E_202512 EPUB contains these study week start dates:
    EPUB_DATES = ["2026-02-02", "2026-02-09", "2026-02-16", "2026-02-23"]

    def test_sunday_march_1_finds_weekend_meeting(self):
        """Sunday March 1 falls in the Feb 23 - Mar 1 study week."""
        today = datetime(2026, 3, 1)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 1 (Sunday) should match the Feb 23 - Mar 1 study week")

    def test_saturday_feb_28_finds_weekend_meeting(self):
        """Saturday Feb 28 also falls in the Feb 23 - Mar 1 study week."""
        today = datetime(2026, 2, 28)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "Feb 28 (Saturday) should match the Feb 23 - Mar 1 study week")

    def test_monday_feb_23_finds_weekend_meeting(self):
        """Monday Feb 23 is the start of the study week - boundary check."""
        today = datetime(2026, 2, 23)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "Feb 23 (Monday, week start) should match the Feb 23 - Mar 1 study week")

    def test_march_2_does_not_match_feb_23_week(self):
        """March 2 is the start of a new week - should NOT match Feb 23 - Mar 1."""
        today = datetime(2026, 3, 2)
        self.assertFalse(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 2 should NOT match any week in the Dec 2025 Watchtower")

    def test_midweek_lookup_march_1_works(self):
        """Midweek meeting lookup for March 1 should find the Feb 23 week."""
        scraper = EPUBMeetingScraper("en")
        meetings_data = {
            'midweek': {
                '202601': {
                    '2026-02-23': [
                        {'title': 'Song 100', 'duration_minutes': 5, 'section': 'treasures', 'type': 'song'},
                        {'title': 'Opening Comments', 'duration_minutes': 1, 'section': 'treasures', 'type': 'comments'},
                    ]
                }
            }
        }
        with patch.object(scraper, '_load_cached_meetings', return_value=meetings_data):
            meeting = scraper.get_meeting_by_date_range('2026-03-01', MeetingType.MIDWEEK)
            self.assertIsNotNone(meeting,
                "Midweek meeting for Feb 23 week should be found when querying March 1")

    def test_weekend_lookup_march_1_works_if_cached(self):
        """Weekend lookup works correctly once data is in the cache."""
        scraper = EPUBMeetingScraper("en")
        meetings_data = {
            'weekend': {
                '202512': {
                    '2026-02-23': [
                        {'title': 'OPENING_SONG_PRAYER', 'duration_minutes': 5, 'section': 'public_talk', 'type': 'song'},
                        {'title': 'Public Talk', 'duration_minutes': 30, 'section': 'public_talk', 'type': 'talk'},
                    ]
                }
            }
        }
        with patch.object(scraper, '_load_cached_meetings', return_value=meetings_data):
            meeting = scraper.get_meeting_by_date_range('2026-03-01', MeetingType.WEEKEND)
            self.assertIsNotNone(meeting,
                "Weekend meeting for Feb 23 week should be found when querying March 1")


class TestMarch2WeekWeekendMeeting(unittest.TestCase):
    """
    Scenario: Week starting March 2, 2026 (Monday). The next weekend is
    March 7 (Saturday) / March 8 (Sunday). The Watchtower study has heading
    "March 2-8, 2026", so _extract_heading_date returns "2026-03-02".
    """

    EPUB_DATES = ["2026-03-02"]

    def test_monday_march_2_finds_meeting(self):
        """Monday March 2 is the start of the study week."""
        today = datetime(2026, 3, 2)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 2 (Monday, week start) should match the Mar 2-8 study week")

    def test_saturday_march_7_finds_meeting(self):
        """Saturday March 7 - the typical weekend meeting day."""
        today = datetime(2026, 3, 7)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 7 (Saturday) should match the Mar 2-8 study week")

    def test_sunday_march_8_finds_meeting(self):
        """Sunday March 8 - end of the study week."""
        today = datetime(2026, 3, 8)
        self.assertTrue(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 8 (Sunday) should match the Mar 2-8 study week")

    def test_march_9_does_not_match(self):
        """March 9 is the next week - should NOT match Mar 2-8."""
        today = datetime(2026, 3, 9)
        self.assertFalse(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 9 should NOT match the Mar 2-8 study week")

    def test_march_1_does_not_match(self):
        """March 1 is the previous week - should NOT match Mar 2-8."""
        today = datetime(2026, 3, 1)
        self.assertFalse(
            _run_fixed_contains_current_studies_check(today, self.EPUB_DATES),
            "March 1 should NOT match the Mar 2-8 study week")

    def test_weekend_lookup_march_7_works_if_cached(self):
        """Weekend lookup for March 7 finds the Mar 2-8 meeting."""
        scraper = EPUBMeetingScraper("en")
        meetings_data = {
            'weekend': {
                '202601': {
                    '2026-03-02': [
                        {'title': 'OPENING_SONG_PRAYER', 'duration_minutes': 5, 'section': 'public_talk', 'type': 'song'},
                        {'title': 'Public Talk', 'duration_minutes': 30, 'section': 'public_talk', 'type': 'talk'},
                    ]
                }
            }
        }
        with patch.object(scraper, '_load_cached_meetings', return_value=meetings_data):
            meeting = scraper.get_meeting_by_date_range('2026-03-07', MeetingType.WEEKEND)
            self.assertIsNotNone(meeting,
                "Weekend meeting for Mar 2-8 should be found when querying March 7")

    def test_weekend_lookup_march_8_works_if_cached(self):
        """Weekend lookup for March 8 finds the Mar 2-8 meeting."""
        scraper = EPUBMeetingScraper("en")
        meetings_data = {
            'weekend': {
                '202601': {
                    '2026-03-02': [
                        {'title': 'OPENING_SONG_PRAYER', 'duration_minutes': 5, 'section': 'public_talk', 'type': 'song'},
                        {'title': 'Public Talk', 'duration_minutes': 30, 'section': 'public_talk', 'type': 'talk'},
                    ]
                }
            }
        }
        with patch.object(scraper, '_load_cached_meetings', return_value=meetings_data):
            meeting = scraper.get_meeting_by_date_range('2026-03-08', MeetingType.WEEKEND)
            self.assertIsNotNone(meeting,
                "Weekend meeting for Mar 2-8 should be found when querying March 8")


if __name__ == '__main__':
    unittest.main()
