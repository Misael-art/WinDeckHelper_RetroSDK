# Catálogo de Runtimes e Funcionalidades Steam Deck - Design

## Overview

This design document outlines the architecture for completing the Environment Dev project's runtime catalog and implementing Steam Deck-specific optimizations. The system will expand from 77+ existing components to include 8 essential missing runtimes, Steam Deck hardware optimizations, plugin system, advanced package manager integration, and comprehensive application detection.

The design focuses on maintaining backward compatibility while adding modern development tools and Steam Deck-specific features that leverage the device's unique hardware capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Environment Dev Core                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Runtime       │  │   Steam Deck    │  │   Plugin     │ │
│  │   Catalog       │  │   Integration   │  │   System     │ │
│  │   Manager       │  │   Layer         │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Package       │  │   Storage       │  │  Detection   │ │
│  │   Manager       │  │   Manager       │  │  Engine      │ │
│  │   Integration   │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Existing Core Components                    │
│        (Installation, Download, GUI, Logging, etc.)        │
└─────────────────────────────────────────────────────────────┘
```

### Design Rationale

The architecture extends the existing Environment Dev system rather than replacing it, ensuring:
- **Backward Compatibility**: All existing 77+ components continue to work
- **Modular Design**: New features are implemented as separate modules
- **Steam Deck Focus**: Dedicated layer for Steam Deck optimizations
- **Extensibility**: Plugin system allows community contributions

## Components and Interfaces

### 1. Runtime Catalog Manager

**Purpose**: Manages the 8 missing essential runtimes with automatic configuration

```python
class RuntimeCatalogManager:
    def __init__(self):
        self.runtimes = {
            'git': GitRuntime(),
            'dotnet_sdk': DotNetSDKRuntime(),
            'java_jdk': JavaJDKRuntime(),
            'vcpp_redist': VCppRedistRuntime(),
            'anaconda': AnacondaRuntime(),
            'dotnet_desktop': DotNetDesktopRuntime(),
            'powershell7': PowerShell7Runtime(),
            'nodejs_python_updated': UpdatedRuntimesManager()
        }
    
    def install_runtime(self, runtime_name: str) -> bool
    def configure_environment(self, runtime_name: str) -> bool
    def validate_installation(self, runtime_name: str) -> bool
    def get_runtime_status(self) -> Dict[str, RuntimeStatus]
```

**Key Features**:
- Automatic environment variable configuration (JAVA_HOME, PATH, etc.)
- Version management and compatibility checking
- Dependency resolution between runtimes
- Rollback capability for failed installations

### 2. Steam Deck Integration Layer

**Purpose**: Provides Steam Deck-specific optimizations and Steam ecosystem integration

```python
class SteamDeckManager:
    def detect_steam_deck(self) -> bool
    def apply_hardware_optimizations(self) -> bool
    def configure_steam_input(self) -> bool
    def setup_glossi_integration(self) -> bool
    def optimize_power_profiles(self) -> bool
    def configure_touch_screen(self) -> bool
```

**Hardware Detection Strategy**:
- DMI/SMBIOS detection for Steam Deck hardware
- Fallback to Steam client detection
- Manual override option for edge cases

**Steam Integration Components**:
- **GlosSI Integration**: Allows non-Steam apps to use Steam Input
- **Steam Input Mapping**: Maps development tools to controller inputs
- **Overlay Support**: Enables tool access during Steam sessions
- **Steam Cloud Sync**: Synchronizes configurations across devices

### 3. Plugin System

**Purpose**: Extensible architecture for community-contributed runtimes and features

```python
class PluginManager:
    def load_plugin(self, plugin_path: str) -> Plugin
    def validate_plugin(self, plugin: Plugin) -> ValidationResult
    def register_runtime(self, plugin: Plugin, runtime: Runtime) -> bool
    def detect_conflicts(self) -> List[PluginConflict]
    def update_plugin(self, plugin_name: str) -> bool
```

**Plugin Interface**:
```python
class Plugin:
    name: str
    version: str
    dependencies: List[str]
    
    def install(self) -> bool
    def configure(self) -> bool
    def validate(self) -> bool
    def uninstall(self) -> bool
```

**Security Model**:
- Sandboxed execution environment
- API whitelist for safe operations
- Digital signature verification for trusted plugins
- User consent for privileged operations

### 4. Storage Manager

**Purpose**: Intelligent storage management for space-constrained environments

```python
class StorageManager:
    def calculate_requirements(self, components: List[str]) -> StorageRequirement
    def check_available_space(self) -> Dict[str, int]
    def suggest_selective_installation(self) -> List[str]
    def cleanup_post_installation(self) -> int
    def distribute_across_drives(self, components: List[str]) -> Dict[str, List[str]]
```

**Storage Optimization Strategies**:
- **Pre-installation Analysis**: Calculate total space requirements
- **Selective Installation**: Allow users to choose components based on available space
- **Multi-drive Distribution**: Spread installations across available drives
- **Cleanup Automation**: Remove temporary files and caches post-installation
- **Compression**: Use compression for rarely-accessed components

### 5. Package Manager Integration

**Purpose**: Native integration with npm, pip, conda, and other package managers

```python
class PackageManagerIntegrator:
    def detect_package_managers(self) -> List[PackageManager]
    def install_global_packages(self, manager: str, packages: List[str]) -> bool
    def create_virtual_environment(self, manager: str, name: str) -> bool
    def resolve_conflicts(self) -> List[ConflictResolution]
    def maintain_installation_registry(self) -> bool
```

**Supported Package Managers**:
- **npm**: Global package installation and project setup
- **pip**: Virtual environment management and package installation
- **conda**: Environment creation and package management
- **yarn**: Alternative Node.js package manager
- **pipenv**: Python dependency management

### 6. Detection Engine

**Purpose**: Comprehensive application detection across multiple installation methods

```python
class DetectionEngine:
    def scan_registry_installations(self) -> List[InstalledApp]
    def detect_portable_applications(self) -> List[PortableApp]
    def verify_versions(self, apps: List[App]) -> List[VersionInfo]
    def validate_dependencies(self, app: App) -> DependencyStatus
    def generate_comprehensive_report(self) -> InstallationReport
```

**Detection Methods**:
- **Windows Registry**: Standard installed applications
- **Portable Detection**: Executable-based detection for portable apps
- **Version Verification**: Compare installed vs. available versions
- **Dependency Validation**: Ensure all dependencies are satisfied
- **Path-based Detection**: Find applications in common installation paths

### 7. Catalog Update Manager

**Purpose**: Automatic updates for runtime catalog with fallback mechanisms

```python
class CatalogUpdateManager:
    def check_catalog_updates(self) -> UpdateStatus
    def download_catalog_updates(self) -> bool
    def validate_catalog_integrity(self) -> bool
    def apply_updates_with_rollback(self) -> bool
    def manage_mirror_fallbacks(self) -> List[str]
    def notify_user_of_updates(self, updates: List[Update]) -> bool
    def maintain_local_cache(self) -> bool
```

**Update Strategy**:
- **Startup Checks**: Verify catalog updates on system initialization
- **Background Updates**: Download updates without interrupting user workflow
- **Mirror Management**: Automatically switch to alternative mirrors when URLs become obsolete
- **Backward Compatibility**: Ensure new catalog versions work with existing installations
- **Cache Fallback**: Use local cache when remote updates fail

## Data Models

### Runtime Configuration Model

```python
@dataclass
class RuntimeConfig:
    name: str
    version: str
    download_url: str
    mirrors: List[str]
    installation_type: InstallationType
    environment_variables: Dict[str, str]
    dependencies: List[str]
    post_install_scripts: List[str]
    validation_commands: List[str]
```

### Steam Deck Profile Model

```python
@dataclass
class SteamDeckProfile:
    hardware_detected: bool
    controller_config: ControllerConfig
    power_profile: PowerProfile
    display_settings: DisplaySettings
    audio_settings: AudioSettings
    steam_integration: SteamIntegrationConfig
```

### Plugin Metadata Model

```python
@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    api_version: str
    dependencies: List[str]
    permissions: List[Permission]
    signature: str
```

## Error Handling

### Runtime Installation Errors

**Strategy**: Graceful degradation with detailed error reporting

1. **Pre-installation Validation**: Check system requirements and dependencies
2. **Atomic Operations**: Ensure installations can be rolled back on failure
3. **Mirror Fallback**: Automatically try alternative download sources
4. **Partial Success Handling**: Continue with successful installations if some fail
5. **User Notification**: Provide clear error messages and suggested actions

### Steam Deck Detection Failures

**Strategy**: Fallback to generic optimizations with manual override

1. **Hardware Detection Fallback**: Use multiple detection methods
2. **Manual Configuration**: Allow users to force Steam Deck mode
3. **Graceful Degradation**: Apply generic optimizations if Steam Deck detection fails
4. **Steam Client Detection**: Use Steam client presence as secondary indicator

### Plugin System Errors

**Strategy**: Isolation and safe failure modes

1. **Plugin Isolation**: Prevent plugin failures from affecting core system
2. **Validation Errors**: Detailed reporting of plugin validation failures
3. **Conflict Resolution**: Automatic detection and resolution of plugin conflicts
4. **Safe Mode**: Ability to disable all plugins for troubleshooting

## Testing Strategy

### Unit Testing

- **Runtime Managers**: Test each runtime installation and configuration
- **Detection Engine**: Verify detection accuracy across different scenarios
- **Plugin System**: Test plugin loading, validation, and execution
- **Storage Manager**: Validate space calculations and optimization algorithms

### Integration Testing

- **End-to-End Runtime Installation**: Complete installation workflows
- **Steam Deck Hardware Simulation**: Mock Steam Deck environment for testing
- **Package Manager Integration**: Test with real package managers
- **Multi-component Scenarios**: Test complex installation combinations

### Steam Deck Testing

- **Hardware-specific Testing**: Test on actual Steam Deck hardware
- **Steam Integration Testing**: Verify GlosSI and Steam Input functionality
- **Performance Testing**: Validate power and performance optimizations
- **Compatibility Testing**: Ensure compatibility with SteamOS updates

### Plugin Testing

- **Plugin API Testing**: Verify plugin interface compliance
- **Security Testing**: Validate sandboxing and permission systems
- **Conflict Testing**: Test plugin conflict detection and resolution
- **Update Testing**: Verify plugin update mechanisms

## Performance Considerations

### Download Optimization

- **Parallel Downloads**: Download multiple runtimes simultaneously
- **Resume Capability**: Resume interrupted downloads
- **Bandwidth Management**: Respect user bandwidth limitations
- **Mirror Selection**: Choose fastest available mirrors

### Installation Performance

- **Background Installation**: Install components in background when possible
- **Installation Queuing**: Optimize installation order for dependencies
- **Resource Management**: Manage CPU and disk I/O during installation
- **Progress Tracking**: Provide accurate progress information

### Steam Deck Optimizations

- **Battery Optimization**: Minimize background processes during installation
- **Thermal Management**: Monitor and respond to thermal conditions
- **Storage Optimization**: Optimize for Steam Deck's storage characteristics
- **Memory Management**: Efficient memory usage for limited RAM scenarios

## Security Considerations

### Plugin Security

- **Code Signing**: Require signed plugins from trusted sources
- **Sandboxing**: Execute plugins in isolated environments
- **Permission Model**: Granular permissions for plugin operations
- **API Restrictions**: Limit plugin access to safe operations only

### Download Security

- **Checksum Verification**: Verify integrity of downloaded files
- **HTTPS Enforcement**: Use secure connections for all downloads
- **Mirror Validation**: Validate mirror authenticity
- **Malware Scanning**: Optional integration with antivirus systems

### System Security

- **Privilege Escalation**: Minimize required administrator privileges
- **Registry Protection**: Safe registry modification practices
- **File System Security**: Secure file operations and permissions
- **Update Security**: Secure update mechanisms for catalog and plugins