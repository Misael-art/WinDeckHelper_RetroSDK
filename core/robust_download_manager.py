"""
Robust Download Manager with mandatory SHA256 verification and secure HTTPS-only downloads.

This module implements a secure download infrastructure that ensures integrity and security
for all download operations in the Environment Dev system.
"""

import hashlib
import os
import ssl
import time
import urllib.request
import urllib.error
import random
import threading
import queue
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from core.error_handler import EnvDevError


class DownloadError(EnvDevError):
    """Base exception for download-related errors."""
    pass


class HashVerificationError(DownloadError):
    """Exception raised when hash verification fails."""
    pass


class SecureConnectionError(DownloadError):
    """Exception raised when secure connection cannot be established."""
    pass


class MirrorError(DownloadError):
    """Exception raised when all mirrors fail."""
    pass


class RetryExhaustedError(DownloadError):
    """Exception raised when all retry attempts are exhausted."""
    pass


class DownloadStatus(Enum):
    """Status of download operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    HASH_VERIFICATION_FAILED = "hash_verification_failed"
    RETRYING = "retrying"
    MIRROR_FALLBACK = "mirror_fallback"


class MirrorStatus(Enum):
    """Status of mirror health."""
    HEALTHY = "healthy"
    SLOW = "slow"
    UNREACHABLE = "unreachable"
    FAILED = "failed"


@dataclass
class DownloadResult:
    """Result of a download operation."""
    url: str
    file_path: Path
    status: DownloadStatus
    file_size: int
    download_time: float
    sha256_hash: str
    expected_hash: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class DownloadRequest:
    """Request for downloading a file."""
    url: str
    destination_path: Path
    expected_sha256: str
    description: Optional[str] = None
    mirrors: Optional[List[str]] = None


@dataclass
class MirrorInfo:
    """Information about a mirror."""
    url: str
    status: MirrorStatus = MirrorStatus.HEALTHY
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    last_health_check: Optional[float] = None


@dataclass
class MirrorResult:
    """Result of mirror system operations."""
    selected_mirror: Optional[str]
    attempted_mirrors: List[str]
    mirror_health: Dict[str, MirrorInfo]
    fallback_used: bool
    total_attempts: int


@dataclass
class RetryResult:
    """Result of retry operations."""
    attempt_number: int
    max_retries: int
    backoff_delay: float
    success: bool
    error_message: Optional[str] = None
    retry_history: List[Dict[str, any]] = field(default_factory=list)


@dataclass
class DownloadProgress:
    """Progress information for a download."""
    url: str
    file_path: Path
    total_size: int
    downloaded_size: int
    progress_percentage: float
    download_speed_mbps: float
    estimated_time_remaining: float
    status: DownloadStatus
    start_time: float
    error_message: Optional[str] = None


@dataclass
class ParallelDownloadResult:
    """Result of parallel download operations."""
    total_downloads: int
    successful_downloads: int
    failed_downloads: int
    total_size_bytes: int
    total_download_time: float
    average_speed_mbps: float
    bandwidth_utilization: float
    download_results: List[DownloadResult]
    progress_history: List[DownloadProgress] = field(default_factory=list)
    integrity_summary: Optional[Dict[str, any]] = None


@dataclass
class BandwidthConfig:
    """Configuration for bandwidth management."""
    max_concurrent_downloads: int = 4
    max_bandwidth_mbps: Optional[float] = None
    bandwidth_per_download_mbps: Optional[float] = None
    adaptive_bandwidth: bool = True
    priority_downloads: List[str] = field(default_factory=list)


class RobustDownloadManager:
    """
    Robust Download Manager with mandatory SHA256 verification and secure HTTPS-only downloads.
    
    This class implements secure download infrastructure that ensures integrity and security
    for all download operations in the Environment Dev system.
    """
    
    def __init__(self, security_manager=None, temp_dir: Optional[Path] = None, max_retries: int = 3, bandwidth_config: Optional[BandwidthConfig] = None):
        """
        Initialize the Robust Download Manager.
        
        Args:
            security_manager: Security manager for auditing
            temp_dir: Directory for temporary files during download
            max_retries: Maximum number of retry attempts (default: 3)
            bandwidth_config: Configuration for bandwidth management
        """
        self.security_manager = security_manager
        self.temp_dir = temp_dir or Path.cwd() / "temp_downloads"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure secure SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Download statistics
        self.download_history: List[DownloadResult] = []
        
        # Mirror and retry configuration
        self.max_retries = max_retries
        self.mirror_health: Dict[str, MirrorInfo] = {}
        self.health_check_interval = 300  # 5 minutes
        self.mirror_timeout = 10  # seconds
        self._lock = threading.Lock()
        
        # Parallel download configuration
        self.bandwidth_config = bandwidth_config or BandwidthConfig()
        self.active_downloads: Dict[str, DownloadProgress] = {}
        self.progress_callbacks: List[Callable[[DownloadProgress], None]] = []
        self.bandwidth_monitor = BandwidthMonitor()
        self._progress_lock = threading.Lock()
    
    def download_with_mandatory_hash_verification(
        self, 
        url: str, 
        expected_sha256: str,
        destination_path: Optional[Path] = None
    ) -> DownloadResult:
        """
        Download a file with mandatory SHA256 hash verification.
        
        Args:
            url: URL to download from (must be HTTPS)
            expected_sha256: Expected SHA256 hash for verification
            destination_path: Where to save the file (optional)
            
        Returns:
            DownloadResult with download status and details
            
        Raises:
            SecureConnectionError: If URL is not HTTPS or connection fails
            HashVerificationError: If hash verification fails
            DownloadError: For other download-related errors
        """
        # Validate HTTPS-only requirement
        if not self._is_secure_url(url):
            raise SecureConnectionError(f"Only HTTPS URLs are allowed. Got: {url}")
        
        # Generate destination path if not provided
        if destination_path is None:
            filename = self._extract_filename_from_url(url)
            destination_path = self.temp_dir / filename
        
        start_time = time.time()
        temp_path = destination_path.with_suffix(destination_path.suffix + ".tmp")
        
        try:
            # Download file to temporary location
            file_size = self._download_file_securely(url, temp_path)
            
            # Calculate SHA256 hash
            calculated_hash = self._calculate_sha256(temp_path)
            
            # Verify hash
            if not self._verify_hash(calculated_hash, expected_sha256):
                temp_path.unlink(missing_ok=True)
                result = DownloadResult(
                    url=url,
                    file_path=destination_path,
                    status=DownloadStatus.HASH_VERIFICATION_FAILED,
                    file_size=file_size,
                    download_time=time.time() - start_time,
                    sha256_hash=calculated_hash,
                    expected_hash=expected_sha256,
                    error_message=f"Hash verification failed. Expected: {expected_sha256}, Got: {calculated_hash}"
                )
                self.download_history.append(result)
                raise HashVerificationError(result.error_message)
            
            # Move from temp to final location
            temp_path.rename(destination_path)
            
            # Create successful result
            result = DownloadResult(
                url=url,
                file_path=destination_path,
                status=DownloadStatus.COMPLETED,
                file_size=file_size,
                download_time=time.time() - start_time,
                sha256_hash=calculated_hash,
                expected_hash=expected_sha256
            )
            
            self.download_history.append(result)
            return result
            
        except Exception as e:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            
            # Create failed result
            result = DownloadResult(
                url=url,
                file_path=destination_path,
                status=DownloadStatus.FAILED,
                file_size=0,
                download_time=time.time() - start_time,
                sha256_hash="",
                expected_hash=expected_sha256,
                error_message=str(e)
            )
            
            self.download_history.append(result)
            
            if isinstance(e, (SecureConnectionError, HashVerificationError)):
                raise
            else:
                raise DownloadError(f"Download failed: {str(e)}") from e
    
    def download_multiple_with_verification(
        self, 
        requests: List[DownloadRequest]
    ) -> List[DownloadResult]:
        """
        Download multiple files with hash verification.
        
        Args:
            requests: List of download requests
            
        Returns:
            List of download results
        """
        results = []
        
        for request in requests:
            try:
                result = self.download_with_mandatory_hash_verification(
                    url=request.url,
                    expected_sha256=request.expected_sha256,
                    destination_path=request.destination_path
                )
                results.append(result)
            except (DownloadError, HashVerificationError, SecureConnectionError) as e:
                # Create failed result for this request
                result = DownloadResult(
                    url=request.url,
                    file_path=request.destination_path,
                    status=DownloadStatus.FAILED,
                    file_size=0,
                    download_time=0.0,
                    sha256_hash="",
                    expected_hash=request.expected_sha256,
                    error_message=str(e)
                )
                results.append(result)
        
        return results
    
    def verify_existing_file(self, file_path: Path, expected_sha256: str) -> bool:
        """
        Verify an existing file's SHA256 hash.
        
        Args:
            file_path: Path to the file to verify
            expected_sha256: Expected SHA256 hash
            
        Returns:
            True if hash matches, False otherwise
        """
        if not file_path.exists():
            return False
        
        try:
            calculated_hash = self._calculate_sha256(file_path)
            return self._verify_hash(calculated_hash, expected_sha256)
        except Exception:
            return False
    
    def generate_integrity_summary(self, results: List[DownloadResult]) -> Dict[str, any]:
        """
        Generate integrity summary for download results.
        
        Args:
            results: List of download results
            
        Returns:
            Dictionary with integrity summary
        """
        total_downloads = len(results)
        successful = sum(1 for r in results if r.status == DownloadStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)
        hash_failed = sum(1 for r in results if r.status == DownloadStatus.HASH_VERIFICATION_FAILED)
        
        total_size = sum(r.file_size for r in results if r.status == DownloadStatus.COMPLETED)
        total_time = sum(r.download_time for r in results)
        
        return {
            "total_downloads": total_downloads,
            "successful": successful,
            "failed": failed,
            "hash_verification_failed": hash_failed,
            "success_rate": (successful / total_downloads * 100) if total_downloads > 0 else 0,
            "total_size_bytes": total_size,
            "total_download_time": total_time,
            "average_speed_mbps": (total_size / (1024 * 1024) / total_time) if total_time > 0 else 0,
            "failed_downloads": [r for r in results if r.status != DownloadStatus.COMPLETED]
        }
    
    def _is_secure_url(self, url: str) -> bool:
        """Check if URL uses HTTPS protocol."""
        parsed = urlparse(url)
        return parsed.scheme.lower() == 'https'
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        if not filename or '.' not in filename:
            # Generate filename based on URL hash if no proper filename found
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"download_{url_hash}.bin"
        
        return filename
    
    def _download_file_securely(self, url: str, destination: Path) -> int:
        """
        Download file securely using HTTPS with SSL verification.
        
        Args:
            url: HTTPS URL to download from
            destination: Path to save the file
            
        Returns:
            Size of downloaded file in bytes
            
        Raises:
            SecureConnectionError: If secure connection fails
            DownloadError: If download fails
        """
        try:
            # Create secure HTTPS handler
            https_handler = urllib.request.HTTPSHandler(context=self.ssl_context)
            opener = urllib.request.build_opener(https_handler)
            
            # Set user agent to identify our application
            opener.addheaders = [('User-Agent', 'EnvironmentDev-RobustDownloadManager/1.0')]
            
            # Open connection and download
            with opener.open(url) as response:
                # Verify we got a successful response
                if response.getcode() != 200:
                    raise DownloadError(f"HTTP {response.getcode()}: {response.reason}")
                
                # Download file in chunks
                total_size = 0
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        total_size += len(chunk)
                
                return total_size
                
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLError):
                raise SecureConnectionError(f"SSL verification failed: {e.reason}")
            else:
                raise SecureConnectionError(f"Connection failed: {e.reason}")
        except Exception as e:
            raise DownloadError(f"Download failed: {str(e)}")
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _verify_hash(self, calculated: str, expected: str) -> bool:
        """
        Verify that calculated hash matches expected hash.
        
        Args:
            calculated: Calculated hash
            expected: Expected hash
            
        Returns:
            True if hashes match (case-insensitive), False otherwise
        """
        return calculated.lower() == expected.lower()
    
    def get_download_history(self) -> List[DownloadResult]:
        """Get history of all download operations."""
        return self.download_history.copy()
    
    def clear_download_history(self) -> None:
        """Clear download history."""
        self.download_history.clear()
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary download files."""
        if self.temp_dir.exists():
            for temp_file in self.temp_dir.glob("*.tmp"):
                try:
                    temp_file.unlink()
                except Exception:
                    pass  # Ignore errors during cleanup
    
    def implement_intelligent_mirror_system(self, mirrors: List[str]) -> MirrorResult:
        """
        Implement intelligent mirror system with health monitoring and selection.
        
        Args:
            mirrors: List of mirror URLs
            
        Returns:
            MirrorResult with mirror selection and health information
        """
        with self._lock:
            # Initialize mirror health if not exists
            for mirror in mirrors:
                if mirror not in self.mirror_health:
                    self.mirror_health[mirror] = MirrorInfo(url=mirror)
            
            # Update health checks if needed
            current_time = time.time()
            for mirror in mirrors:
                mirror_info = self.mirror_health[mirror]
                if (mirror_info.last_health_check is None or 
                    current_time - mirror_info.last_health_check > self.health_check_interval):
                    self._check_mirror_health(mirror)
            
            # Select best mirror based on health and performance
            selected_mirror = self._select_best_mirror(mirrors)
            
            return MirrorResult(
                selected_mirror=selected_mirror,
                attempted_mirrors=[],
                mirror_health=self.mirror_health.copy(),
                fallback_used=False,
                total_attempts=0
            )
    
    def execute_configurable_retries(self, max_retries: int = 3) -> RetryResult:
        """
        Configure retry system with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            RetryResult with retry configuration
        """
        return RetryResult(
            attempt_number=0,
            max_retries=max_retries,
            backoff_delay=0.0,
            success=False,
            retry_history=[]
        )
    
    def implement_exponential_backoff(self, attempt: int) -> int:
        """
        Calculate exponential backoff delay for retry attempts.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0
        
        # Base delay of 1 second, exponentially increased with jitter
        base_delay = 2 ** (attempt - 1)
        jitter = random.uniform(0.1, 0.5)  # Add randomness to prevent thundering herd
        
        return int(base_delay + jitter)
    
    def download_with_mirror_fallback_and_retry(
        self,
        url: str,
        expected_sha256: str,
        destination_path: Optional[Path] = None,
        mirrors: Optional[List[str]] = None,
        max_retries: Optional[int] = None
    ) -> DownloadResult:
        """
        Download with intelligent mirror fallback and configurable retry system.
        
        Args:
            url: Primary URL to download from
            expected_sha256: Expected SHA256 hash for verification
            destination_path: Where to save the file (optional)
            mirrors: List of mirror URLs (optional)
            max_retries: Maximum retry attempts (optional, uses instance default)
            
        Returns:
            DownloadResult with download status and details
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Prepare URL list (primary + mirrors)
        all_urls = [url]
        if mirrors:
            all_urls.extend(mirrors)
        
        # Generate destination path if not provided
        if destination_path is None:
            filename = self._extract_filename_from_url(url)
            destination_path = self.temp_dir / filename
        
        retry_history = []
        last_error = None
        
        # Try each URL with retries
        for url_index, current_url in enumerate(all_urls):
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    # Calculate backoff delay
                    if attempt > 0:
                        delay = self.implement_exponential_backoff(attempt)
                        time.sleep(delay)
                        retry_history.append({
                            "attempt": attempt,
                            "url": current_url,
                            "delay": delay,
                            "timestamp": time.time()
                        })
                    
                    # Attempt download
                    result = self.download_with_mandatory_hash_verification(
                        current_url, expected_sha256, destination_path
                    )
                    
                    # Update mirror health on success
                    if current_url in self.mirror_health:
                        with self._lock:
                            mirror_info = self.mirror_health[current_url]
                            mirror_info.success_count += 1
                            mirror_info.last_used = time.time()
                            mirror_info.status = MirrorStatus.HEALTHY
                    
                    # Add retry information to result
                    result.error_message = f"Success after {len(retry_history)} retries"
                    return result
                    
                except (DownloadError, HashVerificationError, SecureConnectionError) as e:
                    last_error = e
                    
                    # Update mirror health on failure
                    if current_url in self.mirror_health:
                        with self._lock:
                            mirror_info = self.mirror_health[current_url]
                            mirror_info.failure_count += 1
                            if mirror_info.failure_count > mirror_info.success_count:
                                mirror_info.status = MirrorStatus.FAILED
                    
                    # If this was the last attempt for this URL, try next URL
                    if attempt >= max_retries:
                        break
        
        # All URLs and retries exhausted
        start_time = time.time()
        result = DownloadResult(
            url=url,
            file_path=destination_path,
            status=DownloadStatus.FAILED,
            file_size=0,
            download_time=time.time() - start_time,
            sha256_hash="",
            expected_hash=expected_sha256,
            error_message=f"All mirrors and retries exhausted. Last error: {str(last_error)}"
        )
        
        self.download_history.append(result)
        raise RetryExhaustedError(result.error_message)
    
    def _check_mirror_health(self, mirror_url: str) -> None:
        """
        Check health of a specific mirror.
        
        Args:
            mirror_url: URL of the mirror to check
        """
        try:
            start_time = time.time()
            
            # Create a simple HEAD request to check mirror availability
            request = urllib.request.Request(mirror_url, method='HEAD')
            request.add_header('User-Agent', 'EnvironmentDev-RobustDownloadManager/1.0')
            
            with urllib.request.urlopen(request, timeout=self.mirror_timeout, context=self.ssl_context) as response:
                response_time = time.time() - start_time
                
                mirror_info = self.mirror_health[mirror_url]
                mirror_info.response_time = response_time
                mirror_info.last_health_check = time.time()
                
                # Determine status based on response time
                if response_time < 2.0:
                    mirror_info.status = MirrorStatus.HEALTHY
                elif response_time < 5.0:
                    mirror_info.status = MirrorStatus.SLOW
                else:
                    mirror_info.status = MirrorStatus.UNREACHABLE
                    
        except Exception:
            # Mirror is unreachable
            mirror_info = self.mirror_health[mirror_url]
            mirror_info.status = MirrorStatus.UNREACHABLE
            mirror_info.last_health_check = time.time()
    
    def _select_best_mirror(self, mirrors: List[str]) -> Optional[str]:
        """
        Select the best mirror based on health and performance metrics.
        
        Args:
            mirrors: List of available mirrors
            
        Returns:
            URL of the best mirror, or None if no healthy mirrors
        """
        healthy_mirrors = []
        
        for mirror in mirrors:
            mirror_info = self.mirror_health.get(mirror)
            if mirror_info and mirror_info.status in [MirrorStatus.HEALTHY, MirrorStatus.SLOW]:
                healthy_mirrors.append((mirror, mirror_info))
        
        if not healthy_mirrors:
            return mirrors[0] if mirrors else None  # Fallback to first mirror
        
        # Sort by success rate and response time
        def mirror_score(mirror_tuple):
            mirror_url, mirror_info = mirror_tuple
            success_rate = (mirror_info.success_count / 
                          max(1, mirror_info.success_count + mirror_info.failure_count))
            response_penalty = mirror_info.response_time * 0.1  # Small penalty for slow mirrors
            return success_rate - response_penalty
        
        healthy_mirrors.sort(key=mirror_score, reverse=True)
        return healthy_mirrors[0][0]
    
    def get_mirror_health_report(self) -> Dict[str, Dict[str, any]]:
        """
        Get comprehensive mirror health report.
        
        Returns:
            Dictionary with mirror health information
        """
        with self._lock:
            report = {}
            for mirror_url, mirror_info in self.mirror_health.items():
                total_attempts = mirror_info.success_count + mirror_info.failure_count
                success_rate = (mirror_info.success_count / max(1, total_attempts)) * 100
                
                report[mirror_url] = {
                    "status": mirror_info.status.value,
                    "response_time": mirror_info.response_time,
                    "success_count": mirror_info.success_count,
                    "failure_count": mirror_info.failure_count,
                    "success_rate": success_rate,
                    "last_used": mirror_info.last_used,
                    "last_health_check": mirror_info.last_health_check
                }
            
            return report
    
    def enable_parallel_downloads(self, requests: List[DownloadRequest], progress_callback: Optional[Callable[[DownloadProgress], None]] = None) -> ParallelDownloadResult:
        """
        Enable parallel download system for multiple components.
        
        Args:
            requests: List of download requests
            progress_callback: Optional callback for progress updates
            
        Returns:
            ParallelDownloadResult with comprehensive download statistics
        """
        if progress_callback:
            self.progress_callbacks.append(progress_callback)
        
        start_time = time.time()
        download_futures: Dict[Future, DownloadRequest] = {}
        results: List[DownloadResult] = []
        
        # Initialize progress tracking
        for request in requests:
            progress = DownloadProgress(
                url=request.url,
                file_path=request.destination_path,
                total_size=0,
                downloaded_size=0,
                progress_percentage=0.0,
                download_speed_mbps=0.0,
                estimated_time_remaining=0.0,
                status=DownloadStatus.PENDING,
                start_time=time.time()
            )
            
            with self._progress_lock:
                self.active_downloads[request.url] = progress
        
        # Start bandwidth monitoring
        self.bandwidth_monitor.start_monitoring()
        
        try:
            # Execute parallel downloads with bandwidth management
            with ThreadPoolExecutor(max_workers=self.bandwidth_config.max_concurrent_downloads) as executor:
                # Submit download tasks
                for request in requests:
                    future = executor.submit(self._download_with_progress_tracking, request)
                    download_futures[future] = request
                
                # Collect results as they complete
                for future in as_completed(download_futures):
                    request = download_futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update progress to completed
                        with self._progress_lock:
                            if request.url in self.active_downloads:
                                progress = self.active_downloads[request.url]
                                progress.status = result.status
                                progress.progress_percentage = 100.0 if result.status == DownloadStatus.COMPLETED else 0.0
                                self._notify_progress_callbacks(progress)
                        
                    except Exception as e:
                        # Create failed result
                        failed_result = DownloadResult(
                            url=request.url,
                            file_path=request.destination_path,
                            status=DownloadStatus.FAILED,
                            file_size=0,
                            download_time=0.0,
                            sha256_hash="",
                            expected_hash=request.expected_sha256,
                            error_message=str(e)
                        )
                        results.append(failed_result)
                        
                        # Update progress to failed
                        with self._progress_lock:
                            if request.url in self.active_downloads:
                                progress = self.active_downloads[request.url]
                                progress.status = DownloadStatus.FAILED
                                progress.error_message = str(e)
                                self._notify_progress_callbacks(progress)
        
        finally:
            # Stop bandwidth monitoring
            self.bandwidth_monitor.stop_monitoring()
            
            # Clear active downloads
            with self._progress_lock:
                self.active_downloads.clear()
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.status == DownloadStatus.COMPLETED)
        failed = len(results) - successful
        total_size = sum(r.file_size for r in results if r.status == DownloadStatus.COMPLETED)
        average_speed = (total_size / (1024 * 1024) / total_time) if total_time > 0 else 0
        
        # Generate integrity summary
        integrity_summary = self.generate_integrity_summary(results)
        
        # Create parallel download result
        parallel_result = ParallelDownloadResult(
            total_downloads=len(requests),
            successful_downloads=successful,
            failed_downloads=failed,
            total_size_bytes=total_size,
            total_download_time=total_time,
            average_speed_mbps=average_speed,
            bandwidth_utilization=self.bandwidth_monitor.get_utilization_percentage(),
            download_results=results,
            integrity_summary=integrity_summary
        )
        
        return parallel_result
    
    def _download_with_progress_tracking(self, request: DownloadRequest) -> DownloadResult:
        """
        Download a file with progress tracking and bandwidth management.
        
        Args:
            request: Download request
            
        Returns:
            DownloadResult with download status and details
        """
        # Update progress to in progress
        with self._progress_lock:
            if request.url in self.active_downloads:
                progress = self.active_downloads[request.url]
                progress.status = DownloadStatus.IN_PROGRESS
                self._notify_progress_callbacks(progress)
        
        # Apply bandwidth throttling if configured
        if self.bandwidth_config.bandwidth_per_download_mbps:
            self._apply_bandwidth_throttling(request.url)
        
        try:
            # Use existing download method with progress updates
            result = self._download_with_progress_updates(request)
            return result
            
        except Exception as e:
            # Update progress on error
            with self._progress_lock:
                if request.url in self.active_downloads:
                    progress = self.active_downloads[request.url]
                    progress.status = DownloadStatus.FAILED
                    progress.error_message = str(e)
                    self._notify_progress_callbacks(progress)
            raise
    
    def _download_with_progress_updates(self, request: DownloadRequest) -> DownloadResult:
        """
        Download file with real-time progress updates.
        
        Args:
            request: Download request
            
        Returns:
            DownloadResult with download status and details
        """
        if not self._is_secure_url(request.url):
            raise SecureConnectionError(f"Only HTTPS URLs are allowed. Got: {request.url}")
        
        start_time = time.time()
        temp_path = request.destination_path.with_suffix(request.destination_path.suffix + ".tmp")
        
        try:
            # Use the existing download method for simplicity and reliability
            result = self.download_with_mandatory_hash_verification(
                url=request.url,
                expected_sha256=request.expected_sha256,
                destination_path=request.destination_path
            )
            
            # Update progress to completed
            with self._progress_lock:
                if request.url in self.active_downloads:
                    progress = self.active_downloads[request.url]
                    progress.total_size = result.file_size
                    progress.downloaded_size = result.file_size
                    progress.progress_percentage = 100.0
                    progress.status = result.status
                    self._notify_progress_callbacks(progress)
            
            return result
            
        except Exception as e:
            # Create failed result
            result = DownloadResult(
                url=request.url,
                file_path=request.destination_path,
                status=DownloadStatus.FAILED,
                file_size=0,
                download_time=time.time() - start_time,
                sha256_hash="",
                expected_hash=request.expected_sha256,
                error_message=str(e)
            )
            
            # Update progress on error
            with self._progress_lock:
                if request.url in self.active_downloads:
                    progress = self.active_downloads[request.url]
                    progress.status = DownloadStatus.FAILED
                    progress.error_message = str(e)
                    self._notify_progress_callbacks(progress)
            
            return result
    
    def _update_download_progress(self, url: str, downloaded_size: int, total_size: int, start_time: float) -> None:
        """
        Update download progress for a specific URL.
        
        Args:
            url: URL being downloaded
            downloaded_size: Number of bytes downloaded
            total_size: Total file size in bytes
            start_time: Download start time
        """
        with self._progress_lock:
            if url in self.active_downloads:
                progress = self.active_downloads[url]
                progress.downloaded_size = downloaded_size
                
                # Calculate progress percentage
                if total_size > 0:
                    progress.progress_percentage = (downloaded_size / total_size) * 100
                
                # Calculate download speed
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed_bps = downloaded_size / elapsed_time
                    progress.download_speed_mbps = speed_bps / (1024 * 1024)
                    
                    # Estimate time remaining
                    if progress.download_speed_mbps > 0 and total_size > 0:
                        remaining_bytes = total_size - downloaded_size
                        progress.estimated_time_remaining = remaining_bytes / speed_bps
                
                self._notify_progress_callbacks(progress)
    
    def _notify_progress_callbacks(self, progress: DownloadProgress) -> None:
        """
        Notify all registered progress callbacks.
        
        Args:
            progress: Current download progress
        """
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception:
                # Ignore callback errors to prevent disrupting downloads
                pass
    
    def _apply_bandwidth_throttling(self, url: str) -> None:
        """
        Apply bandwidth throttling for a specific download.
        
        Args:
            url: URL being downloaded
        """
        if self.bandwidth_config.bandwidth_per_download_mbps:
            # Simple throttling implementation
            # In a real implementation, this would control the download rate
            pass
    
    def add_progress_callback(self, callback: Callable[[DownloadProgress], None]) -> None:
        """
        Add a progress callback function.
        
        Args:
            callback: Function to call with progress updates
        """
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[DownloadProgress], None]) -> None:
        """
        Remove a progress callback function.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_active_downloads(self) -> Dict[str, DownloadProgress]:
        """
        Get currently active downloads.
        
        Returns:
            Dictionary of active downloads by URL
        """
        with self._progress_lock:
            return self.active_downloads.copy()
    
    def get_bandwidth_utilization(self) -> float:
        """
        Get current bandwidth utilization percentage.
        
        Returns:
            Bandwidth utilization as percentage (0-100)
        """
        return self.bandwidth_monitor.get_utilization_percentage()


class BandwidthMonitor:
    """
    Monitor and manage bandwidth utilization for parallel downloads.
    """
    
    def __init__(self):
        """Initialize the bandwidth monitor."""
        self.monitoring = False
        self.start_time = 0.0
        self.total_bytes_downloaded = 0
        self.peak_bandwidth_mbps = 0.0
        self.current_bandwidth_mbps = 0.0
        self._lock = threading.Lock()
    
    def start_monitoring(self) -> None:
        """Start bandwidth monitoring."""
        try:
            with self._lock:
                self.monitoring = True
                self.start_time = time.time()
                self.total_bytes_downloaded = 0
                self.peak_bandwidth_mbps = 0.0
                self.current_bandwidth_mbps = 0.0
        except Exception:
            # Ignore errors in monitoring to prevent blocking downloads
            pass
    
    def stop_monitoring(self) -> None:
        """Stop bandwidth monitoring."""
        try:
            with self._lock:
                self.monitoring = False
        except Exception:
            # Ignore errors in monitoring to prevent blocking downloads
            pass
    
    def record_bytes_downloaded(self, bytes_count: int) -> None:
        """
        Record bytes downloaded for bandwidth calculation.
        
        Args:
            bytes_count: Number of bytes downloaded
        """
        try:
            with self._lock:
                if self.monitoring:
                    self.total_bytes_downloaded += bytes_count
                    
                    # Calculate current bandwidth
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time > 0:
                        self.current_bandwidth_mbps = (self.total_bytes_downloaded / elapsed_time) / (1024 * 1024)
                        self.peak_bandwidth_mbps = max(self.peak_bandwidth_mbps, self.current_bandwidth_mbps)
        except Exception:
            # Ignore errors in monitoring to prevent blocking downloads
            pass
    
    def get_utilization_percentage(self) -> float:
        """
        Get bandwidth utilization as percentage.
        
        Returns:
            Utilization percentage (0-100)
        """
        try:
            with self._lock:
                # This is a simplified calculation
                # In a real implementation, this would compare against available bandwidth
                return min(100.0, self.current_bandwidth_mbps * 10)  # Assume 10 Mbps baseline
        except Exception:
            # Return 0 on error to prevent blocking
            return 0.0
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get bandwidth statistics.
        
        Returns:
            Dictionary with bandwidth statistics
        """
        try:
            with self._lock:
                elapsed_time = time.time() - self.start_time if self.monitoring else 0
                
                return {
                    "total_bytes_downloaded": self.total_bytes_downloaded,
                    "elapsed_time_seconds": elapsed_time,
                    "average_bandwidth_mbps": self.current_bandwidth_mbps,
                    "peak_bandwidth_mbps": self.peak_bandwidth_mbps,
                    "utilization_percentage": self.get_utilization_percentage()
                }
        except Exception:
            # Return empty stats on error
            return {
                "total_bytes_downloaded": 0,
                "elapsed_time_seconds": 0,
                "average_bandwidth_mbps": 0.0,
                "peak_bandwidth_mbps": 0.0,
                "utilization_percentage": 0.0
            }