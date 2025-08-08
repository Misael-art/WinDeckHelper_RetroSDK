"""
Simple test to verify parallel download functionality works.
"""

import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.robust_download_manager import (
    RobustDownloadManager,
    DownloadRequest,
    BandwidthConfig
)


def test_basic_parallel_functionality():
    """Test basic parallel download functionality."""
    print("Testing basic parallel download functionality...")
    
    # Setup
    temp_dir = Path(tempfile.mkdtemp())
    manager = RobustDownloadManager(temp_dir=temp_dir)
    
    # Create test data
    test_content = b"Test file content"
    test_hash = hashlib.sha256(test_content).hexdigest()
    
    # Create test requests
    requests = [
        DownloadRequest(
            url="https://example.com/file1.zip",
            destination_path=temp_dir / "file1.zip",
            expected_sha256=test_hash,
            description="Test file 1"
        ),
        DownloadRequest(
            url="https://example.com/file2.zip",
            destination_path=temp_dir / "file2.zip",
            expected_sha256=test_hash,
            description="Test file 2"
        )
    ]
    
    # Mock the HTTP response
    with patch('core.robust_download_manager.urllib.request.build_opener') as mock_build_opener:
        def create_mock_response():
            mock_response = MagicMock()
            mock_response.getcode.return_value = 200
            mock_response.headers.get.return_value = str(len(test_content))
            mock_response.read.side_effect = [test_content, b'']
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            return mock_response
        
        mock_opener = MagicMock()
        mock_opener.open.side_effect = lambda url: create_mock_response()
        mock_build_opener.return_value = mock_opener
        
        # Execute parallel downloads
        print("Executing parallel downloads...")
        result = manager.enable_parallel_downloads(requests)
        
        # Verify results
        print(f"Total downloads: {result.total_downloads}")
        print(f"Successful downloads: {result.successful_downloads}")
        print(f"Failed downloads: {result.failed_downloads}")
        print(f"Total size: {result.total_size_bytes} bytes")
        print(f"Average speed: {result.average_speed_mbps:.2f} Mbps")
        print(f"Bandwidth utilization: {result.bandwidth_utilization:.2f}%")
        
        assert result.total_downloads == 2
        assert result.successful_downloads == 2
        assert result.failed_downloads == 0
        
        print("✓ Basic parallel download functionality works!")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


def test_bandwidth_monitor():
    """Test bandwidth monitor functionality."""
    print("Testing bandwidth monitor...")
    
    from core.robust_download_manager import BandwidthMonitor
    
    monitor = BandwidthMonitor()
    
    # Test lifecycle
    assert not monitor.monitoring
    monitor.start_monitoring()
    assert monitor.monitoring
    
    # Test recording bytes
    monitor.record_bytes_downloaded(1024)
    assert monitor.total_bytes_downloaded == 1024
    
    # Test statistics
    stats = monitor.get_statistics()
    assert "total_bytes_downloaded" in stats
    assert stats["total_bytes_downloaded"] == 1024
    
    monitor.stop_monitoring()
    assert not monitor.monitoring
    
    print("✓ Bandwidth monitor works!")


if __name__ == "__main__":
    test_basic_parallel_functionality()
    test_bandwidth_monitor()
    print("\n✓ All simple tests passed!")