"""
Tests for mirror fallback and retry system in RobustDownloadManager.

This module tests the intelligent mirror system with health monitoring,
configurable retry system with exponential backoff, and fallback mechanisms.
"""

import hashlib
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import urllib.error
import ssl

from core.robust_download_manager import (
    RobustDownloadManager,
    DownloadResult,
    DownloadStatus,
    MirrorInfo,
    MirrorStatus,
    MirrorResult,
    RetryResult,
    RetryExhaustedError,
    DownloadError,
    HashVerificationError,
    SecureConnectionError
)


class TestMirrorFallbackRetrySystem(unittest.TestCase):
    """Test cases for mirror fallback and retry system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.download_manager = RobustDownloadManager(temp_dir=self.temp_dir, max_retries=3)
        
        # Test data
        self.test_content = b"Test file content for mirror fallback testing"
        self.test_hash = hashlib.sha256(self.test_content).hexdigest()
        
        self.primary_url = "https://primary.example.com/file.zip"
        self.mirror_urls = [
            "https://mirror1.example.com/file.zip",
            "https://mirror2.example.com/file.zip",
            "https://mirror3.example.com/file.zip"
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.object(RobustDownloadManager, '_check_mirror_health')
    def test_implement_intelligent_mirror_system(self, mock_health_check):
        """Test intelligent mirror system implementation."""
        # Mock health check to avoid network calls
        mock_health_check.return_value = None
        
        # Test mirror system initialization
        result = self.download_manager.implement_intelligent_mirror_system(self.mirror_urls)
        
        self.assertIsInstance(result, MirrorResult)
        self.assertIsNotNone(result.selected_mirror)
        self.assertIn(result.selected_mirror, self.mirror_urls)
        self.assertEqual(len(result.mirror_health), len(self.mirror_urls))
        
        # Verify mirror health initialization
        for mirror_url in self.mirror_urls:
            self.assertIn(mirror_url, self.download_manager.mirror_health)
            mirror_info = self.download_manager.mirror_health[mirror_url]
            self.assertIsInstance(mirror_info, MirrorInfo)
            self.assertEqual(mirror_info.url, mirror_url)
            self.assertEqual(mirror_info.status, MirrorStatus.HEALTHY)
    
    def test_execute_configurable_retries(self):
        """Test configurable retry system."""
        # Test default retry configuration
        result = self.download_manager.execute_configurable_retries()
        
        self.assertIsInstance(result, RetryResult)
        self.assertEqual(result.max_retries, 3)
        self.assertEqual(result.attempt_number, 0)
        self.assertFalse(result.success)
        self.assertEqual(len(result.retry_history), 0)
        
        # Test custom retry configuration
        custom_result = self.download_manager.execute_configurable_retries(max_retries=5)
        self.assertEqual(custom_result.max_retries, 5)
    
    def test_implement_exponential_backoff(self):
        """Test exponential backoff implementation."""
        # Test backoff calculation
        self.assertEqual(self.download_manager.implement_exponential_backoff(0), 0)
        
        backoff_1 = self.download_manager.implement_exponential_backoff(1)
        self.assertGreaterEqual(backoff_1, 1)
        self.assertLessEqual(backoff_1, 2)
        
        backoff_2 = self.download_manager.implement_exponential_backoff(2)
        self.assertGreaterEqual(backoff_2, 2)
        self.assertLessEqual(backoff_2, 3)
        
        backoff_3 = self.download_manager.implement_exponential_backoff(3)
        self.assertGreaterEqual(backoff_3, 4)
        self.assertLessEqual(backoff_3, 5)
        
        # Verify exponential growth
        self.assertLess(backoff_1, backoff_2)
        self.assertLess(backoff_2, backoff_3)
    
    @patch('urllib.request.urlopen')
    def test_mirror_health_check_healthy(self, mock_urlopen):
        """Test mirror health check for healthy mirror."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response
        
        # Initialize mirror and check health
        mirror_url = self.mirror_urls[0]
        self.download_manager.mirror_health[mirror_url] = MirrorInfo(url=mirror_url)
        
        self.download_manager._check_mirror_health(mirror_url)
        
        mirror_info = self.download_manager.mirror_health[mirror_url]
        self.assertEqual(mirror_info.status, MirrorStatus.HEALTHY)
        self.assertIsNotNone(mirror_info.last_health_check)
        self.assertGreater(mirror_info.response_time, 0)
    
    @patch('urllib.request.urlopen')
    @patch('time.time')
    def test_mirror_health_check_slow(self, mock_time, mock_urlopen):
        """Test mirror health check for slow mirror."""
        # Mock slow response
        def slow_response(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            return mock_response
        
        mock_urlopen.side_effect = slow_response
        
        # Mock time.time to simulate slow response (3 second response time)
        mock_time.side_effect = [0, 3.0, 3.0]  # start, end, last_health_check
        
        # Initialize mirror and check health
        mirror_url = self.mirror_urls[0]
        self.download_manager.mirror_health[mirror_url] = MirrorInfo(url=mirror_url)
        
        self.download_manager._check_mirror_health(mirror_url)
        
        mirror_info = self.download_manager.mirror_health[mirror_url]
        self.assertEqual(mirror_info.status, MirrorStatus.SLOW)
    
    @patch('urllib.request.urlopen')
    def test_mirror_health_check_unreachable(self, mock_urlopen):
        """Test mirror health check for unreachable mirror."""
        # Mock connection error
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        # Initialize mirror and check health
        mirror_url = self.mirror_urls[0]
        self.download_manager.mirror_health[mirror_url] = MirrorInfo(url=mirror_url)
        
        self.download_manager._check_mirror_health(mirror_url)
        
        mirror_info = self.download_manager.mirror_health[mirror_url]
        self.assertEqual(mirror_info.status, MirrorStatus.UNREACHABLE)
        self.assertIsNotNone(mirror_info.last_health_check)
    
    def test_select_best_mirror(self):
        """Test best mirror selection algorithm."""
        # Initialize mirrors with different health statuses
        mirrors = self.mirror_urls[:3]
        
        # Mirror 1: Healthy with good performance
        self.download_manager.mirror_health[mirrors[0]] = MirrorInfo(
            url=mirrors[0],
            status=MirrorStatus.HEALTHY,
            response_time=1.0,
            success_count=10,
            failure_count=1
        )
        
        # Mirror 2: Slow but reliable
        self.download_manager.mirror_health[mirrors[1]] = MirrorInfo(
            url=mirrors[1],
            status=MirrorStatus.SLOW,
            response_time=3.0,
            success_count=8,
            failure_count=2
        )
        
        # Mirror 3: Unreachable
        self.download_manager.mirror_health[mirrors[2]] = MirrorInfo(
            url=mirrors[2],
            status=MirrorStatus.UNREACHABLE,
            response_time=10.0,
            success_count=2,
            failure_count=8
        )
        
        # Test best mirror selection
        best_mirror = self.download_manager._select_best_mirror(mirrors)
        self.assertEqual(best_mirror, mirrors[0])  # Should select the healthy one
    
    def test_select_best_mirror_no_healthy(self):
        """Test best mirror selection when no mirrors are healthy."""
        mirrors = self.mirror_urls[:2]
        
        # All mirrors unreachable
        for mirror in mirrors:
            self.download_manager.mirror_health[mirror] = MirrorInfo(
                url=mirror,
                status=MirrorStatus.UNREACHABLE,
                response_time=10.0,
                success_count=0,
                failure_count=5
            )
        
        # Should fallback to first mirror
        best_mirror = self.download_manager._select_best_mirror(mirrors)
        self.assertEqual(best_mirror, mirrors[0])
    
    def test_select_best_mirror_empty_list(self):
        """Test best mirror selection with empty mirror list."""
        best_mirror = self.download_manager._select_best_mirror([])
        self.assertIsNone(best_mirror)
    
    @patch.object(RobustDownloadManager, 'download_with_mandatory_hash_verification')
    def test_download_with_mirror_fallback_success_first_try(self, mock_download):
        """Test successful download on first attempt."""
        # Mock successful download
        expected_result = DownloadResult(
            url=self.primary_url,
            file_path=self.temp_dir / "test.zip",
            status=DownloadStatus.COMPLETED,
            file_size=len(self.test_content),
            download_time=1.0,
            sha256_hash=self.test_hash,
            expected_hash=self.test_hash
        )
        mock_download.return_value = expected_result
        
        # Test download with mirror fallback
        result = self.download_manager.download_with_mirror_fallback_and_retry(
            url=self.primary_url,
            expected_sha256=self.test_hash,
            mirrors=self.mirror_urls
        )
        
        self.assertEqual(result.status, DownloadStatus.COMPLETED)
        self.assertEqual(result.url, self.primary_url)
        mock_download.assert_called_once()
    
    @patch.object(RobustDownloadManager, 'download_with_mandatory_hash_verification')
    @patch('time.sleep')
    def test_download_with_mirror_fallback_retry_success(self, mock_sleep, mock_download):
        """Test successful download after retries."""
        # Mock first two attempts fail, third succeeds
        mock_download.side_effect = [
            DownloadError("Network error"),
            DownloadError("Timeout"),
            DownloadResult(
                url=self.primary_url,
                file_path=self.temp_dir / "test.zip",
                status=DownloadStatus.COMPLETED,
                file_size=len(self.test_content),
                download_time=1.0,
                sha256_hash=self.test_hash,
                expected_hash=self.test_hash
            )
        ]
        
        # Test download with retries
        result = self.download_manager.download_with_mirror_fallback_and_retry(
            url=self.primary_url,
            expected_sha256=self.test_hash,
            max_retries=3
        )
        
        self.assertEqual(result.status, DownloadStatus.COMPLETED)
        self.assertEqual(mock_download.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Two retry delays
    
    @patch.object(RobustDownloadManager, 'download_with_mandatory_hash_verification')
    def test_download_with_mirror_fallback_all_fail(self, mock_download):
        """Test download failure when all mirrors and retries fail."""
        # Mock all attempts fail
        mock_download.side_effect = DownloadError("All mirrors failed")
        
        # Test download with mirror fallback - should raise RetryExhaustedError
        with self.assertRaises(RetryExhaustedError):
            self.download_manager.download_with_mirror_fallback_and_retry(
                url=self.primary_url,
                expected_sha256=self.test_hash,
                mirrors=self.mirror_urls[:2],
                max_retries=2
            )
        
        # Should have tried primary + 2 mirrors, each with 3 attempts (initial + 2 retries)
        expected_calls = 3 * 3  # 3 URLs * 3 attempts each
        self.assertEqual(mock_download.call_count, expected_calls)
    
    @patch.object(RobustDownloadManager, 'download_with_mandatory_hash_verification')
    def test_download_with_mirror_fallback_updates_health(self, mock_download):
        """Test that mirror health is updated based on success/failure."""
        # Initialize mirror health
        mirror_url = self.mirror_urls[0]
        self.download_manager.mirror_health[mirror_url] = MirrorInfo(url=mirror_url)
        
        # Mock successful download
        mock_download.return_value = DownloadResult(
            url=mirror_url,
            file_path=self.temp_dir / "test.zip",
            status=DownloadStatus.COMPLETED,
            file_size=len(self.test_content),
            download_time=1.0,
            sha256_hash=self.test_hash,
            expected_hash=self.test_hash
        )
        
        # Test download
        result = self.download_manager.download_with_mirror_fallback_and_retry(
            url=mirror_url,
            expected_sha256=self.test_hash
        )
        
        # Verify mirror health was updated
        mirror_info = self.download_manager.mirror_health[mirror_url]
        self.assertEqual(mirror_info.success_count, 1)
        self.assertEqual(mirror_info.status, MirrorStatus.HEALTHY)
        self.assertIsNotNone(mirror_info.last_used)
    
    def test_get_mirror_health_report(self):
        """Test mirror health report generation."""
        # Initialize mirrors with different health data
        mirrors = self.mirror_urls[:2]
        
        self.download_manager.mirror_health[mirrors[0]] = MirrorInfo(
            url=mirrors[0],
            status=MirrorStatus.HEALTHY,
            response_time=1.5,
            success_count=8,
            failure_count=2,
            last_used=time.time(),
            last_health_check=time.time()
        )
        
        self.download_manager.mirror_health[mirrors[1]] = MirrorInfo(
            url=mirrors[1],
            status=MirrorStatus.SLOW,
            response_time=4.0,
            success_count=5,
            failure_count=5,
            last_used=time.time() - 100,
            last_health_check=time.time() - 50
        )
        
        # Get health report
        report = self.download_manager.get_mirror_health_report()
        
        self.assertEqual(len(report), 2)
        
        # Check first mirror report
        mirror1_report = report[mirrors[0]]
        self.assertEqual(mirror1_report["status"], "healthy")
        self.assertEqual(mirror1_report["response_time"], 1.5)
        self.assertEqual(mirror1_report["success_count"], 8)
        self.assertEqual(mirror1_report["failure_count"], 2)
        self.assertEqual(mirror1_report["success_rate"], 80.0)
        
        # Check second mirror report
        mirror2_report = report[mirrors[1]]
        self.assertEqual(mirror2_report["status"], "slow")
        self.assertEqual(mirror2_report["success_rate"], 50.0)
    
    def test_mirror_health_thread_safety(self):
        """Test thread safety of mirror health operations."""
        import threading
        
        mirror_url = self.mirror_urls[0]
        self.download_manager.mirror_health[mirror_url] = MirrorInfo(url=mirror_url)
        
        def update_mirror_health():
            for _ in range(100):
                with self.download_manager._lock:
                    mirror_info = self.download_manager.mirror_health[mirror_url]
                    mirror_info.success_count += 1
        
        # Run multiple threads updating mirror health
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_mirror_health)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final count is correct
        mirror_info = self.download_manager.mirror_health[mirror_url]
        self.assertEqual(mirror_info.success_count, 500)  # 5 threads * 100 updates each


class TestMirrorSystemIntegration(unittest.TestCase):
    """Integration tests for mirror system with real network conditions."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.download_manager = RobustDownloadManager(temp_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_mirror_system_configuration(self):
        """Test mirror system configuration and initialization."""
        mirrors = [
            "https://mirror1.example.com/file.zip",
            "https://mirror2.example.com/file.zip"
        ]
        
        # Test mirror system implementation
        result = self.download_manager.implement_intelligent_mirror_system(mirrors)
        
        self.assertIsInstance(result, MirrorResult)
        self.assertIn(result.selected_mirror, mirrors)
        
        # Verify all mirrors are tracked
        for mirror in mirrors:
            self.assertIn(mirror, self.download_manager.mirror_health)
    
    def test_retry_configuration_limits(self):
        """Test retry configuration with various limits."""
        # Test minimum retries
        result = self.download_manager.execute_configurable_retries(max_retries=0)
        self.assertEqual(result.max_retries, 0)
        
        # Test maximum retries (should be capped at reasonable limit)
        result = self.download_manager.execute_configurable_retries(max_retries=10)
        self.assertEqual(result.max_retries, 10)
        
        # Test default retries
        result = self.download_manager.execute_configurable_retries()
        self.assertEqual(result.max_retries, 3)


if __name__ == '__main__':
    unittest.main()