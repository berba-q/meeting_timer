"""
Updated test script for the improved MeetingScraper with performance timing.
This tests both midweek and weekend meeting extraction with speed benchmarks.
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import shutil
from pathlib import Path
import time
from typing import Dict, List
import logging
logging.basicConfig(filename='epub_test.log', filemode='w', level=logging.INFO, format='%(message)s')

from src.utils.optimized_scraper import OptimizedMeetingScraper
from src.utils.scraper import MeetingScraper
from src.models.meeting import MeetingType

# EPUB scraper import
from src.utils.epub_scraper import EPUBMeetingScraper

# Add the parent directory to sys.path so we can import modules from there
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)



def clear_all_cache_once():
    """Clear the entire cache directory ONCE at the start"""
    try:
        from platformdirs import user_cache_dir
    except ImportError:
        cache_dir = Path.home() / ".meeting_timer_cache"
    else:
        cache_dir = Path(user_cache_dir("MeetingTimer"))
    
    if cache_dir.exists():
        logging.info(f"Clearing cache directory: {cache_dir}")
        shutil.rmtree(cache_dir)
        logging.info("Cache cleared successfully!")
    else:
        logging.info("Cache directory doesn't exist - no need to clear")


def test_epub_full():
    """Test EPUB scraper with multiple languages"""
    logging.info("=== EPUB MULTI-LANGUAGE TEST ===")

    languages_to_test = ["en", "it", "fr", "es", "de"]
    timing_results = TimingResults()

    # Clear cache ONCE at the beginning, not between languages!
    clear_all_cache_once()

    for lang in languages_to_test:
        logging.info(f"\n{'='*60}")
        logging.info(f"Testing EPUB scraper with language: {lang.upper()}")
        logging.info('='*60)

        # DO NOT clear cache here! Each language should have its own cache file
        scraper = EPUBMeetingScraper(language=lang)

        # Test current meetings first
        logging.info(f"\n[{lang}] Fetching current meetings:")
        for m_type in [MeetingType.MIDWEEK, MeetingType.WEEKEND]:
            meeting = scraper.get_meeting_for_current_week(meeting_type=m_type)
            if meeting:
                logging.info(f"\n--- {m_type.value.upper()} MEETING ---")
                logging.info(f"Title: {meeting.title}")
                logging.info(f"Date: {meeting.date.strftime('%Y-%m-%d')}")
                logging.info(f"Total Duration: {meeting.total_duration_minutes} minutes")
                logging.info(f"Sections: {len(meeting.sections)}")
                for i, section in enumerate(meeting.sections):
                    logging.info(f"  Section {i+1}: {section.title} ({section.total_duration_minutes} min, {len(section.parts)} parts)")
            else:
                logging.info(f"\n--- {m_type.value.upper()} MEETING ---")
                logging.info("No meeting found for current week.")

        # Time the update process
        total_start_time = time.time()
        try:
            meetings = scraper.update_meetings()
            total_time = time.time() - total_start_time

            logging.info(f"\n✓ Total: {total_time:.3f}s")
            logging.info(f"✓ Meetings: {len(meetings)}")

            timing_results.add_result(lang, "EPUB", total_time, len(meetings))

            # Display meeting details
            for meeting_type, meeting in meetings.items():
                logging.info(f"\n--- {meeting_type.value.upper()} MEETING ---")
                logging.info(f"Title: {meeting.title}")
                logging.info(f"Date: {meeting.date.strftime('%Y-%m-%d')}")
                logging.info(f"Total Duration: {meeting.total_duration_minutes} minutes")
                logging.info(f"Sections: {len(meeting.sections)}")
                
                for i, section in enumerate(meeting.sections):
                    logging.info(f"  Section {i+1}: {section.title} ({section.total_duration_minutes} min, {len(section.parts)} parts)")

            # Check cache file
            logging.info(f"[{lang}] Cache file: {scraper.cache_path}")
            if scraper.cache_path.exists():
                cache_size = scraper.cache_path.stat().st_size
                logging.info(f"[{lang}] ✅ Cache file exists ({cache_size} bytes)")
            else:
                logging.info(f"[{lang}] ❌ Cache file missing!")

        except Exception as e:
            total_time = time.time() - total_start_time
            logging.info(f"[{lang.upper()}] Error: {str(e)} (after {total_time:.3f}s)")
            timing_results.add_result(lang, "EPUB", total_time, 0)

        logging.info(f"[{lang}] Test complete. Meetings found: {len(meetings)}")

    timing_results.print_summary()

    
    # Show final cache status
    logging.info(f"\n{'='*80}")
    logging.info("FINAL CACHE STATUS")
    logging.info('='*80)
    
    try:
        from platformdirs import user_cache_dir
        cache_dir = Path(user_cache_dir("MeetingTimer"))
    except ImportError:
        cache_dir = Path.home() / ".meeting_timer_cache"
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*_meetings_cache.json"))
        logging.info(f"Cache directory: {cache_dir}")
        logging.info(f"Cache files found: {len(cache_files)}")
        
        for cache_file in cache_files:
            lang = cache_file.name.split('_')[0]
            size = cache_file.stat().st_size
            logging.info(f"  {lang.upper()}: {cache_file.name} ({size} bytes)")
    else:
        logging.info("No cache directory found!")

def test_single_language_debug(language: str = "de"):
    """Test a single language with detailed debugging"""
    logging.info(f"\n{'='*60}")
    logging.info(f"SINGLE LANGUAGE DEBUG: {language.upper()}")
    logging.info('='*60)
    
    # Clear cache for clean test
    clear_all_cache_once()
    
    scraper = EPUBMeetingScraper(language=language)

    # Print the internal log if available
    if hasattr(scraper, "_last_log_lines"):
        log_lines = scraper._last_log_lines
        log_path = f"epub_meeting_log_{language}.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        logging.info(f"📄 Internal log written to {log_path}")

    logging.info(f"1. Language: {language}")
    logging.info(f"2. Language code: {scraper.lang_code}")
    logging.info(f"3. Cache path: {scraper.cache_path}")

    # Test issue calculation
    mwb_issue, w_issue = scraper._get_current_issue_dates()
    logging.info(f"4. MWB issue: {mwb_issue}")
    logging.info(f"5. WT issue: {w_issue}")

    # Test the full process
    logging.info(f"\n6. Running full update process...")
    start_time = time.time()

    try:
        meetings = scraper.update_meetings()
        elapsed = time.time() - start_time

        # Print the internal log if available
        if hasattr(scraper, "_last_log_lines"):
            log_lines = scraper._last_log_lines
            log_path = f"epub_meeting_log_{language}.txt"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))
            logging.info(f"📄 Internal log written to {log_path}")

        logging.info(f"   ✅ Success in {elapsed:.3f}s")
        logging.info(f"   Meetings found: {len(meetings)}")

        for meeting_type, meeting in meetings.items():
            logging.info(f"   - {meeting_type.name}: {meeting.title}")

        # Check cache
        if scraper.cache_path.exists():
            size = scraper.cache_path.stat().st_size
            logging.info(f"   Cache: {scraper.cache_path.name} ({size} bytes)")
        else:
            logging.info(f"   ❌ No cache file created!")

    except Exception as e:
        elapsed = time.time() - start_time
        logging.info(f"   ❌ Error after {elapsed:.3f}s: {e}")
        import traceback
        traceback.print_exc()

class TimingResults:
    """Class to store and display timing results"""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, language: str, method: str, duration: float, meetings_count: int):
        """Add a timing result"""
        if language not in self.results:
            self.results[language] = {}
        self.results[language][method] = {
            'duration': duration,
            'meetings_count': meetings_count,
            'meetings_per_second': meetings_count / duration if duration > 0 else 0
        }
    
    def print_summary(self):
        """Print a summary of all timing results"""
        logging.info("\n" + "="*80)
        logging.info("PERFORMANCE SUMMARY")
        logging.info("="*80)
        
        for language, methods in self.results.items():
            logging.info(f"\n{language.upper()}:")
            for method, data in methods.items():
                logging.info(f"  {method:20s}: {data['duration']:6.2f}s ({data['meetings_count']} meetings, {data['meetings_per_second']:.2f} meetings/s)")
        
        # Calculate averages
        if len(self.results) > 1:
            logging.info("\nAVERAGES:")
            method_totals = {}
            
            for language, methods in self.results.items():
                for method, data in methods.items():
                    if method not in method_totals:
                        method_totals[method] = {'total_time': 0, 'total_meetings': 0, 'count': 0}
                    
                    method_totals[method]['total_time'] += data['duration']
                    method_totals[method]['total_meetings'] += data['meetings_count']
                    method_totals[method]['count'] += 1
            
            for method, totals in method_totals.items():
                avg_time = totals['total_time'] / totals['count']
                avg_meetings = totals['total_meetings'] / totals['count']
                avg_rate = avg_meetings / avg_time if avg_time > 0 else 0
                logging.info(f"  {method:20s}: {avg_time:6.2f}s avg ({avg_meetings:.1f} meetings, {avg_rate:.2f} meetings/s)")


def test_optimized_vs_original():
    """Test optimized version vs original - MAIN COMPARISON"""
    logging.info("=== OPTIMIZED vs ORIGINAL COMPARISON ===")
    
    # Test original
    logging.info("\n1. Testing ORIGINAL implementation...")
    clear_all_cache_once()
    original_scraper = MeetingScraper("en")

    start_time = time.time()
    original_meetings = original_scraper.update_meetings()
    original_time = time.time() - start_time

    logging.info(f"✓ Original: {original_time:.2f}s ({len(original_meetings)} meetings)")

    # Test optimized
    logging.info("\n2. Testing OPTIMIZED implementation...")
    clear_all_cache_once()
    optimized_scraper = OptimizedMeetingScraper("en")

    start_time = time.time()
    optimized_meetings = optimized_scraper.update_meetings()
    optimized_time = time.time() - start_time

    logging.info(f"✓ Optimized: {optimized_time:.2f}s ({len(optimized_meetings)} meetings)")

    # Test EPUB
    logging.info("\n3. Testing EPUB implementation...")
    clear_all_cache_once()
    epub_scraper = EPUBMeetingScraper("en")

    start_time = time.time()
    epub_meetings = epub_scraper.update_meetings()
    epub_time = time.time() - start_time

    logging.info(f"✓ EPUB: {epub_time:.2f}s ({len(epub_meetings)} meetings)")

    # Compare results
    if original_time > 0:
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        improvement = ((original_time - optimized_time) / original_time) * 100

        logging.info(f"\n📊 RESULTS:")
        logging.info(f"   Speedup: {speedup:.1f}x faster")
        logging.info(f"   Improvement: {improvement:.1f}%")
        logging.info(f"   Time saved: {original_time - optimized_time:.1f}s")

        target_met = "✅" if optimized_time < 9.0 else "❌"
        logging.info(f"   Single-digit target (<9s): {target_met}")

        if optimized_time < 9.0:
            logging.info("🎉 SUCCESS! Single-digit performance achieved!")
        elif speedup > 2.0:
            logging.info("🚀 Great improvement! Close to single-digit target.")
        else:
            logging.info("⚠️  Need more optimization for single-digit target.")

        # EPUB comparison block
        if original_time > 0:
            epub_speedup = original_time / epub_time if epub_time > 0 else float('inf')
            epub_improvement = ((original_time - epub_time) / original_time) * 100

            logging.info(f"\n📊 EPUB RESULTS:")
            logging.info(f"   Speedup vs Original: {epub_speedup:.1f}x faster")
            logging.info(f"   Improvement: {epub_improvement:.1f}%")
            logging.info(f"   Time saved: {original_time - epub_time:.1f}s")

            target_met = "✅" if epub_time < 9.0 else "❌"
            logging.info(f"   Single-digit target (<9s): {target_met}")

    return original_time, optimized_time

def test_optimized_with_detailed_timing():
    """Test optimized scraper with detailed timing breakdown"""
    logging.info("=== OPTIMIZED SCRAPER DETAILED TIMING ===")
    clear_all_cache_once()
    
    language = "en"
    scraper = OptimizedMeetingScraper(language=language)
    
    logging.info(f"Testing detailed timing for {language.upper()} (optimized)...")
    
    # Step 1: Time URL fetching
    logging.info("\n1. Fetching meeting URLs...")
    start_time = time.time()
    meeting_links = scraper.get_current_meeting_urls()
    url_fetch_time = time.time() - start_time
    logging.info(f"   URL fetch time: {url_fetch_time:.3f}s")
    logging.info(f"   Found {len(meeting_links)} meeting URLs")
    
    # Step 2: Time complete scraping
    logging.info("\n2. Complete optimized scraping:")
    start_time = time.time()
    meetings = scraper.update_meetings()
    total_time = time.time() - start_time
    
    logging.info(f"   Total time: {total_time:.3f}s")
    logging.info(f"   Meetings retrieved: {len(meetings)}")
    
    for meeting_type, meeting in meetings.items():
        logging.info(f"   ✓ {meeting_type.value}: {meeting.title}")
        logging.info(f"     - Sections: {len(meeting.sections)}")
        logging.info(f"     - Total parts: {sum(len(s.parts) for s in meeting.sections)}")
    
    # Step 3: Cache performance test
    logging.info("\n3. Cache performance test:")
    logging.info("   Testing cached retrieval...")
    
    start_time = time.time()
    meetings_cached = scraper.update_meetings()  # Should be much faster due to cache
    cached_time = time.time() - start_time
    
    logging.info(f"   Cached retrieval: {cached_time:.3f}s")
    
    if total_time > 0:
        cache_speedup = total_time / cached_time if cached_time > 0 else float('inf')
        logging.info(f"   Cache speedup: {cache_speedup:.1f}x faster")

def test_single_digit_attempt():
    """Quick test to see if we hit single digits"""
    logging.info("🎯 SINGLE-DIGIT ATTEMPT (OPTIMIZED)")
    
    clear_all_cache_once()
    scraper = OptimizedMeetingScraper("en")
    
    start_time = time.time()
    meetings = scraper.update_meetings()
    total_time = time.time() - start_time
    
    result = "✅ SUCCESS!" if total_time < 9.0 else "❌ Not yet"
    logging.info(f"{result} Time: {total_time:.2f}s (target: <9s)")
    logging.info(f"Meetings: {len(meetings)}")
    
    return total_time

def test_optimized_multi_language():
    """Test optimized scraper with multiple languages"""
    logging.info("=== OPTIMIZED MULTI-LANGUAGE TEST ===")
    
    languages_to_test = ["en", "it", "fr", "es", "de"]
    timing_results = TimingResults()
    
    for lang in languages_to_test:
        logging.info(f"\n{'='*60}")
        logging.info(f"Testing OPTIMIZED scraper with language: {lang.upper()}")
        logging.info('='*60)
        
        clear_all_cache_once()  # Clear cache for each language test
        scraper = OptimizedMeetingScraper(language=lang)
        
        # Time the entire process
        total_start_time = time.time()
        
        try:
            logging.info("Fetching meeting URLs...")
            url_start_time = time.time()
            meeting_links = scraper.get_current_meeting_urls()
            url_fetch_time = time.time() - url_start_time
            
            logging.info(f"URL fetch completed in {url_fetch_time:.3f}s")
            logging.info(f"Found URLs:")
            for meeting_type, url in meeting_links.items():
                logging.info(f"- {meeting_type.value}: {url}")
            
            # Time the scraping process
            scrape_start_time = time.time()
            meetings = scraper.update_meetings()
            scrape_time = time.time() - scrape_start_time
            
            total_time = time.time() - total_start_time
            
            logging.info(f"\nTIMING RESULTS:")
            logging.info(f"- URL fetch: {url_fetch_time:.3f}s")
            logging.info(f"- Scraping:  {scrape_time:.3f}s")
            logging.info(f"- Total:     {total_time:.3f}s")
            
            timing_results.add_result(lang, "Total", total_time, len(meetings))
            timing_results.add_result(lang, "Scraping", scrape_time, len(meetings))
            
            # Show meeting details
            for meeting_type, meeting in meetings.items():
                logging.info(f"\n--- {meeting_type.value.upper()} MEETING ---")
                logging.info(f"Title: {meeting.title}")
                logging.info(f"Date: {meeting.date.strftime('%Y-%m-%d')}")
                logging.info(f"Total Duration: {meeting.total_duration_minutes} minutes")
                logging.info(f"Sections: {len(meeting.sections)}")
                
                for i, section in enumerate(meeting.sections):
                    logging.info(f"  Section {i+1}: {section.title} ({section.total_duration_minutes} min, {len(section.parts)} parts)")
            
            logging.info(f"\n--- SUMMARY FOR {lang.upper()} ---")
            logging.info(f"Successfully tested {len(meetings)} meeting types in {total_time:.3f}s")
            
            # Check if single-digit target met
            if total_time < 9.0:
                logging.info(f"🎯 Single-digit target MET! ({total_time:.2f}s)")
            else:
                logging.info(f"⏱️  Single-digit target missed ({total_time:.2f}s)")
            
        except Exception as e:
            total_time = time.time() - total_start_time
            logging.info(f"[{lang.upper()}] Error: {str(e)} (after {total_time:.3f}s)")
            timing_results.add_result(lang, "Total", total_time, 0)
    
    timing_results.print_summary()

def benchmark_optimized_cache_performance():
    """Benchmark optimized scraper cache performance"""
    logging.info("=== OPTIMIZED CACHE PERFORMANCE BENCHMARK ===")
    
    language = "en"
    scraper = OptimizedMeetingScraper(language=language)
    
    # Test 1: Cold cache (no cache)
    logging.info("1. Cold cache test...")
    clear_all_cache_once()
    
    start_time = time.time()
    meetings_cold = scraper.update_meetings()
    cold_time = time.time() - start_time
    logging.info(f"   Cold cache: {cold_time:.3f}s ({len(meetings_cold)} meetings)")
    
    # Test 2: Warm cache (should use cached data)
    logging.info("2. Warm cache test...")
    
    start_time = time.time()
    meetings_warm = scraper.update_meetings()
    warm_time = time.time() - start_time
    logging.info(f"   Warm cache: {warm_time:.3f}s ({len(meetings_warm)} meetings)")
    
    if cold_time > 0 and warm_time > 0:
        cache_improvement = ((cold_time - warm_time) / cold_time) * 100
        cache_speedup = cold_time / warm_time
        logging.info(f"   Cache improvement: {cache_speedup:.1f}x faster ({cache_improvement:.1f}% improvement)")
    
    # Test 3: Multiple runs to test consistency
    logging.info("3. Consistency test (5 runs with cache)...")
    
    times = []
    for i in range(5):
        start_time = time.time()
        meetings = scraper.update_meetings()
        run_time = time.time() - start_time
        times.append(run_time)
        logging.info(f"   Run {i+1}: {run_time:.3f}s")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    logging.info(f"   Average: {avg_time:.3f}s")
    logging.info(f"   Range: {min_time:.3f}s - {max_time:.3f}s")

def test_pre_scan_feature():
    """Test the pre-scan all languages feature"""
    logging.info("=== PRE-SCAN ALL LANGUAGES FEATURE ===")
    
    clear_all_cache_once()
    languages = ["en", "it", "fr"]  # Test subset for speed
    
    logging.info(f"Testing pre-scan feature with {languages}...")
    start_time = time.time()
    
    all_urls = OptimizedMeetingScraper.pre_scan_all_languages(languages)
    
    pre_scan_time = time.time() - start_time
    
    logging.info(f"Pre-scan completed in {pre_scan_time:.2f}s")
    logging.info(f"Found URLs for {len(all_urls)} languages:")
    
    for lang, urls in all_urls.items():
        logging.info(f"  {lang}: {len(urls)} meeting URLs")
    
    # Now test individual scraping with pre-populated cache
    logging.info("\nTesting individual scraping with pre-populated cache...")
    
    for lang in languages:
        logging.info(f"\nScraping {lang} with cached URLs...")
        start_time = time.time()
        
        scraper = OptimizedMeetingScraper(lang)
        meetings = scraper.update_meetings()
        
        scrape_time = time.time() - start_time
        logging.info(f"  {lang}: {scrape_time:.2f}s ({len(meetings)} meetings)")

# LEGACY FUNCTIONS for backward compatibility
def test_parallel_vs_sequential_speed():
    """Legacy function - now compares optimized vs original"""
    print("NOTE: Converting to optimized vs original comparison...")
    return test_optimized_vs_original()

def test_with_detailed_timing():
    """Legacy function - now uses optimized scraper"""
    print("NOTE: Using optimized scraper for detailed timing...")
    return test_optimized_with_detailed_timing()

def test_live_scraper_with_timing():
    """Legacy function - now uses optimized multi-language test"""
    print("NOTE: Using optimized multi-language test...")
    return test_optimized_multi_language()

def benchmark_cache_performance():
    """Legacy function - now uses optimized cache benchmark"""
    print("NOTE: Using optimized cache benchmark...")
    return benchmark_optimized_cache_performance()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--speed-test":
            test_optimized_vs_original()
        elif sys.argv[1] == "--optimized":
            test_optimized_vs_original()
        elif sys.argv[1] == "--single-digit":
            test_single_digit_attempt()
        elif sys.argv[1] == "--detailed":
            test_optimized_with_detailed_timing()
        elif sys.argv[1] == "--full":
            test_optimized_multi_language()
        elif sys.argv[1] == "--cache":
            benchmark_optimized_cache_performance()
        elif sys.argv[1] == "--pre-scan":
            test_pre_scan_feature()
        elif sys.argv[1] == "--epub-full":
            test_epub_full()
        elif sys.argv[1] == "--single-language-debug":
            lang = sys.argv[2] if len(sys.argv) > 2 else "de"
            test_single_language_debug(lang)
        elif sys.argv[1] == "--all":
            logging.info("Running all optimized performance tests...\n")
            test_optimized_vs_original()
            logging.info("\n" + "="*100 + "\n")
            test_optimized_with_detailed_timing()
            logging.info("\n" + "="*100 + "\n")
            benchmark_optimized_cache_performance()
            logging.info("\n" + "="*100 + "\n")
            test_pre_scan_feature()
        else:
            logging.info("Unknown option. Use --help for usage.")
    else:
        logging.info("Usage:")
        logging.info("  python test_scraper.py --speed-test   # Compare optimized vs original")
        logging.info("  python test_scraper.py --optimized    # Same as --speed-test")
        logging.info("  python test_scraper.py --single-digit # Quick single-digit test")
        logging.info("  python test_scraper.py --detailed     # Detailed timing breakdown")
        logging.info("  python test_scraper.py --full         # Multi-language test")
        logging.info("  python test_scraper.py --cache        # Cache performance test")
        logging.info("  python test_scraper.py --pre-scan     # Test pre-scan feature")
        logging.info("  python test_scraper.py --epub-full    # EPUB multi-language test")
        logging.info("  python test_scraper.py --all          # Run all performance tests")
        logging.info("")
        logging.info("Running optimized vs original comparison...")
        test_optimized_vs_original()