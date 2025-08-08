"""
Unit tests for RobustDownloadManager with focus on download security and verification.

This test suite validates the secure download infrastructure implementation
according to requirements 4.1 and 4.2.
"""

import hashlib
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from urllib.error import URLError

from core.robust_download_manager import (
    RobustDownloadManager,
    DownloadError,
    HashVerificationError,
    SecureConnectionError,
    DownloadStatus,
    DownloadResult,
    DownloadRequest
)


class TestRobustDownloadManager(unittest.TestCase):
    """Test cases for RobustDownloadManager security and verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = RobustDownloadManager(temp_dir=self.temp_dir)
        
        # Sample test data
        self.test_content = b"Test file content for download verification"
        self.test_sha256 = hashlib.sha256(self.test_content).hexdigest()
        self.test_url = "https://example.com/test-file.zip"
        self.invalid_sha256 = "invalid_hash_value"
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        for file in self.temp_dir.rglob("*"):
            if file.is_file():
                file.unlink()
        self.temp_dir.rmdir()
    
    def test_https_only_requirement(self):
        """Test that only HTTPS URLs are accepted."""
        http_url = "http://example.com/file.zip"
        
        with self.assertRaises(SecureConnectionError) as context:
            self.manager.download_with_mandatory_hash_verification(
                http_url, self.test_sha256
            )
        
        self.assertIn("Only HTTPS URLs are allowed", str(context.exception))
    
    def test_ftp_url_rejection(self):
        """Test that FTP URLs are rejected."""
        ftp_url = "ftp://example.com/file.zip"
        
        with self.assertRaises(SecureConnectionError):
            self.manager.download_with_mandatory_hash_verification(
                ftp_url, self.test_sha256
            )
    
    @patch('urllib.request.build_opener')
    def test_successful_download_with_valid_hash(self, mock_build_opener):
        """Test successful download with valid SHA256 hash."""
        # Mock the download response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.read.side_effect = [self.test_content, b'']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        
        mock_opener = Mock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # Perform download
        result = self.manager.download_with_mandatory_hash_verification(
            self.test_url, self.test_sha256
        )
        
        # Verify result
        self.assertEqual(result.status, DownloadStatus.COMPLETED)
        self.assertEqual(result.url, self.test_url)
        self.assertEqual(result.sha256_hash, self.test_sha256)
        self.assertEqual(result.expected_hash, self.test_sha256)
        self.assertIsNone(result.error_message)
        self.assertGreater(result.file_size, 0)
        self.assertGreater(result.download_time, 0)
    
    @patch('urllib.request.build_opener')
    def test_hash_verification_failure(self, mock_build_opener):
        """Test hash verification failure scenario."""
        # Mock the download response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.read.side_effect = [self.test_content, b'']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        
        mock_opener = Mock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # Use wrong hash to trigger verification failure
        wrong_hash = "wrong_hash_value"
        
        with self.assertRaises(HashVerificationError) as context:
            self.manager.download_with_mandatory_hash_verification(
                self.test_url, wrong_hash
            )
        
        self.assertIn("Hash verification failed", str(context.exception))
        
        # Verify that failed download is recorded in history
        history = self.manager.get_download_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].status, DownloadStatus.HASH_VERIFICATION_FAILED)
    
    @patch('urllib.request.build_opener')
    def test_ssl_verification_failure(self, mock_build_opener):
        """Test SSL verification failure handling."""
        # Mock SSL error
        ssl_error = ssl.SSLError("Certificate verification failed")
        url_error = URLError(ssl_error)
        
        mock_opener = Mock()
        mock_opener.open.side_effect = url_error
        mock_build_opener.return_value = mock_opener
        
        with self.assertRaises(SecureConnectionError) as context:
            self.manager.download_with_mandatory_hash_verification(
                self.test_url, self.test_sha256
            )
        
        self.assertIn("SSL verification failed", str(context.exception))
    
    @patch('urllib.request.build_opener')
    def test_http_error_handling(self, mock_build_opener):
        """Test HTTP error response handling."""
        # Mock HTTP 404 response
        mock_response = Mock()
        mock_response.getcode.return_value = 404
        mock_response.reason = "Not Found"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        
        mock_opener = Mock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        with self.assertRaises(DownloadError) as context:
            self.manager.download_with_mandatory_hash_verification(
                self.test_url, self.test_sha256
            )
        
        self.assertIn("HTTP 404", str(context.exception))
    
    def test_verify_existing_file_success(self):
        """Test verification of existing file with correct hash."""
        # Create test file
        test_file = self.temp_dir / "test_file.txt"
        test_file.write_bytes(self.test_content)
        
        # Verify file
        result = self.manager.verify_existing_file(test_file, self.test_sha256)
        self.assertTrue(result)
    
    def test_verify_existing_file_failure(self):
        """Test verification of existing file with incorrect hash."""
        # Create test file
        test_file = self.temp_dir / "test_file.txt"
        test_file.write_bytes(self.test_content)
        
        # Verify file with wrong hash
        result = self.manager.verify_existing_file(test_file, "wrong_hash")
        self.assertFalse(result)
    
    def test_verify_nonexistent_file(self):
        """Test verification of non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.txt"
        
        result = self.manager.verify_existing_file(nonexistent_file, self.test_sha256)
        self.assertFalse(result)
    
    @patch('urllib.request.build_opener')
    def test_multiple_downloads_with_verification(self, mock_build_opener):
        """Test downloading multiple files with verification."""
        # Mock successful downloads
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.read.side_effect = [self.test_content, b'']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        
        mock_opener = Mock()
        mock_opener.open.return_value = mock_response
        mock_build_opener.return_value = mock_opener
        
        # Create download requests
        requests = [
            DownloadRequest(
                url="https://example.com/file1.zip",
                destination_path=self.temp_dir / "file1.zip",
                expected_sha256=self.test_sha256,
                description="Test file 1"
            ),
            DownloadRequest(
                url="https://example.com/file2.zip",
                destination_path=self.temp_dir / "file2.zip",
                expected_sha256=self.test_sha256,
                description="Test file 2"
            )
        ]
        
        # Perform downloads
        results = self.manager.download_multiple_with_verification(requests)
        
        # Verify results
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result.status, DownloadStatus.COMPLETED)
            self.assertEqual(result.sha256_hash, self.test_sha256)
    
    @patch('urllib.request.build_opener')
    def test_integrity_summary_generation(self, mock_build_opener):
        """Test generation of integrity summary for downloads."""
        # Mock mixed success/failure responses
        def mock_open_side_effect(url):
            if "success" in url:
                mock_response = Mock()
                mock_response.getcode.return_value = 200
                mock_response.read.side_effect = [self.test_content, b'']
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=None)
                return mock_response
            else:
                raise URLError("Connection failed")
        
        mock_opener = Mock()
        mock_opener.open.side_effect = mock_open_side_effect
        mock_build_opener.return_value = mock_opener
        
        # Create mixed download requests
        requests = [
            DownloadRequest(
                url="https://example.com/success1.zip",
                destination_path=self.temp_dir / "success1.zip",
                expected_sha256=self.test_sha256
            ),
            DownloadRequest(
                url="https://example.com/fail1.zip",
                destination_path=self.temp_dir / "fail1.zip",
                expected_sha256=self.test_sha256
            )
        ]
        
        # Perform downloads
        results = self.manager.download_multiple_with_verification(requests)
        
        # Generate integrity summary
        summary = self.manager.generate_integrity_summary(results)
        
        # Verify summary
        self.assertEqual(summary["total_downloads"], 2)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["hash_verification_failed"], 0)
        self.assertEqual(summary["success_rate"], 50.0)
        self.assertEqual(len(summary["failed_downloads"]), 1)
    
    def test_filename_extraction_from_url(self):
        """Test filename extraction from URL."""
        # Test normal URL with filename
        filename = self.manager._extract_filename_from_url("https://example.com/test.zip")
        self.assertEqual(filename, "test.zip")
        
        # Test URL without proper filename
        filename = self.manager._extract_filename_from_url("https://example.com/")
        self.assertTrue(filename.startswith("download_"))
        self.assertTrue(filename.endswith(".bin"))
    
    def test_secure_ssl_context_configuration(self):
        """Test that SSL context is configured securely."""
        self.assertTrue(self.manager.ssl_context.check_hostname)
        self.assertEqual(self.manager.ssl_context.verify_mode, ssl.CERT_REQUIRED)
    
    def test_temp_file_cleanup_on_failure(self):
        """Test that temporary files are cleaned up on download failure."""
        with patch('urllib.request.build_opener') as mock_build_opener:
            # Mock download failure
            mock_opener = Mock()
            mock_opener.open.side_effect = URLError("Connection failed")
            mock_build_opener.return_value = mock_opener
            
            # Attempt download
            with self.assertRaises(DownloadError):
                self.manager.download_with_mandatory_hash_verification(
                    self.test_url, self.test_sha256
                )
            
            # Verify no temp files remain
            temp_files = list(self.temp_dir.glob("*.tmp"))
            self.assertEqual(len(temp_files), 0)
    
    def test_download_history_tracking(self):
        """Test that download history is properly tracked."""
        # Initially empty
        self.assertEqual(len(self.manager.get_download_history()), 0)
        
        # Test with failed download
        with patch('urllib.request.build_opener') as mock_build_opener:
            mock_opener = Mock()
            mock_opener.open.side_effect = URLError("Connection failed")
            mock_build_opener.return_value = mock_opener
            
            with self.assertRaises(DownloadError):
                self.manager.download_with_mandatory_hash_verification(
                    self.test_url, self.test_sha256
                )
        
        # Verify history contains failed download
        history = self.manager.get_download_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].status, DownloadStatus.FAILED)
        
        # Test history clearing
        self.manager.clear_download_history()
        self.assertEqual(len(self.manager.get_download_history()), 0)
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        # Create some temp files
        temp_file1 = self.temp_dir / "test1.tmp"
        temp_file2 = self.temp_dir / "test2.tmp"
        temp_file1.write_text("temp content 1")
        temp_file2.write_text("temp content 2")
        
        # Verify files exist
        self.assertTrue(temp_file1.exists())
        self.assertTrue(temp_file2.exists())
        
        # Cleanup
        self.manager.cleanup_temp_files()
        
        # Verify files are removed
        self.assertFalse(temp_file1.exists())
        self.assertFalse(temp_file2.exists())


class TestDownloadDataModels(unittest.TestCase):
    """Test cases for download data models."""
    
    def test_download_result_creation(self):
        """Test DownloadResult data model creation."""
        result = DownloadResult(
            url="https://example.com/test.zip",
            file_path=Path("/tmp/test.zip"),
            status=DownloadStatus.COMPLETED,
            file_size=1024,
            download_time=2.5,
            sha256_hash="abc123",
            expected_hash="abc123"
        )
        
        self.assertEqual(result.url, "https://example.com/test.zip")
        self.assertEqual(result.status, DownloadStatus.COMPLETED)
        self.assertEqual(result.file_size, 1024)
        self.assertEqual(result.download_time, 2.5)
        self.assertIsNone(result.error_message)
    
    def test_download_request_creation(self):
        """Test DownloadRequest data model creation."""
        request = DownloadRequest(
            url="https://example.com/test.zip",
            destination_path=Path("/tmp/test.zip"),
            expected_sha256="abc123",
            description="Test download"
        )
        
        self.assertEqual(request.url, "https://example.com/test.zip")
        self.assertEqual(request.expected_sha256, "abc123")
        self.assertEqual(request.description, "Test download")


if __name__ == '__main__':
    unittest.main()