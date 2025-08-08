"""
Debug parallel download issues.
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


def debug_parallel_downloads():
    """Debug parallel download functionality."""
    print("Debugging parallel download functionality...")
    
    # Setup
    temp_dir = Path(tempfile.mkdtemp())
    manager = RobustDownloadManager(temp_dir=temp_dir)
    
    # Create test data
    test_content = b"Test file content"
    test_hash = hashlib.sha256(test_content).hexdigest()
    print(f"Test hash: {test_hash}")
    
    # Create test requests
    requests = [
        DownloadRequest(
            url="https://example.com/file1.zip",
            destination_path=temp_dir / "file1.zip",
            expected_sha256=test_hash,
            description="Test file 1"
        )
    ]
    
    # Mock the HTTP response
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
        
        # Execute parallel downloads
        print("Executing parallel downloads...")
        result = manager.enable_parallel_downloads(requests)
        
        # Print detailed results
        print(f"Total downloads: {result.total_downloads}")
        print(f"Successful downloads: {result.successful_downloads}")
        print(f"Failed downloads: {result.failed_downloads}")
        
        for i, download_result in enumerate(result.download_results):
            print(f"Download {i+1}:")
            print(f"  URL: {download_result.url}")
            print(f"  Status: {download_result.status}")
            print(f"  File size: {download_result.file_size}")
            print(f"  Expected hash: {download_result.expected_hash}")
            print(f"  Calculated hash: {download_result.sha256_hash}")
            print(f"  Error: {download_result.error_message}")
            print()
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    debug_parallel_downloads()