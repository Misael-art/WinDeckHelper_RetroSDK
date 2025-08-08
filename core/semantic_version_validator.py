"""
Semantic Version Validator for advanced compatibility checking.
Implements sophisticated semantic versioning validation and scoring.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class VersionConstraintType(Enum):
    """Types of version constraints supported."""
    EXACT = "exact"           # ==1.0.0
    GREATER_THAN = "gt"       # >1.0.0
    GREATER_EQUAL = "gte"     # >=1.0.0
    LESS_THAN = "lt"          # <1.0.0
    LESS_EQUAL = "lte"        # <=1.0.0
    COMPATIBLE = "compatible" # ~1.0.0
    CARET = "caret"          # ^1.0.0
    RANGE = "range"          # 1.0.0 - 2.0.0
    WILDCARD = "wildcard"    # 1.0.*


@dataclass
class SemanticVersion:
    """Represents a semantic version with major.minor.patch format."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    @classmethod
    def parse(cls, version_str: str) -> 'SemanticVersion':
        """Parse a version string into SemanticVersion."""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')
        
        # Regex for semantic version parsing
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        match = re.match(pattern, version_str)
        
        if not match:
            # Fallback for simpler version formats
            simple_pattern = r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?'
            simple_match = re.match(simple_pattern, version_str)
            if simple_match:
                major = int(simple_match.group(1))
                minor = int(simple_match.group(2) or 0)
                patch = int(simple_match.group(3) or 0)
                return cls(major, minor, patch)
            else:
                raise ValueError(f"Invalid version format: {version_str}")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4)
        build = match.group(5)
        
        return cls(major, minor, patch, prerelease, build)
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __lt__(self, other: 'SemanticVersion') -> bool:
        """Compare versions for less than."""
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        
        # Handle prerelease comparison
        if self.prerelease is None and other.prerelease is not None:
            return False  # 1.0.0 > 1.0.0-alpha
        if self.prerelease is not None and other.prerelease is None:
            return True   # 1.0.0-alpha < 1.0.0
        if self.prerelease is not None and other.prerelease is not None:
            return self.prerelease < other.prerelease
        
        return False
    
    def __eq__(self, other: 'SemanticVersion') -> bool:
        """Compare versions for equality."""
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)
    
    def __le__(self, other: 'SemanticVersion') -> bool:
        return self < other or self == other
    
    def __gt__(self, other: 'SemanticVersion') -> bool:
        return not self <= other
    
    def __ge__(self, other: 'SemanticVersion') -> bool:
        return not self < other


@dataclass
class VersionConstraint:
    """Represents a version constraint with type and value."""
    constraint_type: VersionConstraintType
    version: SemanticVersion
    upper_bound: Optional[SemanticVersion] = None
    
    @classmethod
    def parse(cls, constraint_str: str) -> 'VersionConstraint':
        """Parse a constraint string into VersionConstraint."""
        constraint_str = constraint_str.strip()
        
        # Exact match
        if constraint_str.startswith('=='):
            version = SemanticVersion.parse(constraint_str[2:])
            return cls(VersionConstraintType.EXACT, version)
        
        # Greater than or equal
        elif constraint_str.startswith('>='):
            version = SemanticVersion.parse(constraint_str[2:])
            return cls(VersionConstraintType.GREATER_EQUAL, version)
        
        # Less than or equal
        elif constraint_str.startswith('<='):
            version = SemanticVersion.parse(constraint_str[2:])
            return cls(VersionConstraintType.LESS_EQUAL, version)
        
        # Greater than
        elif constraint_str.startswith('>'):
            version = SemanticVersion.parse(constraint_str[1:])
            return cls(VersionConstraintType.GREATER_THAN, version)
        
        # Less than
        elif constraint_str.startswith('<'):
            version = SemanticVersion.parse(constraint_str[1:])
            return cls(VersionConstraintType.LESS_THAN, version)
        
        # Caret constraint (^1.0.0)
        elif constraint_str.startswith('^'):
            version = SemanticVersion.parse(constraint_str[1:])
            return cls(VersionConstraintType.CARET, version)
        
        # Tilde constraint (~1.0.0)
        elif constraint_str.startswith('~'):
            version = SemanticVersion.parse(constraint_str[1:])
            return cls(VersionConstraintType.COMPATIBLE, version)
        
        # Range constraint (1.0.0 - 2.0.0)
        elif ' - ' in constraint_str:
            parts = constraint_str.split(' - ')
            if len(parts) == 2:
                lower = SemanticVersion.parse(parts[0])
                upper = SemanticVersion.parse(parts[1])
                return cls(VersionConstraintType.RANGE, lower, upper)
        
        # Wildcard constraint (1.0.*)
        elif '*' in constraint_str:
            # Convert wildcard to range
            base_version = constraint_str.replace('*', '0')
            version = SemanticVersion.parse(base_version)
            return cls(VersionConstraintType.WILDCARD, version)
        
        # Default to exact match
        else:
            version = SemanticVersion.parse(constraint_str)
            return cls(VersionConstraintType.EXACT, version)


@dataclass
class CompatibilityScore:
    """Represents compatibility score between versions."""
    score: float  # 0.0 to 1.0
    is_compatible: bool
    compatibility_level: str  # "perfect", "high", "medium", "low", "incompatible"
    reasons: List[str]
    suggested_action: Optional[str] = None
    
    @classmethod
    def create(cls, score: float, reasons: List[str]) -> 'CompatibilityScore':
        """Create compatibility score with automatic level calculation."""
        if score >= 1.0:
            level = "perfect"
            compatible = True
        elif score >= 0.8:
            level = "high"
            compatible = True
        elif score >= 0.6:
            level = "medium"
            compatible = True
        elif score >= 0.4:
            level = "low"
            compatible = True  # Changed to True for low but still compatible
        else:
            level = "incompatible"
            compatible = False
        
        return cls(score, compatible, level, reasons)


class SemanticVersionValidator:
    """Advanced semantic version validator with compatibility scoring."""
    
    def __init__(self):
        self.compatibility_cache: Dict[str, CompatibilityScore] = {}
    
    def validate_constraint(self, version: str, constraint: str) -> bool:
        """Validate if a version satisfies a constraint."""
        try:
            sem_version = SemanticVersion.parse(version)
            version_constraint = VersionConstraint.parse(constraint)
            return self._satisfies_constraint(sem_version, version_constraint)
        except ValueError:
            return False
    
    def calculate_compatibility_score(self, 
                                    installed_version: str,
                                    required_constraints: List[str]) -> CompatibilityScore:
        """Calculate compatibility score between installed version and requirements."""
        cache_key = f"{installed_version}:{':'.join(sorted(required_constraints))}"
        
        if cache_key in self.compatibility_cache:
            return self.compatibility_cache[cache_key]
        
        try:
            installed = SemanticVersion.parse(installed_version)
            constraints = [VersionConstraint.parse(c) for c in required_constraints]
            
            score = 0.0
            reasons = []
            satisfied_constraints = 0
            
            for constraint in constraints:
                if self._satisfies_constraint(installed, constraint):
                    satisfied_constraints += 1
                    constraint_score = self._calculate_constraint_score(installed, constraint)
                    score += constraint_score
                    reasons.append(f"Satisfies {constraint.constraint_type.value} constraint")
                else:
                    reasons.append(f"Violates {constraint.constraint_type.value} constraint")
            
            # Normalize score
            if constraints:
                score = score / len(constraints)
            else:
                score = 1.0
            
            # Bonus for satisfying all constraints
            if satisfied_constraints == len(constraints) and satisfied_constraints > 0:
                score = min(1.0, score * 1.1)
            elif satisfied_constraints == 0:
                score = 0.0
            
            compatibility = CompatibilityScore.create(score, reasons)
            compatibility.suggested_action = self._suggest_action(installed, constraints, compatibility)
            
            self.compatibility_cache[cache_key] = compatibility
            return compatibility
            
        except ValueError as e:
            return CompatibilityScore.create(0.0, [f"Version parsing error: {str(e)}"])
    
    def find_compatible_versions(self, 
                                available_versions: List[str],
                                constraints: List[str]) -> List[Tuple[str, CompatibilityScore]]:
        """Find compatible versions from available versions list."""
        compatible_versions = []
        
        for version in available_versions:
            score = self.calculate_compatibility_score(version, constraints)
            if score.is_compatible:
                compatible_versions.append((version, score))
        
        # Sort by compatibility score (descending)
        compatible_versions.sort(key=lambda x: x[1].score, reverse=True)
        return compatible_versions
    
    def suggest_version_resolution(self, 
                                 conflicting_constraints: List[str],
                                 available_versions: List[str] = None) -> Dict[str, Any]:
        """Suggest resolution for conflicting version constraints."""
        suggestions = {
            "resolution_type": "unknown",
            "recommended_version": None,
            "alternative_versions": [],
            "actions_required": [],
            "feasibility": "unknown"
        }
        
        try:
            constraints = [VersionConstraint.parse(c) for c in conflicting_constraints]
            
            # Try to find intersection of all constraints
            intersection = self._find_constraint_intersection(constraints)
            
            if intersection:
                suggestions["resolution_type"] = "intersection"
                suggestions["recommended_version"] = str(intersection)
                suggestions["feasibility"] = "high"
                suggestions["actions_required"] = ["Update to recommended version"]
            
            elif available_versions:
                # Find best compatible version from available versions
                best_matches = []
                for version in available_versions:
                    score = self.calculate_compatibility_score(version, conflicting_constraints)
                    if score.score > 0.5:  # At least medium compatibility
                        best_matches.append((version, score))
                
                if best_matches:
                    best_matches.sort(key=lambda x: x[1].score, reverse=True)
                    suggestions["resolution_type"] = "best_match"
                    suggestions["recommended_version"] = best_matches[0][0]
                    suggestions["alternative_versions"] = [v[0] for v in best_matches[1:3]]
                    suggestions["feasibility"] = "medium"
                    suggestions["actions_required"] = ["Update to best matching version"]
            
            if not suggestions["recommended_version"]:
                suggestions["resolution_type"] = "manual"
                suggestions["feasibility"] = "low"
                suggestions["actions_required"] = [
                    "Manual resolution required",
                    "Consider relaxing version constraints",
                    "Check for alternative packages"
                ]
            
        except Exception as e:
            suggestions["actions_required"] = [f"Error in resolution: {str(e)}"]
        
        return suggestions
    
    def _satisfies_constraint(self, version: SemanticVersion, constraint: VersionConstraint) -> bool:
        """Check if version satisfies constraint."""
        if constraint.constraint_type == VersionConstraintType.EXACT:
            return version == constraint.version
        
        elif constraint.constraint_type == VersionConstraintType.GREATER_THAN:
            return version > constraint.version
        
        elif constraint.constraint_type == VersionConstraintType.GREATER_EQUAL:
            return version >= constraint.version
        
        elif constraint.constraint_type == VersionConstraintType.LESS_THAN:
            return version < constraint.version
        
        elif constraint.constraint_type == VersionConstraintType.LESS_EQUAL:
            return version <= constraint.version
        
        elif constraint.constraint_type == VersionConstraintType.CARET:
            # ^1.2.3 := >=1.2.3 <2.0.0
            if constraint.version.major == 0:
                if constraint.version.minor == 0:
                    # ^0.0.3 := >=0.0.3 <0.0.4
                    return (version.major == 0 and version.minor == 0 and 
                           version.patch >= constraint.version.patch and
                           version.patch < constraint.version.patch + 1)
                else:
                    # ^0.2.3 := >=0.2.3 <0.3.0
                    return (version.major == 0 and 
                           version.minor >= constraint.version.minor and
                           version.minor < constraint.version.minor + 1)
            else:
                return (version.major == constraint.version.major and
                       version >= constraint.version)
        
        elif constraint.constraint_type == VersionConstraintType.COMPATIBLE:
            # ~1.2.3 := >=1.2.3 <1.3.0
            return (version.major == constraint.version.major and
                   version.minor == constraint.version.minor and
                   version.patch >= constraint.version.patch)
        
        elif constraint.constraint_type == VersionConstraintType.RANGE:
            return constraint.version <= version <= constraint.upper_bound
        
        elif constraint.constraint_type == VersionConstraintType.WILDCARD:
            # 1.2.* matches any 1.2.x
            return (version.major == constraint.version.major and
                   version.minor == constraint.version.minor)
        
        return False
    
    def _calculate_constraint_score(self, version: SemanticVersion, constraint: VersionConstraint) -> float:
        """Calculate how well a version matches a constraint."""
        if not self._satisfies_constraint(version, constraint):
            return 0.0
        
        # Perfect match for exact constraints
        if constraint.constraint_type == VersionConstraintType.EXACT:
            return 1.0 if version == constraint.version else 0.0
        
        # For range constraints, score based on position in range
        if constraint.constraint_type == VersionConstraintType.RANGE:
            if constraint.upper_bound:
                # Score based on how close to the middle of the range
                range_size = self._version_distance(constraint.upper_bound, constraint.version)
                version_pos = self._version_distance(version, constraint.version)
                if range_size > 0:
                    return 1.0 - abs(0.5 - (version_pos / range_size))
        
        # For other constraints, score based on semantic distance
        distance = self._semantic_distance(version, constraint.version)
        return max(0.5, 1.0 - distance / 10.0)  # Ensure minimum score for satisfied constraints
    
    def _version_distance(self, v1: SemanticVersion, v2: SemanticVersion) -> float:
        """Calculate distance between two versions."""
        major_diff = abs(v1.major - v2.major) * 100
        minor_diff = abs(v1.minor - v2.minor) * 10
        patch_diff = abs(v1.patch - v2.patch)
        return major_diff + minor_diff + patch_diff
    
    def _semantic_distance(self, v1: SemanticVersion, v2: SemanticVersion) -> float:
        """Calculate semantic distance considering breaking changes."""
        if v1.major != v2.major:
            return 10.0  # Major version difference = high distance
        elif v1.minor != v2.minor:
            return 5.0   # Minor version difference = medium distance
        else:
            return abs(v1.patch - v2.patch) * 0.1  # Patch difference = low distance
    
    def _find_constraint_intersection(self, constraints: List[VersionConstraint]) -> Optional[SemanticVersion]:
        """Find a version that satisfies all constraints."""
        # This is a simplified implementation
        # In practice, this would need more sophisticated constraint solving
        
        # Find the most restrictive lower bound
        lower_bound = None
        upper_bound = None
        
        for constraint in constraints:
            if constraint.constraint_type in [VersionConstraintType.GREATER_THAN, VersionConstraintType.GREATER_EQUAL]:
                if lower_bound is None or constraint.version > lower_bound:
                    lower_bound = constraint.version
            elif constraint.constraint_type in [VersionConstraintType.LESS_THAN, VersionConstraintType.LESS_EQUAL]:
                if upper_bound is None or constraint.version < upper_bound:
                    upper_bound = constraint.version
            elif constraint.constraint_type == VersionConstraintType.EXACT:
                # For exact constraints, check if it satisfies all others
                candidate = constraint.version
                if all(self._satisfies_constraint(candidate, c) for c in constraints):
                    return candidate
        
        # If we have bounds, try to find a version in between
        if lower_bound and upper_bound and lower_bound <= upper_bound:
            return lower_bound
        elif lower_bound:
            return lower_bound
        elif upper_bound:
            return upper_bound
        
        return None
    
    def _suggest_action(self, 
                       installed: SemanticVersion,
                       constraints: List[VersionConstraint],
                       compatibility: CompatibilityScore) -> str:
        """Suggest action based on compatibility analysis."""
        if compatibility.is_compatible:
            if compatibility.score >= 0.9:
                return "No action required - excellent compatibility"
            else:
                return "Consider updating to latest compatible version"
        else:
            # Find what kind of update is needed
            needs_major_update = any(
                c.version.major > installed.major for c in constraints
                if c.constraint_type in [VersionConstraintType.GREATER_THAN, VersionConstraintType.GREATER_EQUAL]
            )
            
            if needs_major_update:
                return "Major version update required - review breaking changes"
            else:
                return "Minor/patch update required"
    
    def clear_cache(self) -> None:
        """Clear the compatibility cache."""
        self.compatibility_cache.clear()