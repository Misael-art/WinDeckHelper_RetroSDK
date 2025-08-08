"""
Data models for dependency graph analysis infrastructure.
Implements DependencyGraph, DependencyNode, and DependencyEdge models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from datetime import datetime


class DependencyType(Enum):
    """Types of dependencies between components."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"
    RUNTIME = "runtime"
    BUILD = "build"


class ConflictType(Enum):
    """Types of conflicts that can occur between dependencies."""
    VERSION_CONFLICT = "version_conflict"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_DEPENDENCY = "missing_dependency"
    INCOMPATIBLE_VERSIONS = "incompatible_versions"


@dataclass
class DependencyNode:
    """Represents a single component in the dependency graph."""
    name: str
    version: Optional[str] = None
    installed_version: Optional[str] = None
    required_version: Optional[str] = None
    component_type: str = "unknown"
    is_installed: bool = False
    installation_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash((self.name, self.version))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DependencyNode):
            return False
        return self.name == other.name and self.version == other.version


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between two components."""
    source: str  # Component that depends on target
    target: str  # Component being depended upon
    dependency_type: DependencyType
    version_constraint: Optional[str] = None
    is_satisfied: bool = False
    conflict_reason: Optional[str] = None
    
    def __hash__(self) -> int:
        return hash((self.source, self.target, self.dependency_type))


@dataclass
class CircularDependency:
    """Represents a circular dependency cycle."""
    cycle_path: List[str]
    cycle_length: int
    severity: str = "high"  # high, medium, low
    
    @property
    def cycle_description(self) -> str:
        return " -> ".join(self.cycle_path + [self.cycle_path[0]])


@dataclass
class VersionConflict:
    """Represents a version conflict between dependencies."""
    component: str
    required_versions: List[str]
    installed_version: Optional[str]
    conflict_type: ConflictType
    conflicting_dependencies: List[str]
    severity: str = "high"
    suggested_resolution: Optional[str] = None


@dataclass
class DependencyGraph:
    """Complete dependency graph with nodes, edges, and analysis results."""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    direct_dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    transitive_dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    version_conflicts: List[VersionConflict] = field(default_factory=list)
    circular_dependencies: List[CircularDependency] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    def add_node(self, node: DependencyNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.name] = node
        if node.name not in self.direct_dependencies:
            self.direct_dependencies[node.name] = set()
        if node.name not in self.transitive_dependencies:
            self.transitive_dependencies[node.name] = set()
    
    def add_edge(self, edge: DependencyEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        
        # Ensure nodes exist
        if edge.source not in self.nodes:
            self.add_node(DependencyNode(name=edge.source))
        if edge.target not in self.nodes:
            self.add_node(DependencyNode(name=edge.target))
        
        # Update direct dependencies
        self.direct_dependencies[edge.source].add(edge.target)
    
    def get_node(self, name: str) -> Optional[DependencyNode]:
        """Get a node by name."""
        return self.nodes.get(name)
    
    def get_dependencies(self, component: str) -> Set[str]:
        """Get direct dependencies of a component."""
        return self.direct_dependencies.get(component, set())
    
    def get_dependents(self, component: str) -> Set[str]:
        """Get components that depend on this component."""
        dependents = set()
        for source, targets in self.direct_dependencies.items():
            if component in targets:
                dependents.add(source)
        return dependents
    
    def has_conflicts(self) -> bool:
        """Check if the graph has any conflicts."""
        return len(self.version_conflicts) > 0 or len(self.circular_dependencies) > 0


@dataclass
class ResolutionPath:
    """Represents a path to resolve dependency conflicts."""
    steps: List[str]
    estimated_time: int  # in minutes
    complexity: str = "medium"  # low, medium, high
    success_probability: float = 0.8
    required_actions: List[str] = field(default_factory=list)
    
    def add_step(self, step: str) -> None:
        """Add a resolution step."""
        self.steps.append(step)
    
    def add_action(self, action: str) -> None:
        """Add a required action."""
        self.required_actions.append(action)


@dataclass
class DependencyAnalysisResult:
    """Complete result of dependency graph analysis."""
    graph: DependencyGraph
    total_components: int
    satisfied_dependencies: int
    unsatisfied_dependencies: int
    conflicts_found: int
    circular_dependencies_found: int
    resolution_paths: List[ResolutionPath] = field(default_factory=list)
    analysis_duration: float = 0.0  # in seconds
    
    @property
    def satisfaction_rate(self) -> float:
        """Calculate the percentage of satisfied dependencies."""
        total = self.satisfied_dependencies + self.unsatisfied_dependencies
        if total == 0:
            return 100.0
        return (self.satisfied_dependencies / total) * 100.0
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues that prevent installation."""
        return self.conflicts_found > 0 or self.circular_dependencies_found > 0