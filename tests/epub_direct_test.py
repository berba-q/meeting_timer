import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import shutil
from pathlib import Path
import time
import logging
from typing import Dict, List, Tuple
import json

# Add the parent directory to sys.path so we can import modules from there
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from src.utils.epub_scraper import EPUBMeetingScraper
from src.models.meeting import MeetingType, Meeting

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EPUBScraperTester:
    """Comprehensive tester for EPUB scraper with metrics and timing"""
    
    def __init__(self):
        self.results = {}
        self.timing_data = {}
        
    def clear_cache(self):
        """Clear the entire cache directory"""
        try:
            from platformdirs import user_cache_dir
        except ImportError:
            cache_dir = Path.home() / ".meeting_timer_cache"
        else:
            cache_dir = Path(user_cache_dir("MeetingTimer"))
        
        if cache_dir.exists():
            print(f"🗑️  Clearing cache directory: {cache_dir}")
            shutil.rmtree(cache_dir)
            print("✅ Cache cleared successfully!")
        else:
            print("ℹ️  Cache directory doesn't exist - no need to clear")

    def time_operation(self, operation_name: str, func, *args, **kwargs):
        """Time an operation and store the result"""
        print(f"⏱️  Starting: {operation_name}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed = end_time - start_time
            
            self.timing_data[operation_name] = {
                'duration': elapsed,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Completed: {operation_name} in {elapsed:.2f}s")
            return result
            
        except Exception as e:
            end_time = time.time()
            elapsed = end_time - start_time
            
            self.timing_data[operation_name] = {
                'duration': elapsed,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"❌ Failed: {operation_name} in {elapsed:.2f}s - {str(e)}")
            raise

    def validate_meeting_structure(self, meeting: Meeting, meeting_type: MeetingType) -> Dict:
        """Validate meeting structure and return metrics"""
        validation = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }
        
        # Basic structure validation
        if not meeting.sections:
            validation['valid'] = False
            validation['issues'].append("No sections found")
            return validation
        
        total_parts = sum(len(section.parts) for section in meeting.sections)
        total_duration = meeting.total_duration_minutes
        
        validation['metrics'] = {
            'total_sections': len(meeting.sections),
            'total_parts': total_parts,
            'total_duration': total_duration,
            'sections': []
        }
        
        # Validate each section
        for i, section in enumerate(meeting.sections):
            section_info = {
                'name': section.title,
                'parts_count': len(section.parts),
                'duration': section.total_duration_minutes,
                'parts': []
            }
            
            if not section.parts:
                validation['issues'].append(f"Section '{section.title}' has no parts")
            
            # Validate parts
            for part in section.parts:
                part_info = {
                    'title': part.title,
                    'duration': part.duration_minutes
                }
                
                if part.duration_minutes <= 0:
                    validation['issues'].append(f"Part '{part.title}' has invalid duration: {part.duration_minutes}")
                    validation['valid'] = False
                
                if not part.title.strip():
                    validation['issues'].append(f"Part has empty title")
                    validation['valid'] = False
                
                section_info['parts'].append(part_info)
            
            validation['metrics']['sections'].append(section_info)
        
        # Meeting type specific validation
        if meeting_type == MeetingType.MIDWEEK:
            if total_duration < 90 or total_duration > 120:
                validation['issues'].append(f"Midweek meeting duration unusual: {total_duration} min (expected ~105 min)")
            
            if len(meeting.sections) != 3:
                validation['issues'].append(f"Midweek meeting should have 3 sections, found {len(meeting.sections)}")
        
        elif meeting_type == MeetingType.WEEKEND:
            if total_duration < 90 or total_duration > 110:
                validation['issues'].append(f"Weekend meeting duration unusual: {total_duration} min (expected ~99 min)")
            
            if len(meeting.sections) != 2:
                validation['issues'].append(f"Weekend meeting should have 2 sections, found {len(meeting.sections)}")
        
        return validation

    def analyze_meeting_content(self, meeting: Meeting, meeting_type: MeetingType) -> Dict:
        """Analyze meeting content for completeness"""
        analysis = {
            'songs_found': 0,
            'prayer_parts': 0,
            'study_parts': 0,
            'ministry_parts': 0,
            'has_opening': False,
            'has_closing': False,
            'content_quality': 'good'
        }
        
        all_parts = [part for section in meeting.sections for part in section.parts]
        
        for part in all_parts:
            title_lower = part.title.lower()
            
            if 'song' in title_lower:
                analysis['songs_found'] += 1
            if 'prayer' in title_lower:
                analysis['prayer_parts'] += 1
            if any(word in title_lower for word in ['study', 'bible reading', 'spiritual gems']):
                analysis['study_parts'] += 1
            if any(word in title_lower for word in ['conversation', 'following up', 'ministry']):
                analysis['ministry_parts'] += 1
            if 'opening' in title_lower:
                analysis['has_opening'] = True
            if any(word in title_lower for word in ['concluding', 'closing']):
                analysis['has_closing'] = True
        
        # Quality assessment
        issues = []
        if meeting_type == MeetingType.MIDWEEK:
            if analysis['songs_found'] < 2:
                issues.append(f"Expected at least 2 songs, found {analysis['songs_found']}")
            if analysis['ministry_parts'] < 3:
                issues.append(f"Expected at least 3 ministry parts, found {analysis['ministry_parts']}")
        
        elif meeting_type == MeetingType.WEEKEND:
            if analysis['songs_found'] < 3:
                issues.append(f"Expected at least 3 songs, found {analysis['songs_found']}")
        
        if not analysis['has_opening']:
            issues.append("No opening comments found")
        if not analysis['has_closing']:
            issues.append("No closing comments found")
        
        if issues:
            analysis['content_quality'] = 'poor' if len(issues) > 2 else 'fair'
            analysis['issues'] = issues
        
        return analysis

    def test_single_language(self, language: str) -> Dict:
        """Test scraper for a single language with comprehensive metrics"""
        print(f"\n{'='*50}")
        print(f"🌍 Testing Language: {language.upper()}")
        print(f"{'='*50}")
        
        lang_results = {
            'language': language,
            'success': False,
            'meetings': {},
            'timing': {},
            'errors': []
        }
        
        try:
            # Initialize scraper
            scraper = self.time_operation(
                f"Initialize scraper ({language})",
                lambda: EPUBMeetingScraper(language=language)
            )
            
            # Update meetings cache
            meetings = self.time_operation(
                f"Update meetings cache ({language})",
                scraper.update_meetings
            )
            
            print(f"📊 Found {len(meetings)} meeting types")
            
            # Test each meeting type
            for meeting_type, meeting in meetings.items():
                meeting_name = meeting_type.name
                print(f"\n🔍 Analyzing {meeting_name} meeting...")
                
                # Validate structure
                validation = self.time_operation(
                    f"Validate {meeting_name} structure ({language})",
                    self.validate_meeting_structure,
                    meeting, meeting_type
                )
                
                # Analyze content
                content_analysis = self.time_operation(
                    f"Analyze {meeting_name} content ({language})",
                    self.analyze_meeting_content,
                    meeting, meeting_type
                )
                
                # Store results
                lang_results['meetings'][meeting_name] = {
                    'title': meeting.title,
                    'date': meeting.date.strftime('%Y-%m-%d'),
                    'validation': validation,
                    'content_analysis': content_analysis,
                    'total_duration': meeting.total_duration_minutes
                }
                
                # Print summary
                self.print_meeting_summary(meeting, meeting_type, validation, content_analysis)
            
            lang_results['success'] = True
            
        except Exception as e:
            error_msg = f"Error testing {language}: {str(e)}"
            print(f"❌ {error_msg}")
            lang_results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        # Store timing data for this language
        lang_timing = {k: v for k, v in self.timing_data.items() 
                      if f"({language})" in k}
        lang_results['timing'] = lang_timing
        
        return lang_results

    def print_meeting_summary(self, meeting: Meeting, meeting_type: MeetingType, 
                            validation: Dict, content_analysis: Dict):
        """Print a detailed summary of the meeting"""
        print(f"\n📋 {meeting_type.name} Meeting Summary:")
        print(f"   Title: {meeting.title}")
        print(f"   Date: {meeting.date.strftime('%Y-%m-%d')}")
        print(f"   Total Duration: {meeting.total_duration_minutes} minutes")
        print(f"   Sections: {len(meeting.sections)}")
        print(f"   Total Parts: {validation['metrics']['total_parts']}")
        
        # Validation status
        status = "✅ Valid" if validation['valid'] else "❌ Invalid"
        print(f"   Structure: {status}")
        
        if validation['issues']:
            print(f"   Issues: {', '.join(validation['issues'])}")
        
        # Content quality
        quality_emoji = {"good": "✅", "fair": "⚠️", "poor": "❌"}
        quality = content_analysis['content_quality']
        print(f"   Content Quality: {quality_emoji.get(quality, '❓')} {quality.title()}")
        print(f"   Songs: {content_analysis['songs_found']}, Ministry Parts: {content_analysis['ministry_parts']}")
        
        # Detailed structure
        print(f"\n   📂 Section Breakdown:")
        for i, section in enumerate(meeting.sections):
            print(f"      {i+1}. {section.title} ({section.total_duration_minutes}min, {len(section.parts)} parts)")
            for j, part in enumerate(section.parts):
                print(f"         {j+1}. {part.title} ({part.duration_minutes}min)")

    def print_final_report(self, all_results: List[Dict]):
        """Print comprehensive final report"""
        print(f"\n{'='*60}")
        print("🏁 FINAL TEST REPORT")
        print(f"{'='*60}")
        
        total_time = sum(
            sum(timing['duration'] for timing in result['timing'].values())
            for result in all_results
        )
        
        print(f"⏱️  Total Test Time: {total_time:.2f} seconds")
        print(f"🌍 Languages Tested: {len(all_results)}")
        
        # Success summary
        successful_langs = [r for r in all_results if r['success']]
        failed_langs = [r for r in all_results if not r['success']]
        
        print(f"✅ Successful: {len(successful_langs)}/{len(all_results)}")
        if successful_langs:
            print(f"   Languages: {', '.join([r['language'].upper() for r in successful_langs])}")
        
        if failed_langs:
            print(f"❌ Failed: {len(failed_langs)}/{len(all_results)}")
            print(f"   Languages: {', '.join([r['language'].upper() for r in failed_langs])}")
            for failed in failed_langs:
                print(f"   {failed['language'].upper()}: {', '.join(failed['errors'])}")
        
        # Multi-language timing comparison
        print(f"\n⏱️  Timing Comparison by Language:")
        for result in all_results:
            if result['success']:
                lang_total = sum(timing['duration'] for timing in result['timing'].values())
                lang = result['language'].upper()
                print(f"   {lang}: {lang_total:.2f}s total")
                
                # Break down by operation type for this language
                for operation, timing in result['timing'].items():
                    op_name = operation.split(' (')[0]  # Remove language suffix
                    status = "✅" if timing['success'] else "❌"
                    print(f"      {status} {op_name}: {timing['duration']:.2f}s")
        
        # Cross-language timing breakdown
        print(f"\n Cross-Language Operation Timing:")
        timing_summary = {}
        for result in all_results:
            if result['success']:
                for operation, timing in result['timing'].items():
                    op_type = operation.split(' (')[0]  # Remove language suffix
                    if op_type not in timing_summary:
                        timing_summary[op_type] = {}
                    timing_summary[op_type][result['language']] = timing['duration']
        
        for operation, lang_times in timing_summary.items():
            print(f"   {operation}:")
            for lang, duration in lang_times.items():
                print(f"      {lang.upper()}: {duration:.2f}s")
            if len(lang_times) > 1:
                avg_time = sum(lang_times.values()) / len(lang_times)
                fastest = min(lang_times, key=lang_times.get)
                slowest = max(lang_times, key=lang_times.get)
                print(f"      Avg: {avg_time:.2f}s | Fastest: {fastest.upper()} | Slowest: {slowest.upper()}")
        
        # Cross-language meeting statistics
        print(f"\n Multi-Language Meeting Comparison:")
        meeting_types = set()
        for result in successful_langs:
            meeting_types.update(result['meetings'].keys())
        
        for meeting_type in sorted(meeting_types):
            print(f"\n   {meeting_type} Meetings:")
            print(f"      {'Language':<8} {'Duration':<10} {'Parts':<6} {'Quality':<8} {'Issues'}")
            print(f"      {'-'*50}")
            
            for result in successful_langs:
                if meeting_type in result['meetings']:
                    meeting_data = result['meetings'][meeting_type]
                    lang = result['language'].upper()
                    duration = meeting_data['total_duration']
                    parts = meeting_data['validation']['metrics']['total_parts']
                    quality = meeting_data['content_analysis']['content_quality']
                    issues = len(meeting_data['validation']['issues'])

                    quality_emoji = {"good": "✅", "fair": "⚠️", "poor": "❌"}
                    quality_display = f"{quality_emoji.get(quality, '❓')}{quality}"
                    
                    print(f"      {lang:<8} {duration:<10} {parts:<6} {quality_display:<8} {issues}")
        
        # Language-specific insights
        print(f"\n Language-Specific Insights:")
        for result in successful_langs:
            lang = result['language'].upper()
            total_meetings = len(result['meetings'])
            total_issues = sum(len(m['validation']['issues']) for m in result['meetings'].values())
            
            if total_issues == 0:
                status = " Perfect"
            elif total_issues <= 2:
                status = " Good"
            elif total_issues <= 5:
                status = " Needs attention"
            else:
                status = " Poor quality"
            
            print(f"   {lang}: {status} ({total_meetings} meetings, {total_issues} total issues)")
        
        # Save detailed results
        self.save_test_results(all_results)

    def save_test_results(self, results: List[Dict]):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"epub_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f" Test results saved to: {filename}")
        except Exception as e:
            print(f"  Could not save results: {e}")

    def run_comprehensive_test(self, languages: List[str] = None, clear_cache: bool = True):
        """Run comprehensive test suite"""
        if languages is None:
            languages = ["en"]  # Default to English
        
        print(" Starting Comprehensive EPUB Scraper Test")
        print(f" Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if clear_cache:
            self.clear_cache()
        
        all_results = []
        
        # Test each language
        for language in languages:
            result = self.test_single_language(language)
            all_results.append(result)

        # Additional check for EN midweek meeting for current week
        from datetime import date
        from src.utils.epub_scraper import EPUBMeetingScraper
        from src.models.meeting import MeetingType

        print("\n🔎 Checking current midweek meeting for EN on today's date...")
        try:
            en_scraper = EPUBMeetingScraper(language="en")
            current_meeting = en_scraper.get_meeting_for_current_week(meeting_type=MeetingType.MIDWEEK)
            print(f"📅 Current EN Midweek Meeting for week of {current_meeting.date.strftime('%Y-%m-%d')}: {current_meeting.title}")
            for section in current_meeting.sections:
                print(f" - Section: {section.title}")
                for part in section.parts:
                    print(f"    • {part.title} ({part.duration_minutes} min)")
            # New test: weekend meeting for current week
            weekend_meeting = en_scraper.get_meeting_for_current_week(meeting_type=MeetingType.WEEKEND)
            print(f"📅 Current EN Weekend Meeting for week of {weekend_meeting.date.strftime('%Y-%m-%d')}: {weekend_meeting.title}")
            for section in weekend_meeting.sections:
                print(f" - Section: {section.title}")
                for part in section.parts:
                    print(f"    • {part.title} ({part.duration_minutes} min)")
        except Exception as e:
            print(f"❌ Could not fetch current EN midweek meeting: {e}")
        
        # Print final report
        self.print_final_report(all_results)
        
        return all_results


def main():
    """Main function with command line argument handling"""
    tester = EPUBScraperTester()
    
    # Default test configuration - TEST MULTIPLE LANGUAGES BY DEFAULT
    languages = ["en", "it", "fr", "es", "de"]  # Test multiple languages
    clear_cache = True
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if "--clear-cache" in sys.argv:
            clear_cache = True
        elif "--no-clear-cache" in sys.argv:
            clear_cache = False
        
        if "--languages" in sys.argv:
            lang_index = sys.argv.index("--languages") + 1
            if lang_index < len(sys.argv):
                languages = sys.argv[lang_index].split(",")
        
        if "--single-lang" in sys.argv:
            lang_index = sys.argv.index("--single-lang") + 1
            if lang_index < len(sys.argv):
                languages = [sys.argv[lang_index]]
            else:
                languages = ["en"]  # Default to English if no language specified
        
        if "--profile" in sys.argv:
            print("🔍 Profiling mode enabled - detailed timing analysis")
    
    # Run the test
    start_time = time.time()
    results = tester.run_comprehensive_test(languages, clear_cache)
    total_time = time.time() - start_time
    
    print(f"\n🎯 Test completed in {total_time:.2f} seconds")
    
    # Exit with appropriate code
    successful_tests = sum(1 for r in results if r['success'])
    if successful_tests == len(results):
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"⚠️  {len(results) - successful_tests} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()