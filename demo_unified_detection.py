#!/usr/bin/env python3
"""
Demonstration of the UnifiedDetectionEngine.

This script shows the unified detection engine in action,
detecting applications and runtimes on the system.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment_dev_deep_evaluation.core.config import ConfigurationManager
from environment_dev_deep_evaluation.detection.unified_engine import UnifiedDetectionEngine


def main():
    """Demonstrate the unified detection engine."""
    print("=" * 80)
    print("UnifiedDetectionEngine Demonstration")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize configuration manager
        print("1. Initializing configuration manager...")
        config_manager = ConfigurationManager()
        
        # Initialize unified detection engine
        print("2. Initializing unified detection engine...")
        detection_engine = UnifiedDetectionEngine(config_manager)
        detection_engine.initialize()
        
        print("3. Performing registry scan...")
        registry_apps = detection_engine.scan_registry_installations()
        print(f"   Found {len(registry_apps)} applications in registry")
        
        # Show first few registry applications
        if registry_apps:
            print("   Sample registry applications:")
            for i, app in enumerate(registry_apps[:5]):
                print(f"     {i+1}. {app.name} v{app.version} by {app.publisher}")
        
        print()
        print("4. Detecting essential runtimes...")
        runtime_results = detection_engine.detect_essential_runtimes()
        
        detected_runtimes = [r for r in runtime_results if r.detected]
        print(f"   Detected {len(detected_runtimes)} out of {len(runtime_results)} essential runtimes")
        
        for runtime in runtime_results:
            status = "✓ DETECTED" if runtime.detected else "✗ NOT FOUND"
            version_info = f" (v{runtime.version})" if runtime.version else ""
            print(f"     {runtime.runtime_name}: {status}{version_info}")
        
        print()
        print("5. Performing comprehensive detection...")
        all_apps_result = detection_engine.detect_all_applications()
        print(f"   Overall detection successful: {all_apps_result.detected}")
        print(f"   Detection confidence: {all_apps_result.confidence.value}")
        print(f"   Detection method: {all_apps_result.method.value}")
        
        print()
        print("6. Generating comprehensive report...")
        report = detection_engine.generate_comprehensive_report()
        
        print(f"   Report ID: {report.report_id}")
        print(f"   Generation time: {report.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("   Summary:")
        for key, value in report.detection_summary.items():
            if not key.endswith("_time") and not key.endswith("_used"):
                print(f"     {key.replace('_', ' ').title()}: {value}")
        
        print()
        print("7. Testing runtime validation...")
        
        # Test validation for each configured runtime
        for runtime_key, runtime_config in detection_engine._essential_runtimes.items():
            runtime_name = runtime_config["name"]
            validation_result = detection_engine.validate_runtime_installation(runtime_name)
            
            status = "✓ VALID" if validation_result.success else "✗ INVALID"
            print(f"   {runtime_name}: {status}")
            if not validation_result.success:
                print(f"     Reason: {validation_result.message}")
        
        print()
        print("=" * 80)
        print("Demonstration completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())