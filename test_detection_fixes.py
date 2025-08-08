#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify the fixes for detection system issues.
"""

import sys
import os
import logging

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Import the modules directly
import detection_engine
import yaml_component_detection

def test_yaml_component_detection():
    """Test YAML component detection fixes."""
    print("Testing YAML Component Detection...")
    
    # Create YAML component detection strategy
    yaml_detector = yaml_component_detection.YAMLComponentDetectionStrategy()
    
    # Test detection of a retro devkit component
    print("Testing retro devkit detection...")
    detected_apps = yaml_detector.detect_applications(["GBDK"])
    
    # Check if project components are correctly filtered out
    project_component_detected = False
    for app in detected_apps:
        # Check if the detected path is within the project directory
        if (app.install_path and 
            os.path.abspath(app.install_path).startswith(os.path.abspath(os.path.dirname(__file__)))):
            project_component_detected = True
            break
    
    if project_component_detected:
        print("❌ Project component incorrectly detected as user installation")
    else:
        print("✅ Project components correctly filtered out")
    
    return not project_component_detected

def test_detection_engine():
    """Test detection engine fixes."""
    print("\nTesting Detection Engine...")
    
    # Create detection engine
    engine = detection_engine.DetectionEngine(use_cache=False, enable_updates=False)
    
    # Test Python detection deduplication
    print("Testing Python detection deduplication...")
    result = engine.detect_all_applications(["python"])
    
    # Count Python-related detections
    python_count = 0
    for app in result.applications:
        if 'python' in app.name.lower():
            python_count += 1
    
    if python_count <= 1:
        print("✅ Python deduplication working correctly")
    else:
        print(f"❌ Multiple Python entries detected: {python_count}")
    
    # Test project component filtering
    print("Testing project component filtering...")
    project_components_filtered = True
    for app in result.applications:
        # Check if any detected application has paths within the project directory
        if ((app.install_path and 
             os.path.abspath(app.install_path).startswith(os.path.abspath(os.path.dirname(__file__)))) or
            (app.executable_path and 
             os.path.abspath(app.executable_path).startswith(os.path.abspath(os.path.dirname(__file__))))):
            project_components_filtered = False
            break
    
    if project_components_filtered:
        print("✅ Project components correctly filtered out")
    else:
        print("❌ Project components not filtered out")
    
    return python_count <= 1 and project_components_filtered

def main():
    """Main test function."""
    print("Testing detection system fixes...\n")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    yaml_test_passed = test_yaml_component_detection()
    engine_test_passed = test_detection_engine()
    
    print("\n" + "="*50)
    if yaml_test_passed and engine_test_passed:
        print("✅ All tests passed! Fixes are working correctly.")
    else:
        print("❌ Some tests failed. Please review the fixes.")
        if not yaml_test_passed:
            print("  - YAML component detection fixes need review")
        if not engine_test_passed:
            print("  - Detection engine fixes need review")
    
    print("="*50)

if __name__ == "__main__":
    main()