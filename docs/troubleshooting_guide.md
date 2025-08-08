# Environment Dev Deep Evaluation - Troubleshooting Guide

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Installation Problems](#installation-problems)
4. [Detection Issues](#detection-issues)
5. [Download and Network Problems](#download-and-network-problems)
6. [Steam Deck Specific Issues](#steam-deck-specific-issues)
7. [Performance Issues](#performance-issues)
8. [Plugin Problems](#plugin-problems)
9. [Advanced Troubleshooting](#advanced-troubleshooting)
10. [Getting Support](#getting-support)

## Quick Diagnostics

### Self-Diagnostic Tool

Before diving into specific issues, run the built-in diagnostic tool:

1. **Open Diagnostics**
   - Launch Environment Dev Deep Evaluation
   - Go to Help > Run Diagnostics
   - Or press `Ctrl+Shift+D`

2. **Review Results**
   - System compatibility check
   - Network connectivity test
   - Component detection verification
   - Configuration validation

3. **Follow Recommendations**
   - Apply suggested fixes automatically
   - Review manual fix instructions
   - Export diagnostic report if needed

### Quick Health Check

```bash
# Command line health check
envdev --health-check

# Detailed system information
envdev --system-info

# Network connectivity test
envdev --network-test
```

### Log File Locations

**Windows:**
- Application logs: `%APPDATA%\EnvironmentDevDeepEvaluation\logs\`
- System logs: `%PROGRAMDATA%\EnvironmentDevDeepEvaluation\logs\`
- Crash dumps: `%LOCALAPPDATA%\EnvironmentDevDeepEvaluation\crashes\`

**Steam Deck:**
- Application logs: `~/.local/share/EnvironmentDevDeepEvaluation/logs/`
- System logs: `/var/log/EnvironmentDevDeepEvaluation/`
- Crash dumps: `~/.local/share/EnvironmentDevDeepEvaluation/crashes/`

## Common Issues

### Issue 1: Application Won't Start

#### Symptoms
- Application fails to launch
- Splash screen appears then disappears
- Error message on startup
- Application crashes immediately

#### Diagnostic Steps
1. **Check System Requirements**
   ```bash
   # Verify Windows version
   winver
   
   # Check available memory
   wmic computersystem get TotalPhysicalMemory
   
   # Verify disk space
   dir C:\ | findstr "bytes free"
   ```

2. **Verify Installation Integrity**
   ```bash
   # Windows - verify installation
   sfc /scannow
   
   # Check application files
   envdev --verify-installation
   ```

3. **Check Dependencies**
   - Ensure .NET Runtime is installed
   - Verify Visual C++ Redistributables
   - Check Windows updates

#### Solutions

**Solution A: Run as Administrator**
1. Right-click application shortcut
2. Select "Run as administrator"
3. If successful, adjust UAC settings or create elevated shortcut

**Solution B: Repair Installation**
1. Go to Control Panel > Programs and Features
2. Find Environment Dev Deep Evaluation
3. Click "Change" then "Repair"
4. Follow repair wizard instructions

**Solution C: Clean Reinstall**
1. Uninstall application completely
2. Delete remaining folders:
   - `%PROGRAMFILES%\EnvironmentDevDeepEvaluation`
   - `%APPDATA%\EnvironmentDevDeepEvaluation`
3. Restart computer
4. Download fresh installer
5. Install with administrator privileges

**Solution D: Compatibility Mode**
1. Right-click application executable
2. Select Properties > Compatibility
3. Enable "Run this program in compatibility mode"
4. Select Windows 10 or earlier version
5. Apply and test

### Issue 2: Slow Performance

#### Symptoms
- Application takes long time to start
- Analysis runs slower than 15 seconds
- UI is unresponsive
- High CPU or memory usage

#### Diagnostic Steps
1. **Check System Resources**
   ```bash
   # Check CPU usage
   wmic cpu get loadpercentage /value
   
   # Check memory usage
   wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value
   
   # Check disk usage
   wmic logicaldisk get size,freespace,caption
   ```

2. **Monitor Application Performance**
   - Open Task Manager
   - Find Environment Dev Deep Evaluation process
   - Monitor CPU, Memory, and Disk usage
   - Check for memory leaks over time

#### Solutions

**Solution A: Optimize Settings**
1. Open Settings > Performance
2. Reduce parallel download threads
3. Disable unnecessary features
4. Enable performance mode

**Solution B: Clear Cache**
1. Go to Settings > Advanced
2. Click "Clear All Caches"
3. Restart application
4. Run fresh analysis

**Solution C: Update Hardware Drivers**
1. Update graphics drivers
2. Update network drivers
3. Update storage drivers
4. Restart computer

**Solution D: Increase Virtual Memory**
1. Open System Properties > Advanced
2. Click Performance Settings
3. Go to Advanced > Virtual Memory
4. Increase paging file size
5. Restart computer

### Issue 3: Network Connectivity Problems

#### Symptoms
- Downloads fail consistently
- "Network unreachable" errors
- Timeout errors during analysis
- Mirror servers not responding

#### Diagnostic Steps
1. **Test Basic Connectivity**
   ```bash
   # Test internet connection
   ping google.com
   
   # Test DNS resolution
   nslookup github.com
   
   # Test HTTPS connectivity
   curl -I https://api.github.com
   ```

2. **Check Firewall and Antivirus**
   - Temporarily disable Windows Firewall
   - Disable antivirus real-time protection
   - Check corporate firewall settings
   - Review proxy configurations

#### Solutions

**Solution A: Configure Firewall**
1. Open Windows Defender Firewall
2. Click "Allow an app or feature"
3. Add Environment Dev Deep Evaluation
4. Enable for both Private and Public networks

**Solution B: Configure Proxy**
1. Open Settings > Network
2. Enter proxy server details
3. Configure authentication if required
4. Test connectivity

**Solution C: Use Alternative Mirrors**
1. Go to Settings > Downloads
2. Select different mirror servers
3. Test download speeds
4. Save optimal configuration

**Solution D: DNS Configuration**
1. Change DNS servers to 8.8.8.8 and 8.8.4.4
2. Flush DNS cache: `ipconfig /flushdns`
3. Restart network adapter
4. Test connectivity

## Installation Problems

### Issue 4: Component Installation Failures

#### Symptoms
- "Installation failed" error messages
- Partial installations
- Rollback triggered automatically
- Components not detected after installation

#### Diagnostic Steps
1. **Check Installation Logs**
   ```bash
   # View recent installation logs
   envdev --show-logs --filter installation
   
   # Check specific component logs
   envdev --component-logs git
   ```

2. **Verify Permissions**
   - Check write permissions to installation directories
   - Verify administrator privileges
   - Check disk space availability

3. **Test Manual Installation**
   - Try installing component manually
   - Compare with automated installation
   - Check for conflicting software

#### Solutions

**Solution A: Run with Elevated Privileges**
1. Close application
2. Right-click and "Run as administrator"
3. Retry installation
4. If successful, configure permanent elevation

**Solution B: Free Disk Space**
1. Check available disk space
2. Clean temporary files
3. Move files to external storage
4. Retry installation

**Solution C: Resolve Conflicts**
1. Uninstall conflicting software
2. Update existing installations
3. Use compatibility mode
4. Install to alternative location

**Solution D: Manual Installation**
1. Download component manually
2. Install using component's installer
3. Refresh detection in application
4. Verify installation success

### Issue 5: Rollback Problems

#### Symptoms
- Rollback fails to complete
- System left in inconsistent state
- Cannot restore previous configuration
- Rollback process hangs

#### Diagnostic Steps
1. **Check Rollback Logs**
   ```bash
   # View rollback history
   envdev --rollback-history
   
   # Check rollback status
   envdev --rollback-status
   ```

2. **Verify Backup Integrity**
   - Check backup file existence
   - Verify backup file integrity
   - Test backup restoration manually

#### Solutions

**Solution A: Force Rollback**
1. Open Command Prompt as administrator
2. Run: `envdev --force-rollback --id [rollback_id]`
3. Wait for completion
4. Verify system state

**Solution B: Manual Restoration**
1. Locate backup files in logs
2. Manually restore configuration files
3. Reinstall previous component versions
4. Update system PATH variables

**Solution C: System Restore**
1. Open System Restore (Windows)
2. Select restore point before installation
3. Complete system restore
4. Reinstall application if needed

## Detection Issues

### Issue 6: Components Not Detected

#### Symptoms
- Known installed components show as missing
- Incorrect version numbers displayed
- Components installed in non-standard locations not found
- Detection results inconsistent

#### Diagnostic Steps
1. **Manual Verification**
   ```bash
   # Check Git installation
   git --version
   
   # Check .NET installation
   dotnet --version
   
   # Check Java installation
   java -version
   
   # Check Python installation
   python --version
   ```

2. **Check PATH Variables**
   ```bash
   # Display PATH
   echo %PATH%
   
   # Check specific tool paths
   where git
   where python
   where node
   ```

3. **Registry Check (Windows)**
   ```bash
   # Check installed programs
   reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
   ```

#### Solutions

**Solution A: Refresh Detection**
1. Open Detection tab
2. Click "Refresh All"
3. Wait for completion
4. Review updated results

**Solution B: Add Custom Paths**
1. Go to Settings > Detection
2. Click "Add Custom Path"
3. Browse to installation directory
4. Save and refresh detection

**Solution C: Update Detection Database**
1. Go to Settings > Updates
2. Click "Update Detection Database"
3. Download latest detection rules
4. Restart application

**Solution D: Manual Registration**
1. Go to Detection tab
2. Click "Add Manual Entry"
3. Enter component details
4. Specify installation path
5. Save configuration

### Issue 7: Incorrect Version Detection

#### Symptoms
- Wrong version numbers displayed
- Version conflicts reported incorrectly
- Compatibility issues with correct versions
- Update recommendations for current versions

#### Solutions

**Solution A: Clear Detection Cache**
1. Settings > Advanced > Clear Detection Cache
2. Restart application
3. Run fresh detection
4. Verify version accuracy

**Solution B: Update Version Database**
1. Settings > Updates > Update Version Database
2. Download latest version information
3. Refresh detection
4. Compare with manual verification

**Solution C: Manual Version Override**
1. Detection tab > Select component
2. Click "Edit Details"
3. Manually enter correct version
4. Save changes

## Download and Network Problems

### Issue 8: Download Failures

#### Symptoms
- Downloads timeout or fail
- Corrupted download files
- Hash verification failures
- Mirror servers unreachable

#### Diagnostic Steps
1. **Test Network Speed**
   ```bash
   # Test download speed
   envdev --speed-test
   
   # Test specific mirrors
   envdev --test-mirrors
   ```

2. **Check Download Integrity**
   ```bash
   # Verify downloaded files
   envdev --verify-downloads
   
   # Check hash mismatches
   envdev --check-hashes
   ```

#### Solutions

**Solution A: Change Download Settings**
1. Settings > Downloads
2. Reduce concurrent downloads
3. Increase timeout values
4. Enable retry on failure

**Solution B: Use Different Mirrors**
1. Settings > Downloads > Mirrors
2. Disable problematic mirrors
3. Add custom mirror URLs
4. Test mirror connectivity

**Solution C: Manual Download**
1. Copy download URL from logs
2. Download using web browser
3. Place file in download directory
4. Resume installation

### Issue 9: Hash Verification Failures

#### Symptoms
- "Hash mismatch" error messages
- Downloads rejected as corrupted
- Security warnings during installation
- Repeated download attempts

#### Solutions

**Solution A: Re-download Files**
1. Clear download cache
2. Delete corrupted files
3. Retry download from different mirror
4. Verify hash manually

**Solution B: Update Hash Database**
1. Settings > Security > Update Hashes
2. Download latest hash database
3. Retry verification
4. Report hash mismatches if persistent

**Solution C: Temporary Hash Bypass** (Use with caution)
1. Settings > Security > Advanced
2. Temporarily disable hash verification
3. Complete installation
4. Re-enable hash verification
5. Verify installation integrity

## Steam Deck Specific Issues

### Issue 10: Steam Deck Not Detected

#### Symptoms
- Application doesn't recognize Steam Deck hardware
- Standard interface shown instead of optimized version
- Steam Deck features unavailable
- Performance not optimized

#### Diagnostic Steps
1. **Check Hardware Detection**
   ```bash
   # Check DMI information
   sudo dmidecode -s system-product-name
   
   # Check Steam client
   ps aux | grep steam
   
   # Verify SteamOS version
   cat /etc/os-release
   ```

2. **Manual Detection Override**
   - Settings > Steam Deck > Force Detection
   - Enable Steam Deck mode manually
   - Test optimized interface

#### Solutions

**Solution A: Update Detection Logic**
1. Settings > Updates > Update Steam Deck Detection
2. Download latest detection rules
3. Restart application
4. Verify detection

**Solution B: Manual Configuration**
1. Settings > Steam Deck > Manual Setup
2. Enable Steam Deck optimizations
3. Configure controller settings
4. Test interface

**Solution C: Reinstall for Steam Deck**
1. Download Steam Deck specific package
2. Uninstall current version
3. Install Steam Deck optimized version
4. Configure settings

### Issue 11: Controller Input Problems

#### Symptoms
- Gamepad controls not working
- Button mapping incorrect
- Navigation difficult with controller
- Steam Input not recognized

#### Solutions

**Solution A: Configure Steam Input**
1. Add application to Steam as non-Steam game
2. Configure controller settings in Steam
3. Enable Steam Input for application
4. Test controller functionality

**Solution B: Update Controller Drivers**
1. Switch to Desktop Mode
2. Update controller drivers
3. Restart Steam Deck
4. Test controller in application

**Solution C: Reset Controller Configuration**
1. Settings > Steam Deck > Controller
2. Reset to default configuration
3. Reconfigure button mappings
4. Save and test

### Issue 12: Performance Issues on Steam Deck

#### Symptoms
- Application runs slowly
- High battery drain
- Thermal throttling
- Frame rate drops

#### Solutions

**Solution A: Enable Performance Mode**
1. Settings > Steam Deck > Performance
2. Enable performance optimizations
3. Adjust power profile
4. Monitor temperature

**Solution B: Reduce Background Processes**
1. Close unnecessary applications
2. Disable background services
3. Clear system cache
4. Restart Steam Deck

**Solution C: Optimize Settings**
1. Reduce visual effects
2. Disable animations
3. Lower refresh rate if needed
4. Enable power saving mode

## Performance Issues

### Issue 13: High Memory Usage

#### Symptoms
- Application uses excessive RAM
- System becomes slow
- Out of memory errors
- Memory leaks over time

#### Diagnostic Steps
1. **Monitor Memory Usage**
   ```bash
   # Check memory usage
   envdev --memory-usage
   
   # Monitor over time
   envdev --monitor-memory --duration 300
   ```

2. **Identify Memory Leaks**
   - Use Task Manager to monitor
   - Check for increasing memory usage
   - Identify problematic operations

#### Solutions

**Solution A: Restart Application**
1. Close application completely
2. Clear system cache
3. Restart application
4. Monitor memory usage

**Solution B: Adjust Memory Settings**
1. Settings > Performance > Memory
2. Reduce cache sizes
3. Limit concurrent operations
4. Enable memory optimization

**Solution C: Increase System Memory**
1. Close other applications
2. Increase virtual memory
3. Add physical RAM if possible
4. Use memory optimization tools

### Issue 14: CPU Usage Problems

#### Symptoms
- High CPU usage during idle
- System becomes unresponsive
- Fan noise increases
- Battery drains quickly

#### Solutions

**Solution A: Optimize CPU Usage**
1. Settings > Performance > CPU
2. Reduce background processing
3. Lower analysis frequency
4. Enable CPU throttling

**Solution B: Update Application**
1. Check for updates
2. Install latest version
3. Review performance improvements
4. Reset settings if needed

**Solution C: System Optimization**
1. Update system drivers
2. Run system maintenance
3. Check for malware
4. Optimize startup programs

## Plugin Problems

### Issue 15: Plugin Installation Failures

#### Symptoms
- Plugin installation fails
- Security warnings during installation
- Plugin not recognized after installation
- Compatibility errors

#### Solutions

**Solution A: Verify Plugin Signature**
1. Check plugin digital signature
2. Verify publisher authenticity
3. Download from official sources
4. Scan for malware

**Solution B: Update Plugin System**
1. Settings > Plugins > Update System
2. Download latest plugin framework
3. Restart application
4. Retry plugin installation

**Solution C: Manual Plugin Installation**
1. Download plugin manually
2. Extract to plugins directory
3. Restart application
4. Enable plugin in settings

### Issue 16: Plugin Conflicts

#### Symptoms
- Application crashes with plugins enabled
- Features not working correctly
- Error messages about plugin conflicts
- Performance degradation

#### Solutions

**Solution A: Disable Conflicting Plugins**
1. Settings > Plugins
2. Disable recently installed plugins
3. Test application stability
4. Enable plugins one by one

**Solution B: Update Plugins**
1. Check for plugin updates
2. Update all plugins
3. Restart application
4. Test functionality

**Solution C: Reset Plugin Configuration**
1. Settings > Plugins > Reset All
2. Disable all plugins
3. Restart application
4. Reconfigure plugins as needed

## Advanced Troubleshooting

### Registry Issues (Windows)

#### Clean Registry Entries
```bash
# Backup registry first
reg export HKEY_CURRENT_USER\Software\EnvironmentDevDeepEvaluation backup.reg

# Clean invalid entries
reg delete HKEY_CURRENT_USER\Software\EnvironmentDevDeepEvaluation\InvalidKey /f

# Restore if needed
reg import backup.reg
```

### File System Issues

#### Check File System Integrity
```bash
# Check disk for errors
chkdsk C: /f /r

# System file checker
sfc /scannow

# DISM repair
DISM /Online /Cleanup-Image /RestoreHealth
```

### Network Diagnostics

#### Advanced Network Testing
```bash
# Reset network stack
netsh winsock reset
netsh int ip reset

# Flush DNS
ipconfig /flushdns

# Reset TCP/IP
netsh int tcp reset
```

### Database Corruption

#### Repair Application Database
```bash
# Check database integrity
envdev --check-database

# Repair database
envdev --repair-database

# Rebuild database
envdev --rebuild-database
```

### Configuration Issues

#### Reset Configuration
```bash
# Backup current configuration
envdev --export-config backup.json

# Reset to defaults
envdev --reset-config

# Import specific settings
envdev --import-config backup.json --selective
```

## Getting Support

### Before Contacting Support

1. **Run Diagnostics**
   - Complete built-in diagnostic tool
   - Export diagnostic report
   - Review all error messages

2. **Gather Information**
   - System specifications
   - Application version
   - Error logs and screenshots
   - Steps to reproduce issue

3. **Try Basic Solutions**
   - Restart application
   - Update to latest version
   - Check system requirements
   - Review this troubleshooting guide

### Support Channels

#### Built-in Support
- Help > Contact Support
- Help > Report Bug
- Help > Request Feature

#### Community Support
- **Forum**: Community discussions and solutions
- **Discord**: Real-time chat support
- **Reddit**: User community and tips

#### Professional Support
- **Email**: support@environmentdevdeep.com
- **Ticket System**: Online support portal
- **Enterprise**: Dedicated support for business users

### Information to Include

When contacting support, please include:

1. **System Information**
   - Operating system and version
   - Hardware specifications
   - Application version
   - Steam Deck model (if applicable)

2. **Problem Description**
   - Detailed description of issue
   - Steps to reproduce
   - Expected vs actual behavior
   - When problem started

3. **Diagnostic Information**
   - Diagnostic report export
   - Relevant log files
   - Screenshots or videos
   - Error messages

4. **Troubleshooting Attempted**
   - Solutions already tried
   - Results of attempted fixes
   - Configuration changes made
   - Other software involved

### Response Times

- **Community Support**: Usually within 24 hours
- **Standard Support**: 1-2 business days
- **Priority Support**: Same business day
- **Enterprise Support**: Within 4 hours

Remember to check the FAQ and documentation before contacting support, as many common issues have quick solutions available.