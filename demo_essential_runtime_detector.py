#!/usr/bin/env python3
"""
Demonstration of the EssentialRuntimeDetector.

This script shows the essential runtime detector in action,
detecting all 8 essential runtimes on the system.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.essential_runtime_detector import EssentialRuntimeDetector


def main():
    """Demonstrate the essential runtime detector."""
    print("=" * 80)
    print("EssentialRuntimeDetector Demonstration")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize essential runtime detector
        print("1. Initializing essential runtime detector...")
        detector = EssentialRuntimeDetector()
        
        print("2. Detecting all essential runtimes...")
        print()
        
        # Detect all essential runtimes
        results = detector.detect_all_essential_runtimes()
        
        # Display results
        detected_count = sum(1 for r in results if r.detected)
        print(f"Detection Summary: {detected_count}/{len(results)} essential runtimes detected")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            status = "✅ DETECTED" if result.detected else "❌ NOT FOUND"
            version_info = f" (v{result.version})" if result.version else ""
            confidence_info = f" [Confidence: {result.confidence:.2f}]" if result.detected else ""
            
            print(f"{i}. {result.runtime_name}: {status}{version_info}{confidence_info}")
            
            if result.detected:
                if result.install_path:
                    print(f"   📁 Install Path: {result.install_path}")
                if result.executable_path:
                    print(f"   🔧 Executable: {result.executable_path}")
                if result.environment_variables:
                    print(f"   🌍 Environment Variables: {len(result.environment_variables)} found")
                    for var_name, var_value in result.environment_variables.items():
                        print(f"      {var_name} = {var_value}")
                if result.validation_results:
                    successful_validations = sum(result.validation_results.values())
                    total_validations = len(result.validation_results)
                    print(f"   ✅ Validation: {successful_validations}/{total_validations} tests passed")
                if result.metadata:
                    print(f"   📊 Metadata: {len(result.metadata)} items")
                    for key, value in result.metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            print(f"      {key}: {value}")
                        elif isinstance(value, list) and len(value) <= 3:
                            print(f"      {key}: {value}")
            
            if result.errors:
                print(f"   ⚠️  Errors: {len(result.errors)}")
                for error in result.errors:
                    print(f"      - {error}")
            
            if result.warnings:
                print(f"   ⚠️  Warnings: {len(result.warnings)}")
                for warning in result.warnings:
                    print(f"      - {warning}")
            
            print()
        
        print("=" * 80)
        print("3. Testing individual runtime detection methods...")
        print()
        
        # Test individual detection methods
        individual_tests = [
            ("Git 2.47.1", detector.detect_git_2_47_1),
            (".NET SDK 8.0", detector.detect_dotnet_sdk_8_0),
            ("Java JDK 21", detector.detect_java_jdk_21),
            ("Visual C++ Redistributables", detector.detect_vcpp_redistributables),
            ("Anaconda3", detector.detect_anaconda3),
            (".NET Desktop Runtime", detector.detect_dotnet_desktop_runtime),
            ("PowerShell 7", detector.detect_powershell_7),
            ("Node.js/Python Updated", detector.detect_updated_nodejs_python)
        ]
        
        for test_name, test_method in individual_tests:
            try:
                result = test_method()
                status = "✅ DETECTED" if result.detected else "❌ NOT FOUND"
                version_info = f" (v{result.version})" if result.version else ""
                print(f"   {test_name}: {status}{version_info}")
            except Exception as e:
                print(f"   {test_name}: ❌ ERROR - {str(e)}")
        
        print()
        print("=" * 80)
        print("4. Runtime Configuration Summary...")
        print()
        
        # Show configuration summary
        for runtime_key, config in detector._runtime_configs.items():
            print(f"Runtime: {config['name']}")
            print(f"  Target Version: {config['target_version']}")
            print(f"  Detection Methods: ", end="")
            methods = []
            if config.get('version_command'):
                methods.append("Command")
            if config.get('registry_keys'):
                methods.append("Registry")
            if config.get('common_paths'):
                methods.append("Filesystem")
            print(", ".join(methods))
            print(f"  Environment Variables: {len(config.get('environment_variables', {}))}")
            print(f"  Validation Commands: {len(config.get('validation_commands', []))}")
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