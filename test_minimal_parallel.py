"""
Minimal test for parallel download functionality.
"""

import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.robust_download_manager import (
    RobustDownloadManager,
    DownloadRequest,
    BandwidthConfig
)


def test_minimal_parallel():
    """Test minimal parallel download functionality."""
    print("Testing minimal parallel download...")
    
    # Setup
    temp_dir = Path(tempfile.mkdtemp())
    manager = RobustDownloadManager(temp_dir=temp_dir)
    
    # Create test data
    test_content = b"Test file content"
    test_hash = hashlib.sha256(test_content).hexdigest()
    
    # Create single test request
    request = DownloadRequest(
        url="https://example.com/file1.zip",
        destination_path=temp_dir / "file1.zip",
        expected_sha256=test_hash,
        description="Test file 1"
    )
    
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
        result = manager.enable_parallel_downloads([request])
        
        # Verify results
        print(f"✓ Download completed successfully")
        print(f"  Total downloads: {result.total_downloads}")
        print(f"  Successful: {result.successful_downloads}")
        print(f"  Failed: {result.failed_downloads}")
        
        assert result.total_downloads == 1
        assert result.successful_downloads == 1
        assert result.failed_downloads == 0
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print("✓ Minimal parallel download test passed!")


if __name__ == "__main__":
    test_minimal_parallel()