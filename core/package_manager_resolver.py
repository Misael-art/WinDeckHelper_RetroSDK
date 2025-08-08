"""
Package Manager Resolver for dependency resolution.
Integrates with npm, pip, conda for automatic dependency resolution.
"""

import asyncio
import json
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path


class PackageManagerType(Enum):
    """Supported package manager types."""
    NPM = "npm"
    PIP = "pip"
    CONDA = "conda"
    YARN = "yarn"
    PIPENV = "pipenv"


@dataclass
class PackageInfo:
    """Information about a package from package manager."""
    name: str
    version: str
    description: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    available_versions: List[str] = field(default_factory=list)
    latest_version: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    last_updated: Optional[str] = None


@dataclass
class PackageManagerCache:
    """Cache for package manager metadata."""
    packages: Dict[str, PackageInfo] = field(default_factory=dict)
    last_updated: Dict[str, float] = field(default_factory=dict)
    cache_duration: int = 3600  # 1 hour in seconds
    
    def is_expired(self, package_name: str) -> bool:
        """Check if cache entry is expired."""
        if package_name not in self.last_updated:
            return True
        return time.time() - self.last_updated[package_name] > self.cache_duration
    
    def update_package(self, package_name: str, package_info: PackageInfo) -> None:
        """Update package information in cache."""
        self.packages[package_name] = package_info
        self.last_updated[package_name] = time.time()
    
    def get_package(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from cache if not expired."""
        if not self.is_expired(package_name):
            return self.packages.get(package_name)
        return None


class PackageManagerResolver:
    """Resolves dependencies using various package managers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = PackageManagerCache()
        self._detected_managers: Dict[PackageManagerType, bool] = {}
    
    async def resolve_dependencies(self, 
                                 package_name: str,
                                 manager_type: PackageManagerType,
                                 constraints: List[str] = None) -> Dict[str, Any]:
        """Resolve dependencies for a package using specified manager."""
        try:
            # Check if package manager is available
            if not await self._is_manager_available(manager_type):
                return {
                    "success": False,
                    "error": f"{manager_type.value} is not available",
                    "dependencies": []
                }
            
            # Get package information
            package_info = await self._get_package_info(package_name, manager_type)
            if not package_info:
                return {
                    "success": False,
                    "error": f"Package {package_name} not found",
                    "dependencies": []
                }
            
            # Resolve dependencies recursively
            resolved_deps = await self._resolve_recursive_dependencies(
                package_name, manager_type, constraints or []
            )
            
            return {
                "success": True,
                "package_info": package_info,
                "dependencies": resolved_deps,
                "resolution_time": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving dependencies for {package_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "dependencies": []
            }
    
    async def get_available_versions(self, 
                                   package_name: str,
                                   manager_type: PackageManagerType) -> List[str]:
        """Get available versions for a package."""
        try:
            if manager_type == PackageManagerType.NPM:
                return await self._get_npm_versions(package_name)
            elif manager_type == PackageManagerType.PIP:
                return await self._get_pip_versions(package_name)
            elif manager_type == PackageManagerType.CONDA:
                return await self._get_conda_versions(package_name)
            elif manager_type == PackageManagerType.YARN:
                return await self._get_yarn_versions(package_name)
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting versions for {package_name}: {str(e)}")
            return []
    
    async def find_compatible_version(self,
                                    package_name: str,
                                    manager_type: PackageManagerType,
                                    constraints: List[str]) -> Optional[str]:
        """Find the best compatible version for given constraints."""
        available_versions = await self.get_available_versions(package_name, manager_type)
        
        if not available_versions:
            return None
        
        # Use semantic version validator to find best match
        from .semantic_version_validator import SemanticVersionValidator
        validator = SemanticVersionValidator()
        
        compatible_versions = validator.find_compatible_versions(available_versions, constraints)
        
        if compatible_versions:
            return compatible_versions[0][0]  # Return best match
        
        return None
    
    async def check_dependency_conflicts(self,
                                       dependencies: Dict[str, str],
                                       manager_type: PackageManagerType) -> List[Dict[str, Any]]:
        """Check for conflicts in dependency list."""
        conflicts = []
        
        # Group dependencies by package name
        package_constraints = {}
        for dep_string in dependencies.values():
            # Parse dependency string (e.g., "package>=1.0.0")
            package_name, constraint = self._parse_dependency_string(dep_string)
            if package_name not in package_constraints:
                package_constraints[package_name] = []
            package_constraints[package_name].append(constraint)
        
        # Check for conflicts in each package
        from .semantic_version_validator import SemanticVersionValidator
        validator = SemanticVersionValidator()
        
        for package_name, constraints in package_constraints.items():
            if len(constraints) > 1:
                # Multiple constraints for same package - check compatibility
                available_versions = await self.get_available_versions(package_name, manager_type)
                compatible_versions = validator.find_compatible_versions(available_versions, constraints)
                
                if not compatible_versions:
                    conflicts.append({
                        "package": package_name,
                        "conflicting_constraints": constraints,
                        "available_versions": available_versions[:10],  # Limit for performance
                        "resolution_suggestion": validator.suggest_version_resolution(constraints, available_versions)
                    })
        
        return conflicts
    
    async def _is_manager_available(self, manager_type: PackageManagerType) -> bool:
        """Check if package manager is available on system."""
        if manager_type in self._detected_managers:
            return self._detected_managers[manager_type]
        
        try:
            if manager_type == PackageManagerType.NPM:
                result = await self._run_command(["npm", "--version"])
            elif manager_type == PackageManagerType.PIP:
                result = await self._run_command(["pip", "--version"])
            elif manager_type == PackageManagerType.CONDA:
                result = await self._run_command(["conda", "--version"])
            elif manager_type == PackageManagerType.YARN:
                result = await self._run_command(["yarn", "--version"])
            elif manager_type == PackageManagerType.PIPENV:
                result = await self._run_command(["pipenv", "--version"])
            else:
                result = False
            
            self._detected_managers[manager_type] = bool(result)
            return self._detected_managers[manager_type]
            
        except Exception:
            self._detected_managers[manager_type] = False
            return False
    
    async def _get_package_info(self, 
                              package_name: str,
                              manager_type: PackageManagerType) -> Optional[PackageInfo]:
        """Get package information from cache or package manager."""
        # Check cache first
        cached_info = self.cache.get_package(f"{manager_type.value}:{package_name}")
        if cached_info:
            return cached_info
        
        # Fetch from package manager
        try:
            if manager_type == PackageManagerType.NPM:
                info = await self._get_npm_package_info(package_name)
            elif manager_type == PackageManagerType.PIP:
                info = await self._get_pip_package_info(package_name)
            elif manager_type == PackageManagerType.CONDA:
                info = await self._get_conda_package_info(package_name)
            else:
                return None
            
            if info:
                self.cache.update_package(f"{manager_type.value}:{package_name}", info)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting package info for {package_name}: {str(e)}")
            return None
    
    async def _get_npm_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from npm."""
        try:
            result = await self._run_command(["npm", "view", package_name, "--json"])
            if not result:
                return None
            
            data = json.loads(result)
            
            return PackageInfo(
                name=data.get("name", package_name),
                version=data.get("version", "unknown"),
                description=data.get("description"),
                dependencies=data.get("dependencies", {}),
                dev_dependencies=data.get("devDependencies", {}),
                available_versions=data.get("versions", []),
                latest_version=data.get("dist-tags", {}).get("latest"),
                homepage=data.get("homepage"),
                repository=data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),
                license=data.get("license")
            )
            
        except Exception as e:
            self.logger.error(f"Error getting npm package info: {str(e)}")
            return None
    
    async def _get_pip_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from pip."""
        try:
            # Use pip show for basic info
            show_result = await self._run_command(["pip", "show", package_name])
            if not show_result:
                return None
            
            # Parse pip show output
            info_dict = {}
            for line in show_result.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info_dict[key.strip().lower()] = value.strip()
            
            # Get available versions (this is more complex for pip)
            available_versions = await self._get_pip_versions(package_name)
            
            return PackageInfo(
                name=info_dict.get("name", package_name),
                version=info_dict.get("version", "unknown"),
                description=info_dict.get("summary"),
                available_versions=available_versions,
                homepage=info_dict.get("home-page"),
                license=info_dict.get("license")
            )
            
        except Exception as e:
            self.logger.error(f"Error getting pip package info: {str(e)}")
            return None
    
    async def _get_conda_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from conda."""
        try:
            result = await self._run_command(["conda", "search", package_name, "--json"])
            if not result:
                return None
            
            data = json.loads(result)
            if package_name not in data:
                return None
            
            package_data = data[package_name]
            if not package_data:
                return None
            
            latest_info = package_data[-1]  # Last entry is usually latest
            versions = [item["version"] for item in package_data]
            
            return PackageInfo(
                name=package_name,
                version=latest_info.get("version", "unknown"),
                available_versions=versions,
                latest_version=versions[-1] if versions else None
            )
            
        except Exception as e:
            self.logger.error(f"Error getting conda package info: {str(e)}")
            return None
    
    async def _get_npm_versions(self, package_name: str) -> List[str]:
        """Get available versions from npm."""
        try:
            result = await self._run_command(["npm", "view", package_name, "versions", "--json"])
            if result:
                versions = json.loads(result)
                return versions if isinstance(versions, list) else [versions]
            return []
        except Exception:
            return []
    
    async def _get_pip_versions(self, package_name: str) -> List[str]:
        """Get available versions from pip (using pip index)."""
        try:
            # This is a simplified approach - in practice you might want to use PyPI API
            result = await self._run_command(["pip", "index", "versions", package_name])
            if result:
                # Parse the output to extract versions
                versions = []
                for line in result.split('\n'):
                    if 'Available versions:' in line:
                        version_part = line.split('Available versions:')[1].strip()
                        versions = [v.strip() for v in version_part.split(',')]
                        break
                return versions
            return []
        except Exception:
            # Fallback: try to get from pip show and assume current version
            try:
                result = await self._run_command(["pip", "show", package_name])
                if result:
                    for line in result.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(':', 1)[1].strip()
                            return [version]
            except Exception:
                pass
            return []
    
    async def _get_conda_versions(self, package_name: str) -> List[str]:
        """Get available versions from conda."""
        try:
            result = await self._run_command(["conda", "search", package_name, "--json"])
            if result:
                data = json.loads(result)
                if package_name in data:
                    return [item["version"] for item in data[package_name]]
            return []
        except Exception:
            return []
    
    async def _get_yarn_versions(self, package_name: str) -> List[str]:
        """Get available versions from yarn."""
        try:
            result = await self._run_command(["yarn", "info", package_name, "versions", "--json"])
            if result:
                data = json.loads(result)
                return data.get("data", [])
            return []
        except Exception:
            return []
    
    async def _resolve_recursive_dependencies(self,
                                            package_name: str,
                                            manager_type: PackageManagerType,
                                            constraints: List[str],
                                            visited: set = None) -> List[Dict[str, Any]]:
        """Recursively resolve dependencies."""
        if visited is None:
            visited = set()
        
        if package_name in visited:
            return []  # Avoid circular dependencies
        
        visited.add(package_name)
        dependencies = []
        
        try:
            package_info = await self._get_package_info(package_name, manager_type)
            if not package_info:
                return dependencies
            
            # Add direct dependencies
            for dep_name, dep_constraint in package_info.dependencies.items():
                dep_info = {
                    "name": dep_name,
                    "constraint": dep_constraint,
                    "type": "runtime",
                    "depth": len(visited)
                }
                dependencies.append(dep_info)
                
                # Recursively resolve sub-dependencies (limit depth to avoid infinite recursion)
                if len(visited) < 5:
                    sub_deps = await self._resolve_recursive_dependencies(
                        dep_name, manager_type, [dep_constraint], visited.copy()
                    )
                    dependencies.extend(sub_deps)
            
            # Add dev dependencies if at root level
            if len(visited) == 1:
                for dep_name, dep_constraint in package_info.dev_dependencies.items():
                    dep_info = {
                        "name": dep_name,
                        "constraint": dep_constraint,
                        "type": "development",
                        "depth": len(visited)
                    }
                    dependencies.append(dep_info)
            
        except Exception as e:
            self.logger.error(f"Error resolving dependencies for {package_name}: {str(e)}")
        
        return dependencies
    
    async def _run_command(self, command: List[str], timeout: int = 30) -> Optional[str]:
        """Run a command asynchronously with timeout."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            else:
                self.logger.warning(f"Command failed: {' '.join(command)}, stderr: {stderr.decode('utf-8')}")
                return None
                
        except asyncio.TimeoutError:
            self.logger.error(f"Command timed out: {' '.join(command)}")
            return None
        except Exception as e:
            self.logger.error(f"Error running command {' '.join(command)}: {str(e)}")
            return None
    
    def _parse_dependency_string(self, dep_string: str) -> Tuple[str, str]:
        """Parse dependency string into package name and constraint."""
        # Handle various formats: "package>=1.0.0", "package==1.0.0", "package"
        import re
        
        # Match package name and version constraint
        match = re.match(r'^([a-zA-Z0-9_-]+)(.*)$', dep_string.strip())
        if match:
            package_name = match.group(1)
            constraint = match.group(2).strip() or "*"
            return package_name, constraint
        
        return dep_string, "*"
    
    def clear_cache(self) -> None:
        """Clear the package manager cache."""
        self.cache = PackageManagerCache()
        self._detected_managers.clear()