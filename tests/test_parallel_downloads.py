"""
Tests for parallel download capabilities in RobustDownloadManager.

This module contains comprehensive tests for parallel download functionality,
bandwidth management, progress tracking, and performance validation.
"""

import hashlib
import os
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from core.robust_download_manager import (
    RobustDownloadManager,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    DownloadProgress,
    ParallelDownloadResult,
    BandwidthConfig,
    BandwidthMonitor,
    DownloadError,
    HashVerificationError
)


class TestParallelDownloads:
    """Test parallel download functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.bandwidth_config = BandwidthConfig(
            max_concurrent_downloads=3,
            max_bandwidth_mbps=10.0,
            adaptive_bandwidth=True
        )
        self.manager = RobustDownloadManager(
            temp_dir=self.temp_dir,
            bandwidth_config=self.bandwidth_config
        )
        
        # Mock data for testing
        self.test_content = b"Test file content for parallel download testing"
        self.test_hash = hashlib.sha256(self.test_content).hexdigest()
        
        # Create test download requests
        self.test_requests = [
            DownloadRequest(
                url="https://example.com/file1.zip",
                destination_path=self.temp_dir / "file1.zip",
                expected_sha256=self.test_hash,
                description="Test file 1"
            ),
            DownloadRequest(
                url="https://example.com/file2.zip",
                destination_path=self.temp_dir / "file2.zip",
                expected_sha256=self.test_hash,
                description="Test file 2"
            ),
            DownloadRequest(
                url="https://example.com/file3.zip",
                destination_path=self.temp_dir / "file3.zip",
                expected_sha256=self.test_hash,
                description="Test file 3"
            )
        ]
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _mock_successful_download(self, url, destination):
        """Mock a successful download."""
        with open(destination, 'wb') as f:
            f.write(self.test_content)
        return len(self.test_content)
    
    @patch('core.robust_download_manager.urllib.request.build_opener')
    def test_enable_parallel_downloads_success(self, mock_build_opener):
        """Test successful parallel downloads."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.headers.get.return_value = str(len(self.test_content))
        mock_response.read.side_effect = [self.test_content, b'']
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # Execute parallel downloads
        result = self.manager.enable_parallel_downloads(self.test_requests)
        
        # Verify results
        assert isinstance(result, ParallelDownloadResult)
        assert result.total_downloads == 3
        assert result.successful_downloads == 3
        assert result.failed_downloads == 0
        assert result.total_size_bytes == len(self.test_content) * 3
        assert result.average_speed_mbps >= 0
        assert result.bandwidth_utilization >= 0
        assert len(result.download_results) == 3
        assert result.integrity_summary is not None
        
        # Verify all downloads completed successfully
        for download_result in result.download_results:
            assert download_result.status == DownloadStatus.COMPLETED
            assert download_result.sha256_hash == self.test_hash
    
    @patch('core.robust_download_manager.urllib.request.build_opener')
    def test_parallel_downloads_with_failures(self, mock_build_opener):
        """Test parallel downloads with some failures."""
        # Mock responses - first succeeds, second fails, third succeeds
        def mock_open_side_effect(url):
            if "file2" in url:
                raise Exception("Network error")
            
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.headers.get.return_value = str(len(self.test_content))
            mock_response.read.side_effect = [self.test_content, b'']
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            return mock_response
        
        mock_opener = MagicMock()
        mock_opener.open.side_effect = mock_open_side_effect
        mock_build_opener.return_value = mock_opener
        
        # Execute parallel downloads
        result = self.manager.enable_parallel_downloads(self.test_requests)
        
        # Verify results
        assert result.total_downloads == 3
        assert result.successful_downloads == 2
        assert result.failed_downloads == 1
        assert len(result.download_results) == 3
        
        # Verify specific results
        failed_results = [r for r in result.download_results if r.status == DownloadStatus.FAILED]
        assert len(failed_results) == 1
        assert "file2" in failed_results[0].url
    
    def test_progress_tracking(self):
        """Test progress tracking during parallel downloads."""
        progress_updates = []
        
        def progress_callback(progress: DownloadProgress):
            progress_updates.append(progress)
        
        # Add progress callback
        self.manager.add_progress_callback(progress_callback)
        
        with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
            # Mock the HTTP response with chunked data
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.headers.get.return_value = str(len(self.test_content))
            
            # Simulate chunked reading
            chunks = [self.test_content[:10], self.test_content[10:20], self.test_content[20:]]
            mock_response.read.side_effect = chunks + [b'']
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            
            mock_opener = MagicMock()
            mock_opener.open.return_value = mock_response
            mock_build_opener.return_value = mock_opener
            
            # Execute download with single request for simpler testing
            result = self.manager.enable_parallel_downloads([self.test_requests[0]])
        
        # Verify progress updates were received
        assert len(progress_updates) > 0
        
        # Verify progress data structure
        for progress in progress_updates:
            assert isinstance(progress, DownloadProgress)
            assert progress.url == self.test_requests[0].url
            assert progress.progress_percentage >= 0
            assert progress.download_speed_mbps >= 0
    
    def test_bandwidth_management(self):
        """Test bandwidth management configuration."""
        # Test with different bandwidth configurations
        configs = [
            BandwidthConfig(max_concurrent_downloads=2, max_bandwidth_mbps=5.0),
            BandwidthConfig(max_concurrent_downloads=4, bandwidth_per_download_mbps=2.0),
            BandwidthConfig(max_concurrent_downloads=1, adaptive_bandwidth=False)
        ]
        
        for config in configs:
            manager = RobustDownloadManager(temp_dir=self.temp_dir, bandwidth_config=config)
            
            # Verify configuration is applied
            assert manager.bandwidth_config.max_concurrent_downloads == config.max_concurrent_downloads
            assert manager.bandwidth_config.max_bandwidth_mbps == config.max_bandwidth_mbps
            assert manager.bandwidth_config.adaptive_bandwidth == config.adaptive_bandwidth
    
    def test_integrity_summary_generation(self):
        """Test integrity summary generation before installation."""
        # Create mock download results
        successful_result = DownloadResult(
            url="https://example.com/file1.zip",
            file_path=self.temp_dir / "file1.zip",
            status=DownloadStatus.COMPLETED,
            file_size=1024,
            download_time=2.5,
            sha256_hash=self.test_hash,
            expected_hash=self.test_hash
        )
        
        failed_result = DownloadResult(
            url="https://example.com/file2.zip",
            file_path=self.temp_dir / "file2.zip",
            status=DownloadStatus.FAILED,
            file_size=0,
            download_time=1.0,
            sha256_hash="",
            expected_hash=self.test_hash,
            error_message="Network error"
        )
        
        hash_failed_result = DownloadResult(
            url="https://example.com/file3.zip",
            file_path=self.temp_dir / "file3.zip",
            status=DownloadStatus.HASH_VERIFICATION_FAILED,
            file_size=512,
            download_time=1.5,
            sha256_hash="wrong_hash",
            expected_hash=self.test_hash,
            error_message="Hash verification failed"
        )
        
        results = [successful_result, failed_result, hash_failed_result]
        
        # Generate integrity summary
        summary = self.manager.generate_integrity_summary(results)
        
        # Verify summary contents
        assert summary["total_downloads"] == 3
        assert summary["successful"] == 1
        assert summary["failed"] == 1
        assert summary["hash_verification_failed"] == 1
        assert summary["success_rate"] == 33.33333333333333  # 1/3 * 100
        assert summary["total_size_bytes"] == 1024  # Only successful download
        assert summary["total_download_time"] == 5.0  # Sum of all download times
        assert len(summary["failed_downloads"]) == 2  # Failed and hash failed
    
    def test_concurrent_download_limit(self):
        """Test that concurrent download limit is respected."""
        # Create many download requests
        many_requests = []
        for i in range(10):
            request = DownloadRequest(
                url=f"https://example.com/file{i}.zip",
                destination_path=self.temp_dir / f"file{i}.zip",
                expected_sha256=self.test_hash,
                description=f"Test file {i}"
            )
            many_requests.append(request)
        
        # Set low concurrent limit
        config = BandwidthConfig(max_concurrent_downloads=2)
        manager = RobustDownloadManager(temp_dir=self.temp_dir, bandwidth_config=config)
        
        # Track concurrent downloads
        max_concurrent = 0
        current_concurrent = 0
        concurrent_lock = threading.Lock()
        
        def track_concurrent_start():
            nonlocal max_concurrent, current_concurrent
            with concurrent_lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
        
        def track_concurrent_end():
            nonlocal current_concurrent
            with concurrent_lock:
                current_concurrent -= 1
        
        with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
            def mock_open_side_effect(url):
                track_concurrent_start()
                time.sleep(0.1)  # Simulate download time
                track_concurrent_end()
                
                mock_response = MagicMock()
                mock_response.getcode.return_value = 200
                mock_response.headers.get.return_value = str(len(self.test_content))
                mock_response.read.side_effect = [self.test_content, b'']
                mock_response.__enter__.return_value = mock_response
                mock_response.__exit__.return_value = None
                return mock_response
            
            mock_opener = MagicMock()
            mock_opener.open.side_effect = mock_open_side_effect
            mock_build_opener.return_value = mock_opener
            
            # Execute parallel downloads
            result = manager.enable_parallel_downloads(many_requests)
        
        # Verify concurrent limit was respected
        assert max_concurrent <= config.max_concurrent_downloads


class TestBandwidthMonitor:
    """Test bandwidth monitoring functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.monitor = BandwidthMonitor()
    
    def test_bandwidth_monitoring_lifecycle(self):
        """Test bandwidth monitoring start/stop lifecycle."""
        # Initially not monitoring
        assert not self.monitor.monitoring
        
        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor.monitoring
        assert self.monitor.start_time > 0
        assert self.monitor.total_bytes_downloaded == 0
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        assert not self.monitor.monitoring
    
    def test_bytes_recording(self):
        """Test recording of downloaded bytes."""
        self.monitor.start_monitoring()
        
        # Record some bytes
        self.monitor.record_bytes_downloaded(1024)
        self.monitor.record_bytes_downloaded(2048)
        
        # Verify total
        assert self.monitor.total_bytes_downloaded == 3072
        
        # Verify bandwidth calculation
        stats = self.monitor.get_statistics()
        assert stats["total_bytes_downloaded"] == 3072
        assert stats["average_bandwidth_mbps"] >= 0
    
    def test_utilization_calculation(self):
        """Test bandwidth utilization calculation."""
        self.monitor.start_monitoring()
        
        # Record bytes and check utilization
        self.monitor.record_bytes_downloaded(1024 * 1024)  # 1 MB
        utilization = self.monitor.get_utilization_percentage()
        
        assert 0 <= utilization <= 100
    
    def test_statistics_generation(self):
        """Test bandwidth statistics generation."""
        self.monitor.start_monitoring()
        
        # Record some activity
        self.monitor.record_bytes_downloaded(1024)
        time.sleep(0.1)  # Small delay for time calculation
        
        stats = self.monitor.get_statistics()
        
        # Verify statistics structure
        required_keys = [
            "total_bytes_downloaded",
            "elapsed_time_seconds",
            "average_bandwidth_mbps",
            "peak_bandwidth_mbps",
            "utilization_percentage"
        ]
        
        for key in required_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))
            assert stats[key] >= 0


class TestPerformanceAndReliability:
    """Test performance and reliability of parallel downloads."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = RobustDownloadManager(temp_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_performance_with_large_file_list(self):
        """Test performance with large number of files."""
        # Create many download requests
        num_files = 50
        requests = []
        test_content = b"Test content" * 100  # Larger content
        test_hash = hashlib.sha256(test_content).hexdigest()
        
        for i in range(num_files):
            request = DownloadRequest(
                url=f"https://example.com/file{i}.zip",
                destination_path=self.temp_dir / f"file{i}.zip",
                expected_sha256=test_hash,
                description=f"Performance test file {i}"
            )
            requests.append(request)
        
        with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
            # Mock fast responses
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.headers.get.return_value = str(len(test_content))
            mock_response.read.side_effect = [test_content, b'']
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            
            mock_opener = MagicMock()
            mock_opener.open.return_value = mock_response
            mock_build_opener.return_value = mock_opener
            
            # Measure performance
            start_time = time.time()
            result = self.manager.enable_parallel_downloads(requests)
            end_time = time.time()
            
            # Verify performance
            total_time = end_time - start_time
            assert total_time < 30  # Should complete within 30 seconds
            assert result.successful_downloads == num_files
            assert result.average_speed_mbps > 0
    
    def test_reliability_with_network_errors(self):
        """Test reliability when network errors occur."""
        # Create requests
        requests = []
        test_content = b"Test content"
        test_hash = hashlib.sha256(test_content).hexdigest()
        
        for i in range(10):
            request = DownloadRequest(
                url=f"https://example.com/file{i}.zip",
                destination_path=self.temp_dir / f"file{i}.zip",
                expected_sha256=test_hash,
                description=f"Reliability test file {i}"
            )
            requests.append(request)
        
        with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
            # Mock intermittent failures
            call_count = 0
            
            def mock_open_side_effect(url):
                nonlocal call_count
                call_count += 1
                
                # Fail every 3rd request
                if call_count % 3 == 0:
                    raise Exception("Simulated network error")
                
                mock_response = MagicMock()
                mock_response.getcode.return_value = 200
                mock_response.headers.get.return_value = str(len(test_content))
                mock_response.read.side_effect = [test_content, b'']
                mock_response.__enter__.return_value = mock_response
                mock_response.__exit__.return_value = None
                return mock_response
            
            mock_opener = MagicMock()
            mock_opener.open.side_effect = mock_open_side_effect
            mock_build_opener.return_value = mock_opener
            
            # Execute downloads
            result = self.manager.enable_parallel_downloads(requests)
            
            # Verify system handled errors gracefully
            assert result.total_downloads == 10
            assert result.successful_downloads > 0  # Some should succeed
            assert result.failed_downloads > 0  # Some should fail
            assert result.successful_downloads + result.failed_downloads == 10
    
    def test_memory_usage_with_concurrent_downloads(self):
        """Test memory usage doesn't grow excessively with concurrent downloads."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many concurrent downloads
        requests = []
        test_content = b"Test content" * 1000  # Larger content
        test_hash = hashlib.sha256(test_content).hexdigest()
        
        for i in range(20):
            request = DownloadRequest(
                url=f"https://example.com/file{i}.zip",
                destination_path=self.temp_dir / f"file{i}.zip",
                expected_sha256=test_hash,
                description=f"Memory test file {i}"
            )
            requests.append(request)
        
        with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.headers.get.return_value = str(len(test_content))
            mock_response.read.side_effect = [test_content, b'']
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            
            mock_opener = MagicMock()
            mock_opener.open.return_value = mock_response
            mock_build_opener.return_value = mock_opener
            
            # Execute downloads
            result = self.manager.enable_parallel_downloads(requests)
            
            # Check memory usage after downloads
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024
            assert result.successful_downloads == 20


if __name__ == "__main__":
    pytest.main([__file__])