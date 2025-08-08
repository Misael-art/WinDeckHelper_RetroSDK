"""
Unit tests for Intelligent Storage Manager

Tests for storage analysis accuracy and functionality.
Requirements: 6.1, 6.2
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from core.intelligent_storage_manager import (
    IntelligentStorageManager,
    SpaceRequirement,
    DriveInfo,
    SelectiveInstallationResult,
    StoragePriority,
    DriveType
)


class TestIntelligentStorageManager(unittest.TestCase):
    """Test cases for IntelligentStorageManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage_manager = IntelligentStorageManager()
        
        # Mock drive data
        self.mock_drives = {
            'C:\\': DriveInfo(
                path='C:\\',
                total_space=500 * 1024**3,  # 500GB
                available_space=100 * 1024**3,  # 100GB
                used_space=400 * 1024**3,  # 400GB
                drive_type=DriveType.SSD,
                filesystem='NTFS',
                is_system_drive=True,
                performance_score=85.0
            ),
            'D:\\': DriveInfo(
                path='D:\\',
                total_space=1000 * 1024**3,  # 1TB
                available_space=800 * 1024**3,  # 800GB
                used_space=200 * 1024**3,  # 200GB
                drive_type=DriveType.HDD,
                filesystem='NTFS',
                is_system_drive=False,
                performance_score=70.0
            )
        }
    
    def test_calculate_space_requirements_basic(self):
        """Test basic space requirement calculation"""
        components = ['git', 'dotnet-sdk', 'java-jdk']
        
        requirements = self.storage_manager.calculate_space_requirements_before_installation(components)
        
        # Verify all components have requirements
        self.assertEqual(len(requirements), 3)
        for component in components:
            self.assertIn(component, requirements)
            req = requirements[component]
            self.assertIsInstance(req, SpaceRequirement)
            self.assertGreater(req.total_required, 0)
            self.assertGreater(req.download_size, 0)
            self.assertGreater(req.installation_size, 0)
    
    def test_calculate_space_requirements_unknown_component(self):
        """Test space requirement calculation for unknown component"""
        components = ['unknown-component-xyz']
        
        requirements = self.storage_manager.calculate_space_requirements_before_installation(components)
        
        self.assertEqual(len(requirements), 1)
        req = requirements['unknown-component-xyz']
        
        # Should use fallback values
        self.assertEqual(req.download_size, 50 * 1024 * 1024)  # 50MB
        self.assertEqual(req.installation_size, 200 * 1024 * 1024)  # 200MB
        self.assertEqual(req.temporary_size, 100 * 1024 * 1024)  # 100MB
        self.assertEqual(req.total_required, 350 * 1024 * 1024)  # 350MB
        self.assertEqual(req.priority, StoragePriority.MEDIUM)
    
    def test_component_priority_assignment(self):
        """Test that components get correct priority assignments"""
        critical_components = ['git', 'dotnet-sdk', 'java-jdk', 'vcpp-redist']
        high_components = ['powershell', 'nodejs', 'python']
        medium_components = ['some-other-tool']
        
        for component in critical_components:
            priority = self.storage_manager._get_component_priority(component)
            self.assertEqual(priority, StoragePriority.CRITICAL)
        
        for component in high_components:
            priority = self.storage_manager._get_component_priority(component)
            self.assertEqual(priority, StoragePriority.HIGH)
        
        for component in medium_components:
            priority = self.storage_manager._get_component_priority(component)
            self.assertEqual(priority, StoragePriority.MEDIUM)
    
    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    def test_analyze_available_space_across_drives(self, mock_disk_usage, mock_disk_partitions):
        """Test drive space analysis"""
        # Mock partition data
        mock_partition_c = Mock()
        mock_partition_c.mountpoint = 'C:\\'
        mock_partition_c.device = 'C:'
        mock_partition_c.fstype = 'NTFS'
        
        mock_partition_d = Mock()
        mock_partition_d.mountpoint = 'D:\\'
        mock_partition_d.device = 'D:'
        mock_partition_d.fstype = 'NTFS'
        
        mock_disk_partitions.return_value = [mock_partition_c, mock_partition_d]
        
        # Mock usage data
        def mock_usage_side_effect(path):
            if path == 'C:\\':
                mock_usage = Mock()
                mock_usage.total = 500 * 1024**3
                mock_usage.free = 100 * 1024**3
                mock_usage.used = 400 * 1024**3
                return mock_usage
            elif path == 'D:\\':
                mock_usage = Mock()
                mock_usage.total = 1000 * 1024**3
                mock_usage.free = 800 * 1024**3
                mock_usage.used = 200 * 1024**3
                return mock_usage
        
        mock_disk_usage.side_effect = mock_usage_side_effect
        
        drives = self.storage_manager.analyze_available_space_across_drives()
        
        self.assertEqual(len(drives), 2)
        self.assertIn('C:\\', drives)
        self.assertIn('D:\\', drives)
        
        # Verify C: drive info
        c_drive = drives['C:\\']
        self.assertEqual(c_drive.total_space, 500 * 1024**3)
        self.assertEqual(c_drive.available_space, 100 * 1024**3)
        self.assertTrue(c_drive.is_system_drive)
        
        # Verify D: drive info
        d_drive = drives['D:\\']
        self.assertEqual(d_drive.total_space, 1000 * 1024**3)
        self.assertEqual(d_drive.available_space, 800 * 1024**3)
        self.assertFalse(d_drive.is_system_drive)
    
    def test_selective_installation_sufficient_space(self):
        """Test selective installation when there's sufficient space"""
        components = ['git', 'nodejs', 'python']
        available_space = 10 * 1024**3  # 10GB
        
        result = self.storage_manager.enable_selective_installation_based_on_available_space(
            components, available_space
        )
        
        self.assertIsInstance(result, SelectiveInstallationResult)
        # With 10GB available, all small components should be recommended
        self.assertEqual(len(result.recommended_components), 3)
        self.assertEqual(len(result.skipped_components), 0)
        self.assertGreater(result.available_space_after, 0)
    
    def test_selective_installation_insufficient_space(self):
        """Test selective installation when space is limited"""
        components = ['git', 'dotnet-sdk', 'anaconda', 'java-jdk']
        available_space = 500 * 1024 * 1024  # 500MB - very limited
        
        result = self.storage_manager.enable_selective_installation_based_on_available_space(
            components, available_space
        )
        
        self.assertIsInstance(result, SelectiveInstallationResult)
        # With limited space, some components should be skipped
        self.assertLess(len(result.recommended_components), len(components))
        self.assertGreater(len(result.skipped_components), 0)
        
        # Critical components should be prioritized
        if result.recommended_components:
            # Git should be recommended as it's critical and smaller
            self.assertIn('git', result.recommended_components)
    
    def test_selective_installation_priority_ordering(self):
        """Test that selective installation respects priority ordering"""
        # Create components with different priorities
        components = ['git', 'nodejs', 'some-low-priority-tool']
        available_space = 300 * 1024 * 1024  # Limited space
        
        result = self.storage_manager.enable_selective_installation_based_on_available_space(
            components, available_space
        )
        
        # Git (critical) should be recommended before others
        if result.recommended_components:
            self.assertIn('git', result.recommended_components)
    
    def test_selective_installation_warnings(self):
        """Test that selective installation generates appropriate warnings"""
        components = ['git', 'dotnet-sdk', 'java-jdk']  # All critical components
        available_space = 100 * 1024 * 1024  # Very limited space
        
        result = self.storage_manager.enable_selective_installation_based_on_available_space(
            components, available_space
        )
        
        # Should have warnings about skipped critical components
        self.assertGreater(len(result.warnings), 0)
        
        # Check for specific warning types
        warning_text = ' '.join(result.warnings).lower()
        if result.skipped_components:
            # Should warn about high priority components being skipped
            has_priority_warning = any('priority' in warning.lower() for warning in result.warnings)
            self.assertTrue(has_priority_warning or len(result.skipped_components) == 0)
    
    def test_drive_type_detection(self):
        """Test drive type detection logic"""
        test_cases = [
            ('nvme0n1', DriveType.NVME),
            ('ssd-drive', DriveType.SSD),
            ('WD-HDD-1TB', DriveType.HDD),
            ('unknown-device', DriveType.UNKNOWN)
        ]
        
        for device, expected_type in test_cases:
            detected_type = self.storage_manager._detect_drive_type(device)
            self.assertEqual(detected_type, expected_type, f"Failed for device: {device}")
    
    def test_performance_score_calculation(self):
        """Test drive performance score calculation"""
        # Mock usage object
        mock_usage = Mock()
        mock_usage.total = 1000 * 1024**3  # 1TB
        mock_usage.free = 500 * 1024**3   # 500GB free (50%)
        
        # Test different drive types
        nvme_score = self.storage_manager._calculate_performance_score(DriveType.NVME, mock_usage)
        ssd_score = self.storage_manager._calculate_performance_score(DriveType.SSD, mock_usage)
        hdd_score = self.storage_manager._calculate_performance_score(DriveType.HDD, mock_usage)
        
        # NVME should have highest score, HDD lowest
        self.assertGreater(nvme_score, ssd_score)
        self.assertGreater(ssd_score, hdd_score)
        
        # All scores should be reasonable (0-100 range)
        for score in [nvme_score, ssd_score, hdd_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
    
    def test_system_drive_detection(self):
        """Test system drive detection"""
        if os.name == 'nt':  # Windows
            self.assertTrue(self.storage_manager._is_system_drive('C:\\'))
            self.assertFalse(self.storage_manager._is_system_drive('D:\\'))
        else:  # Unix-like
            self.assertTrue(self.storage_manager._is_system_drive('/'))
            self.assertFalse(self.storage_manager._is_system_drive('/home'))
    
    def test_caching_behavior(self):
        """Test that drive information is properly cached"""
        with patch.object(self.storage_manager, 'analyze_available_space_across_drives') as mock_analyze:
            mock_analyze.return_value = self.mock_drives
            
            # First call should trigger analysis
            result1 = self.storage_manager.analyze_available_space_across_drives()
            self.assertEqual(mock_analyze.call_count, 1)
            
            # Second call within cache duration should use cache
            result2 = self.storage_manager.analyze_available_space_across_drives()
            self.assertEqual(mock_analyze.call_count, 1)  # Should not increase
            
            # Results should be identical
            self.assertEqual(result1, result2)
    
    def test_space_requirement_caching(self):
        """Test that space requirements are cached"""
        component = 'git'
        
        # First calculation
        req1 = self.storage_manager._calculate_component_space_requirement(component)
        
        # Second calculation should use cache
        req2 = self.storage_manager._calculate_component_space_requirement(component)
        
        # Should be the same object (cached)
        self.assertIs(req1, req2)
        self.assertIn(component, self.storage_manager.space_requirements_cache)


if __name__ == '__main__':
    unittest.main()