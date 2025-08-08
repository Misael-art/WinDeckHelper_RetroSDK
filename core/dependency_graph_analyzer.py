"""
Dependency Graph Analyzer for Environment Dev Deep Evaluation.
Implements graph creation, analysis, and visualization capabilities.
"""

import time
import asyncio
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import defaultdict, deque
import logging

from .dependency_graph_models import (
    DependencyGraph, DependencyNode, DependencyEdge, DependencyType,
    CircularDependency, VersionConflict, ConflictType, ResolutionPath,
    DependencyAnalysisResult
)
from .semantic_version_validator import SemanticVersionValidator, CompatibilityScore
from .package_manager_resolver import PackageManagerResolver, PackageManagerType


class DependencyGraphAnalyzer:
    """
    Analyzes dependency graphs for components and detects conflicts.
    Implements graph creation, cycle detection, and resolution path calculation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._component_registry: Dict[str, Dict[str, Any]] = {}
        self.semantic_validator = SemanticVersionValidator()
        self.package_resolver = PackageManagerResolver()
    
    def create_dependency_graph(self, components: List[str]) -> DependencyGraph:
        """
        Create a dependency graph from a list of components.
        
        Args:
            components: List of component names to analyze
            
        Returns:
            DependencyGraph: Complete dependency graph with nodes and edges
        """
        graph = DependencyGraph()
        
        # Add all components as nodes
        for component in components:
            node = self._create_node_for_component(component)
            graph.add_node(node)
        
        # Build edges based on dependencies
        for component in components:
            dependencies = self._get_component_dependencies(component)
            for dep_name, dep_info in dependencies.items():
                edge = DependencyEdge(
                    source=component,
                    target=dep_name,
                    dependency_type=DependencyType(dep_info.get('type', 'required')),
                    version_constraint=dep_info.get('version_constraint'),
                    is_satisfied=self._check_dependency_satisfaction(component, dep_name, dep_info)
                )
                graph.add_edge(edge)
        
        # Calculate transitive dependencies
        self._calculate_transitive_dependencies(graph)
        
        return graph
    
    def analyze_graph(self, graph: DependencyGraph) -> DependencyAnalysisResult:
        """
        Perform complete analysis of the dependency graph.
        
        Args:
            graph: DependencyGraph to analyze
            
        Returns:
            DependencyAnalysisResult: Complete analysis results
        """
        start_time = time.time()
        
        # Detect circular dependencies
        circular_deps = self.detect_circular_dependencies(graph)
        graph.circular_dependencies = circular_deps
        
        # Detect version conflicts
        version_conflicts = self.detect_version_conflicts(graph)
        graph.version_conflicts = version_conflicts
        
        # Calculate statistics
        satisfied_deps = sum(1 for edge in graph.edges if edge.is_satisfied)
        unsatisfied_deps = len(graph.edges) - satisfied_deps
        
        # Generate resolution paths
        resolution_paths = self._generate_resolution_paths(graph)
        
        analysis_duration = time.time() - start_time
        
        return DependencyAnalysisResult(
            graph=graph,
            total_components=len(graph.nodes),
            satisfied_dependencies=satisfied_deps,
            unsatisfied_dependencies=unsatisfied_deps,
            conflicts_found=len(version_conflicts),
            circular_dependencies_found=len(circular_deps),
            resolution_paths=resolution_paths,
            analysis_duration=analysis_duration
        )
    
    def detect_circular_dependencies(self, graph: DependencyGraph) -> List[CircularDependency]:
        """
        Detect circular dependencies using DFS-based cycle detection.
        
        Args:
            graph: DependencyGraph to analyze
            
        Returns:
            List[CircularDependency]: List of detected circular dependencies
        """
        circular_deps = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs_visit(node: str) -> bool:
            """DFS visit function for cycle detection."""
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle_path = path[cycle_start:] + [node]
                circular_deps.append(CircularDependency(
                    cycle_path=cycle_path,
                    cycle_length=len(cycle_path) - 1,
                    severity=self._calculate_cycle_severity(cycle_path)
                ))
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visit all dependencies
            for dependency in graph.get_dependencies(node):
                if dfs_visit(dependency):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        # Check all nodes for cycles
        for node_name in graph.nodes:
            if node_name not in visited:
                dfs_visit(node_name)
        
        return circular_deps
    
    def detect_version_conflicts(self, graph: DependencyGraph) -> List[VersionConflict]:
        """
        Detect version conflicts between dependencies.
        
        Args:
            graph: DependencyGraph to analyze
            
        Returns:
            List[VersionConflict]: List of detected version conflicts
        """
        conflicts = []
        
        # Group dependencies by target component
        component_requirements = defaultdict(list)
        for edge in graph.edges:
            if edge.version_constraint:
                component_requirements[edge.target].append({
                    'source': edge.source,
                    'constraint': edge.version_constraint,
                    'type': edge.dependency_type
                })
        
        # Check for conflicts in each component
        for component, requirements in component_requirements.items():
            if len(requirements) > 1:
                # Multiple version requirements - check for conflicts
                versions = [req['constraint'] for req in requirements]
                if not self._are_versions_compatible(versions):
                    node = graph.get_node(component)
                    conflict = VersionConflict(
                        component=component,
                        required_versions=versions,
                        installed_version=node.installed_version if node else None,
                        conflict_type=ConflictType.VERSION_CONFLICT,
                        conflicting_dependencies=[req['source'] for req in requirements],
                        severity=self._calculate_conflict_severity(requirements),
                        suggested_resolution=self._suggest_version_resolution(versions)
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def calculate_shortest_resolution_path(self, graph: DependencyGraph) -> Optional[ResolutionPath]:
        """
        Calculate the shortest path to resolve all conflicts in the graph.
        
        Args:
            graph: DependencyGraph with conflicts to resolve
            
        Returns:
            Optional[ResolutionPath]: Shortest resolution path or None if no resolution possible
        """
        if not graph.has_conflicts():
            return ResolutionPath(steps=["No conflicts to resolve"], estimated_time=0)
        
        resolution_steps = []
        estimated_time = 0
        
        # Resolve circular dependencies first (highest priority)
        for circular_dep in graph.circular_dependencies:
            step = f"Break circular dependency: {circular_dep.cycle_description}"
            resolution_steps.append(step)
            estimated_time += self._estimate_circular_resolution_time(circular_dep)
        
        # Resolve version conflicts
        for conflict in graph.version_conflicts:
            step = f"Resolve version conflict for {conflict.component}: {conflict.suggested_resolution}"
            resolution_steps.append(step)
            estimated_time += self._estimate_conflict_resolution_time(conflict)
        
        return ResolutionPath(
            steps=resolution_steps,
            estimated_time=estimated_time,
            complexity=self._calculate_resolution_complexity(graph),
            success_probability=self._calculate_success_probability(graph),
            required_actions=self._generate_required_actions(graph)
        )
    
    def visualize_dependencies(self, graph: DependencyGraph) -> str:
        """
        Generate a text-based visualization of the dependency graph.
        
        Args:
            graph: DependencyGraph to visualize
            
        Returns:
            str: Text representation of the graph
        """
        lines = ["Dependency Graph Visualization", "=" * 30, ""]
        
        # Show nodes
        lines.append("Components:")
        for name, node in graph.nodes.items():
            status = "✓" if node.is_installed else "✗"
            version_info = f" (v{node.installed_version})" if node.installed_version else ""
            lines.append(f"  {status} {name}{version_info}")
        
        lines.append("")
        
        # Show dependencies
        lines.append("Dependencies:")
        for component, deps in graph.direct_dependencies.items():
            if deps:
                lines.append(f"  {component} depends on:")
                for dep in sorted(deps):
                    lines.append(f"    → {dep}")
        
        # Show conflicts
        if graph.version_conflicts:
            lines.append("")
            lines.append("Version Conflicts:")
            for conflict in graph.version_conflicts:
                lines.append(f"  ⚠ {conflict.component}: {', '.join(conflict.required_versions)}")
        
        # Show circular dependencies
        if graph.circular_dependencies:
            lines.append("")
            lines.append("Circular Dependencies:")
            for circular in graph.circular_dependencies:
                lines.append(f"  🔄 {circular.cycle_description}")
        
        return "\n".join(lines)
    
    def _create_node_for_component(self, component: str) -> DependencyNode:
        """Create a dependency node for a component."""
        # This would integrate with the detection engine in a real implementation
        component_info = self._component_registry.get(component, {})
        
        return DependencyNode(
            name=component,
            version=component_info.get('version'),
            installed_version=component_info.get('installed_version'),
            required_version=component_info.get('required_version'),
            component_type=component_info.get('type', 'unknown'),
            is_installed=component_info.get('is_installed', False),
            installation_path=component_info.get('installation_path'),
            metadata=component_info.get('metadata', {})
        )
    
    def _get_component_dependencies(self, component: str) -> Dict[str, Dict[str, Any]]:
        """Get dependencies for a component."""
        # This would integrate with component metadata in a real implementation
        component_info = self._component_registry.get(component, {})
        return component_info.get('dependencies', {})
    
    def _calculate_transitive_dependencies(self, graph: DependencyGraph) -> None:
        """Calculate transitive dependencies for all nodes."""
        for node_name in graph.nodes:
            visited = set()
            self._dfs_transitive(graph, node_name, visited)
            graph.transitive_dependencies[node_name] = visited - {node_name}
    
    def _dfs_transitive(self, graph: DependencyGraph, node: str, visited: Set[str]) -> None:
        """DFS helper for calculating transitive dependencies."""
        if node in visited:
            return
        
        visited.add(node)
        for dependency in graph.get_dependencies(node):
            self._dfs_transitive(graph, dependency, visited)
    
    def _check_dependency_satisfaction(self, source: str, target: str, dep_info: Dict[str, Any]) -> bool:
        """Check if a dependency is satisfied."""
        target_info = self._component_registry.get(target, {})
        
        if not target_info.get('is_installed', False):
            return False
        
        version_constraint = dep_info.get('version_constraint')
        if version_constraint and target_info.get('installed_version'):
            return self._version_satisfies_constraint(
                target_info['installed_version'],
                version_constraint
            )
        
        return True
    
    def _are_versions_compatible(self, versions: List[str]) -> bool:
        """Check if multiple version constraints are compatible."""
        # Simplified version compatibility check
        # In a real implementation, this would use proper semantic versioning
        unique_versions = set(versions)
        return len(unique_versions) <= 1
    
    def _version_satisfies_constraint(self, version: str, constraint: str) -> bool:
        """Check if a version satisfies a constraint."""
        # Simplified version constraint checking
        # In a real implementation, this would use proper semantic versioning
        if constraint.startswith('>='):
            return version >= constraint[2:]
        elif constraint.startswith('<='):
            return version <= constraint[2:]
        elif constraint.startswith('>'):
            return version > constraint[1:]
        elif constraint.startswith('<'):
            return version < constraint[1:]
        elif constraint.startswith('=='):
            return version == constraint[2:]
        else:
            return version == constraint
    
    def _calculate_cycle_severity(self, cycle_path: List[str]) -> str:
        """Calculate severity of a circular dependency."""
        if len(cycle_path) <= 3:
            return "high"
        elif len(cycle_path) <= 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_conflict_severity(self, requirements: List[Dict[str, Any]]) -> str:
        """Calculate severity of a version conflict."""
        runtime_deps = sum(1 for req in requirements if req['type'] == DependencyType.RUNTIME)
        if runtime_deps > 0:
            return "high"
        elif len(requirements) > 2:
            return "medium"
        else:
            return "low"
    
    def _suggest_version_resolution(self, versions: List[str]) -> str:
        """Suggest a resolution for version conflicts."""
        # Simplified resolution suggestion
        return f"Consider using version {max(versions)} or find compatible versions"
    
    def _generate_resolution_paths(self, graph: DependencyGraph) -> List[ResolutionPath]:
        """Generate possible resolution paths for conflicts."""
        paths = []
        
        if graph.has_conflicts():
            main_path = self.calculate_shortest_resolution_path(graph)
            if main_path:
                paths.append(main_path)
        
        return paths
    
    def _estimate_circular_resolution_time(self, circular_dep: CircularDependency) -> int:
        """Estimate time to resolve a circular dependency."""
        base_time = 15  # minutes
        return base_time * circular_dep.cycle_length
    
    def _estimate_conflict_resolution_time(self, conflict: VersionConflict) -> int:
        """Estimate time to resolve a version conflict."""
        base_time = 10  # minutes
        multiplier = len(conflict.conflicting_dependencies)
        return base_time * multiplier
    
    def _calculate_resolution_complexity(self, graph: DependencyGraph) -> str:
        """Calculate overall resolution complexity."""
        total_issues = len(graph.version_conflicts) + len(graph.circular_dependencies)
        
        if total_issues == 0:
            return "low"
        elif total_issues <= 2:
            return "medium"
        else:
            return "high"
    
    def _calculate_success_probability(self, graph: DependencyGraph) -> float:
        """Calculate probability of successful resolution."""
        base_probability = 0.9
        
        # Reduce probability based on complexity
        penalty_per_conflict = 0.1
        penalty_per_circular = 0.15
        
        total_penalty = (len(graph.version_conflicts) * penalty_per_conflict +
                        len(graph.circular_dependencies) * penalty_per_circular)
        
        return max(0.1, base_probability - total_penalty)
    
    def _generate_required_actions(self, graph: DependencyGraph) -> List[str]:
        """Generate list of required actions to resolve conflicts."""
        actions = []
        
        if graph.circular_dependencies:
            actions.append("Break circular dependencies by refactoring component relationships")
        
        if graph.version_conflicts:
            actions.append("Update or downgrade conflicting component versions")
            actions.append("Review and update version constraints")
        
        return actions
    
    def register_component(self, name: str, info: Dict[str, Any]) -> None:
        """Register component information for analysis."""
        self._component_registry[name] = info
    
    def validate_contextual_compatibility(self, component: str) -> Dict[str, Any]:
        """
        Validate contextual compatibility between existing and required versions.
        
        Args:
            component: Component name to validate
            
        Returns:
            Dict containing compatibility analysis and suggestions
        """
        component_info = self._component_registry.get(component, {})
        installed_version = component_info.get('installed_version')
        required_constraints = []
        
        # Collect all version constraints for this component
        for comp_name, comp_info in self._component_registry.items():
            dependencies = comp_info.get('dependencies', {})
            if component in dependencies:
                constraint = dependencies[component].get('version_constraint')
                if constraint:
                    required_constraints.append(constraint)
        
        if not installed_version or not required_constraints:
            return {
                "component": component,
                "compatibility_score": None,
                "is_compatible": True,
                "suggestions": ["No version constraints to validate"],
                "required_actions": []
            }
        
        # Calculate compatibility score
        compatibility = self.semantic_validator.calculate_compatibility_score(
            installed_version, required_constraints
        )
        
        # Generate suggestions
        suggestions = []
        required_actions = []
        
        if not compatibility.is_compatible:
            # Try to find compatible version using package manager
            manager_type = self._detect_package_manager_for_component(component)
            if manager_type:
                try:
                    # Run async operation in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        compatible_version = loop.run_until_complete(
                            self.package_resolver.find_compatible_version(
                                component, manager_type, required_constraints
                            )
                        )
                        if compatible_version:
                            suggestions.append(f"Update to version {compatible_version}")
                            required_actions.append(f"Update {component} to {compatible_version}")
                        else:
                            suggestions.append("No compatible version found in package manager")
                            required_actions.append("Manual resolution required")
                    finally:
                        loop.close()
                except Exception as e:
                    self.logger.warning(f"Could not query package manager: {str(e)}")
                    suggestions.append("Check package manager for compatible versions")
            else:
                suggestions.append("Manual version resolution required")
                required_actions.append("Update component version manually")
        else:
            if compatibility.score < 0.8:
                suggestions.append("Consider updating to latest compatible version")
        
        return {
            "component": component,
            "installed_version": installed_version,
            "required_constraints": required_constraints,
            "compatibility_score": compatibility,
            "is_compatible": compatibility.is_compatible,
            "suggestions": suggestions,
            "required_actions": required_actions
        }
    
    async def resolve_dependencies_with_package_managers(self, 
                                                       components: List[str]) -> Dict[str, Any]:
        """
        Resolve dependencies using package managers for automatic resolution.
        
        Args:
            components: List of components to resolve
            
        Returns:
            Dict containing resolution results and suggestions
        """
        resolution_results = {}
        
        for component in components:
            component_info = self._component_registry.get(component, {})
            manager_type = self._detect_package_manager_for_component(component)
            
            if manager_type:
                try:
                    # Get dependency resolution from package manager
                    resolution = await self.package_resolver.resolve_dependencies(
                        component, manager_type
                    )
                    
                    if resolution["success"]:
                        # Check for conflicts in resolved dependencies
                        conflicts = await self.package_resolver.check_dependency_conflicts(
                            {dep["name"]: dep["constraint"] for dep in resolution["dependencies"]},
                            manager_type
                        )
                        
                        resolution_results[component] = {
                            "manager": manager_type.value,
                            "resolution": resolution,
                            "conflicts": conflicts,
                            "status": "resolved" if not conflicts else "conflicts_found"
                        }
                    else:
                        resolution_results[component] = {
                            "manager": manager_type.value,
                            "error": resolution["error"],
                            "status": "failed"
                        }
                        
                except Exception as e:
                    resolution_results[component] = {
                        "manager": manager_type.value if manager_type else "unknown",
                        "error": str(e),
                        "status": "error"
                    }
            else:
                resolution_results[component] = {
                    "manager": "none",
                    "status": "no_manager_detected"
                }
        
        return {
            "results": resolution_results,
            "summary": self._generate_resolution_summary(resolution_results),
            "recommendations": self._generate_resolution_recommendations(resolution_results)
        }
    
    def suggest_alternatives_for_conflicts(self, 
                                         conflicts: List[VersionConflict]) -> Dict[str, List[str]]:
        """
        Suggest alternative solutions for conflicting dependencies.
        
        Args:
            conflicts: List of version conflicts to resolve
            
        Returns:
            Dict mapping component names to alternative suggestions
        """
        alternatives = {}
        
        for conflict in conflicts:
            component_alternatives = []
            
            # Use semantic validator to suggest resolution
            resolution_suggestion = self.semantic_validator.suggest_version_resolution(
                conflict.required_versions
            )
            
            if resolution_suggestion["recommended_version"]:
                component_alternatives.append(
                    f"Update to version {resolution_suggestion['recommended_version']}"
                )
            
            # Add alternative versions if available
            for alt_version in resolution_suggestion.get("alternative_versions", []):
                component_alternatives.append(f"Consider version {alt_version}")
            
            # Add package manager specific suggestions
            manager_type = self._detect_package_manager_for_component(conflict.component)
            if manager_type:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        available_versions = loop.run_until_complete(
                            self.package_resolver.get_available_versions(
                                conflict.component, manager_type
                            )
                        )
                        
                        if available_versions:
                            compatible_versions = self.semantic_validator.find_compatible_versions(
                                available_versions[:10], conflict.required_versions
                            )
                            
                            for version, score in compatible_versions[:3]:
                                component_alternatives.append(
                                    f"Available compatible version: {version} (score: {score.score:.2f})"
                                )
                    finally:
                        loop.close()
                except Exception as e:
                    self.logger.warning(f"Could not get alternatives from package manager: {str(e)}")
            
            # Add generic alternatives
            if not component_alternatives:
                component_alternatives.extend([
                    "Relax version constraints if possible",
                    "Look for alternative packages with similar functionality",
                    "Consider using a different version of dependent packages"
                ])
            
            alternatives[conflict.component] = component_alternatives
        
        return alternatives
    
    def _detect_package_manager_for_component(self, component: str) -> Optional[PackageManagerType]:
        """Detect appropriate package manager for a component."""
        component_info = self._component_registry.get(component, {})
        component_type = component_info.get('type', '').lower()
        
        # Map component types to package managers
        if component_type in ['npm', 'node', 'javascript', 'js']:
            return PackageManagerType.NPM
        elif component_type in ['pip', 'python', 'py']:
            return PackageManagerType.PIP
        elif component_type in ['conda', 'anaconda']:
            return PackageManagerType.CONDA
        elif component_type in ['yarn']:
            return PackageManagerType.YARN
        
        # Try to detect from component name patterns
        if 'node' in component.lower() or 'npm' in component.lower():
            return PackageManagerType.NPM
        elif 'python' in component.lower() or 'pip' in component.lower():
            return PackageManagerType.PIP
        elif 'conda' in component.lower() or 'anaconda' in component.lower():
            return PackageManagerType.CONDA
        
        return None
    
    def _generate_resolution_summary(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Generate summary statistics for resolution results."""
        summary = {
            "total_components": len(results),
            "resolved": 0,
            "conflicts_found": 0,
            "failed": 0,
            "no_manager": 0
        }
        
        for result in results.values():
            status = result.get("status", "unknown")
            if status == "resolved":
                summary["resolved"] += 1
            elif status == "conflicts_found":
                summary["conflicts_found"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "no_manager_detected":
                summary["no_manager"] += 1
        
        return summary
    
    def _generate_resolution_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on resolution results."""
        recommendations = []
        
        failed_components = [name for name, result in results.items() 
                           if result.get("status") == "failed"]
        conflict_components = [name for name, result in results.items() 
                             if result.get("status") == "conflicts_found"]
        no_manager_components = [name for name, result in results.items() 
                               if result.get("status") == "no_manager_detected"]
        
        if failed_components:
            recommendations.append(
                f"Failed to resolve dependencies for: {', '.join(failed_components)}. "
                "Check package manager availability and network connectivity."
            )
        
        if conflict_components:
            recommendations.append(
                f"Dependency conflicts found in: {', '.join(conflict_components)}. "
                "Review version constraints and consider updating packages."
            )
        
        if no_manager_components:
            recommendations.append(
                f"No package manager detected for: {', '.join(no_manager_components)}. "
                "Manual dependency management may be required."
            )
        
        if not failed_components and not conflict_components:
            recommendations.append("All dependencies resolved successfully!")
        
        return recommendations
    
    def clear_registry(self) -> None:
        """Clear the component registry and caches."""
        self._component_registry.clear()
        self.semantic_validator.clear_cache()
        self.package_resolver.clear_cache()