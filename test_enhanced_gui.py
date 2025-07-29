#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Enhanced GUI with Real-time Feedback
Tests the dashboard and notification system functionality
"""

import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def test_notification_system():
    """Test the notification system independently"""
    print("Testing Notification System...")
    
    try:
        import tkinter as tk
        from env_dev.gui.notification_system import (
            NotificationCenter, NotificationLevel, NotificationCategory
        )
        
        # Create test window
        root = tk.Tk()
        root.title("Notification System Test")
        root.geometry("400x300")
        
        # Create notification center
        notification_center = NotificationCenter(root)
        
        # Test different notification types
        def run_tests():
            print("  - Testing info notification...")
            notification_center.info("Test Info", "This is a test info message")
            
            root.after(1000, lambda: notification_center.success("Test Success", "This is a test success message"))
            root.after(2000, lambda: notification_center.warning("Test Warning", "This is a test warning message"))
            root.after(3000, lambda: notification_center.error("Test Error", "This is a test error message"))
            
            # Test progress tracking
            root.after(4000, test_progress_tracking)
        
        def test_progress_tracking():
            print("  - Testing progress tracking...")
            tracker = notification_center.start_progress_tracking("test_operation", 5, "Test Operation")
            
            def update_progress(step):
                if step <= 5:
                    notification_center.update_progress("test_operation", step, f"Step {step} of 5")
                    root.after(500, lambda: update_progress(step + 1))
                else:
                    notification_center.complete_progress_tracking("test_operation", True, "Test completed successfully")
                    root.after(2000, root.quit)  # Close after 2 seconds
            
            update_progress(1)
        
        # Start tests
        root.after(500, run_tests)
        
        # Run for a limited time
        root.after(10000, root.quit)  # Auto-close after 10 seconds
        root.mainloop()
        
        print("  ✓ Notification system test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Notification system test failed: {e}")
        return False

def test_dashboard_components():
    """Test dashboard components"""
    print("Testing Dashboard Components...")
    
    try:
        from env_dev.gui.dashboard_gui import StatusCard, SystemStatus, StatusInfo
        import tkinter as tk
        
        # Create test window
        root = tk.Tk()
        root.title("Dashboard Components Test")
        root.geometry("400x300")
        
        # Test StatusCard
        card = StatusCard(root, "Test Card")
        card.pack(fill="x", padx=10, pady=10)
        
        # Test status updates
        def test_status_updates():
            print("  - Testing status card updates...")
            
            # Test different status types
            statuses = [
                StatusInfo(SystemStatus.HEALTHY, "System is healthy", "All systems operational"),
                StatusInfo(SystemStatus.WARNING, "Minor issues detected", "Some components need attention"),
                StatusInfo(SystemStatus.ERROR, "Critical error", "Immediate action required", True),
                StatusInfo(SystemStatus.UNKNOWN, "Status unknown", "Checking system...")
            ]
            
            def update_status(index):
                if index < len(statuses):
                    card.update_status(statuses[index])
                    root.after(1500, lambda: update_status(index + 1))
                else:
                    root.after(1000, root.quit)
            
            update_status(0)
        
        root.after(500, test_status_updates)
        root.after(8000, root.quit)  # Auto-close
        root.mainloop()
        
        print("  ✓ Dashboard components test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Dashboard components test failed: {e}")
        return False

def test_enhanced_dashboard():
    """Test the enhanced dashboard"""
    print("Testing Enhanced Dashboard...")
    
    try:
        # Mock the managers to avoid dependency issues
        with patch('env_dev.gui.enhanced_dashboard.DiagnosticManager'), \
             patch('env_dev.gui.enhanced_dashboard.InstallationManager'), \
             patch('env_dev.gui.enhanced_dashboard.DownloadManager'), \
             patch('env_dev.gui.enhanced_dashboard.OrganizationManager'), \
             patch('env_dev.gui.enhanced_dashboard.RecoveryManager'), \
             patch('env_dev.gui.enhanced_dashboard.load_all_components') as mock_load:
            
            # Mock component data
            mock_load.return_value = {
                "TestComponent1": {
                    "name": "Test Component 1",
                    "category": "Development Tools",
                    "description": "A test component for development",
                    "version": "1.0.0"
                },
                "TestComponent2": {
                    "name": "Test Component 2", 
                    "category": "System Tools",
                    "description": "Another test component",
                    "version": "2.0.0"
                }
            }
            
            from env_dev.gui.enhanced_dashboard import EnhancedDashboard
            
            # Create dashboard instance
            dashboard = EnhancedDashboard()
            
            # Test basic functionality
            def test_dashboard_features():
                print("  - Testing dashboard initialization...")
                
                # Test notification system integration
                dashboard.notification_center.info("Test", "Dashboard test started")
                
                # Test refresh functionality
                print("  - Testing refresh functionality...")
                dashboard.refresh_status()
                
                # Test component loading
                print("  - Testing component loading...")
                dashboard.load_components()
                
                # Close after tests
                dashboard.after(3000, dashboard.quit)
            
            dashboard.after(1000, test_dashboard_features)
            dashboard.after(5000, dashboard.quit)  # Auto-close
            
            # Run dashboard briefly
            dashboard.mainloop()
            
        print("  ✓ Enhanced dashboard test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Enhanced dashboard test failed: {e}")
        return False

def test_progress_dialog():
    """Test the progress dialog"""
    print("Testing Progress Dialog...")
    
    try:
        import tkinter as tk
        from env_dev.gui.notification_system import NotificationCenter
        from env_dev.gui.enhanced_dashboard import RealTimeProgressDialog
        
        # Create test window
        root = tk.Tk()
        root.title("Progress Dialog Test")
        root.geometry("300x200")
        
        # Create notification center
        notification_center = NotificationCenter(root)
        
        def test_progress():
            print("  - Testing progress dialog...")
            
            # Create progress dialog
            progress_dialog = RealTimeProgressDialog(
                root,
                "Test Operation",
                "test_op",
                notification_center
            )
            
            # Simulate progress updates
            def update_progress(step):
                if step <= 10:
                    progress = (step / 10) * 100
                    step_desc = f"Processing step {step} of 10"
                    details = f"Executing operation {step}"
                    
                    progress_dialog.update_progress(progress, step_desc, details)
                    root.after(300, lambda: update_progress(step + 1))
                else:
                    progress_dialog.operation_completed(True, "Test operation completed successfully")
                    root.after(2000, lambda: progress_dialog.destroy())
                    root.after(2500, root.quit)
            
            update_progress(1)
        
        root.after(1000, test_progress)
        root.after(8000, root.quit)  # Auto-close
        root.mainloop()
        
        print("  ✓ Progress dialog test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Progress dialog test failed: {e}")
        return False

def test_integration():
    """Test integration between components"""
    print("Testing Component Integration...")
    
    try:
        # Test that all components can be imported together
        from env_dev.gui.dashboard_gui import StatusCard, SystemStatus, StatusInfo
        from env_dev.gui.notification_system import (
            NotificationCenter, NotificationLevel, NotificationCategory
        )
        from env_dev.gui.enhanced_dashboard import EnhancedDashboard
        
        print("  - All components imported successfully")
        
        # Test that notification system can be created
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        notification_center = NotificationCenter(root)
        print("  - Notification center created successfully")
        
        # Test notification creation
        notification_id = notification_center.info("Integration Test", "Testing component integration")
        print(f"  - Notification created with ID: {notification_id}")
        
        # Clean up
        root.destroy()
        
        print("  ✓ Integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced GUI Test Suite")
    print("=" * 60)
    
    tests = [
        ("Integration Test", test_integration),
        ("Notification System", test_notification_system),
        ("Dashboard Components", test_dashboard_components),
        ("Progress Dialog", test_progress_dialog),
        ("Enhanced Dashboard", test_enhanced_dashboard),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Enhanced GUI is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())