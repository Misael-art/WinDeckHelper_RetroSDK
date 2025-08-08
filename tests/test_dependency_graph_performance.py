"""
Performance tests for Dependency Graph Analyzer.
Tests performance with large graphs and complex scenarios.
"""

import unittest
import time
import random
from typing import List, Dict
from core.dependency_graph_analyzer import DependencyGraphAnalyzer
from core.dependency_graph_models import DependencyType


class TestDependencyGraphPerformance(unittest.TestCase):
    """Performance tests for dependency graph operations."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.analyzer = DependencyGraphAnalyzer()
        self.performance_threshold = 5.0  # 5 seconds max for large operations
    
    def tearDown(self):
        """Clean up after performance tests."""
        self.analyzer.clear_registry()
    
    def test_large_graph_creation_performance(self):
        """Test performance of creating large dependency graphs."""
        # Create a large number of components
        num_components = 1000
        components = []
        
        # Register components with random dependencies
        for i in range(num_components):
            component_name = f"component-{i}"
            components.append(component_name)
            
            # Create random dependencies (0-5 dependencies per component)
            num_deps = random.randint(0, 5)
            dependencies = {}
            
            for j in range(num_deps):
                # Avoid self-dependencies and ensure target exists
                dep_index = random.randint(0, min(i, num_components - 1))
                if dep_index != i:
                    dep_name = f"component-{dep_index}"
                    dependencies[dep_name] = {
                        "type": random.choice(["required", "optional"]),
                        "version_constraint": f">={random.randint(1, 3)}.0.0"
                    }
            
            self.analyzer.register_component(component_name, {
                "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.0",
                "installed_version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.0",
                "is_installed": random.choice([True, False]),
                "type": "library",
                "dependencies": dependencies
            })
        
        # Measure graph creation time
        start_time = time.time()
        graph = self.analyzer.create_dependency_graph(components)
        creation_time = time.time() - start_time
        
        # Verify graph was created correctly
        self.assertEqual(len(graph.nodes), num_components)
        self.assertLessEqual(creation_time, self.performance_threshold)
        
        print(f"Large graph creation ({num_components} components): {creation_time:.2f}s")
    
    def test_large_graph_analysis_performance(self):
        """Test performance of analyzing large dependency graphs."""
        # Create a moderately large graph with known structure
        num_components = 500
        components = self._create_structured_components(num_components)
        
        # Create graph
        graph = self.analyzer.create_dependency_graph(components)
        
        # Measure analysis time
        start_time = time.time()
        result = self.analyzer.analyze_graph(graph)
        analysis_time = time.time() - start_time
        
        # Verify analysis completed
        self.assertIsNotNone(result)
        self.assertEqual(result.total_components, num_components)
        self.assertLessEqual(analysis_time, self.performance_threshold)
        
        print(f"Large graph analysis ({num_components} components): {analysis_time:.2f}s")
    
    def test_circular_dependency_detection_performance(self):
        """Test performance of circular dependency detection in large graphs."""
        # Create components with intentional circular dependencies
        num_components = 200
        components = []
        
        # Create chains that form circles
        for i in range(0, num_components, 10):
            # Create a circular chain of 10 components
            chain_components = []
            for j in range(10):
                component_name = f"chain-{i//10}-component-{j}"
                chain_components.append(component_name)
                components.append(component_name)
            
            # Register components with circular dependencies
            for j, component_name in enumerate(chain_components):
                next_component = chain_components[(j + 1) % len(chain_components)]
                
                self.analyzer.register_component(component_name, {
                    "version": "1.0.0",
                    "installed_version": "1.0.0",
                    "is_installed": True,
                    "type": "library",
                    "dependencies": {
                        next_component: {
                            "type": "required",
                            "version_constraint": ">=1.0.0"
                        }
                    }
                })
        
        # Create graph and measure circular dependency detection
        graph = self.analyzer.create_dependency_graph(components)
        
        start_time = time.time()
        circular_deps = self.analyzer.detect_circular_dependencies(graph)
        detection_time = time.time() - start_time
        
        # Should detect circular dependencies
        self.assertGreater(len(circular_deps), 0)
        self.assertLessEqual(detection_time, self.performance_threshold)
        
        print(f"Circular dependency detection ({num_components} components, {len(circular_deps)} cycles): {detection_time:.2f}s")
    
    def test_version_conflict_detection_performance(self):
        """Test performance of version conflict detection."""
        # Create components with many version conflicts
        num_base_components = 50
        num_dependent_components = 200
        
        # Create base components
        base_components = []
        for i in range(num_base_components):
            component_name = f"base-lib-{i}"
            base_components.append(component_name)
            
            self.analyzer.register_component(component_name, {
                "version": "2.0.0",
                "installed_version": "2.0.0",
                "is_installed": True,
                "type": "library",
                "dependencies": {}
            })
        
        # Create dependent components with conflicting version requirements
        dependent_components = []
        for i in range(num_dependent_components):
            component_name = f"dependent-{i}"
            dependent_components.append(component_name)
            
            # Each dependent requires different versions of base components
            dependencies = {}
            for j in range(min(5, num_base_components)):  # Depend on up to 5 base components
                base_component = base_components[j]
                # Create conflicting version requirements
                version_constraint = f"=={random.choice(['1.0.0', '1.5.0', '2.0.0', '2.5.0'])}"
                dependencies[base_component] = {
                    "type": "required",
                    "version_constraint": version_constraint
                }
            
            self.analyzer.register_component(component_name, {
                "version": "1.0.0",
                "installed_version": "1.0.0",
                "is_installed": True,
                "type": "application",
                "dependencies": dependencies
            })
        
        # Create graph and measure conflict detection
        all_components = base_components + dependent_components
        graph = self.analyzer.create_dependency_graph(all_components)
        
        start_time = time.time()
        conflicts = self.analyzer.detect_version_conflicts(graph)
        detection_time = time.time() - start_time
        
        # Should detect version conflicts
        self.assertGreater(len(conflicts), 0)
        self.assertLessEqual(detection_time, self.performance_threshold)
        
        print(f"Version conflict detection ({len(all_components)} components, {len(conflicts)} conflicts): {detection_time:.2f}s")
    
    def test_resolution_path_calculation_performance(self):
        """Test performance of resolution path calculation."""
        # Create a complex graph with multiple conflicts
        components = self._create_complex_conflict_scenario()
        
        graph = self.analyzer.create_dependency_graph(components)
        
        # Add some conflicts manually to ensure we have them
        from core.dependency_graph_models import VersionConflict, ConflictType, CircularDependency
        
        # Add version conflicts
        for i in range(10):
            conflict = VersionConflict(
                component=f"shared-lib-{i}",
                required_versions=["1.0.0", "2.0.0", "3.0.0"],
                installed_version="1.5.0",
                conflict_type=ConflictType.VERSION_CONFLICT,
                conflicting_dependencies=[f"app-{j}" for j in range(3)],
                suggested_resolution="Update to version 2.0.0"
            )
            graph.version_conflicts.append(conflict)
        
        # Add circular dependencies
        for i in range(5):
            circular = CircularDependency(
                cycle_path=[f"comp-{i}", f"comp-{i+1}", f"comp-{i+2}"],
                cycle_length=3,
                severity="high"
            )
            graph.circular_dependencies.append(circular)
        
        # Measure resolution path calculation
        start_time = time.time()
        resolution_path = self.analyzer.calculate_shortest_resolution_path(graph)
        calculation_time = time.time() - start_time
        
        # Should generate a resolution path
        self.assertIsNotNone(resolution_path)
        self.assertGreater(len(resolution_path.steps), 0)
        self.assertLessEqual(calculation_time, self.performance_threshold)
        
        print(f"Resolution path calculation (15 conflicts): {calculation_time:.2f}s")
    
    def test_visualization_performance(self):
        """Test performance of graph visualization."""
        # Create a large graph
        num_components = 300
        components = self._create_structured_components(num_components)
        
        graph = self.analyzer.create_dependency_graph(components)
        
        # Measure visualization time
        start_time = time.time()
        visualization = self.analyzer.visualize_dependencies(graph)
        visualization_time = time.time() - start_time
        
        # Should generate visualization
        self.assertIsInstance(visualization, str)
        self.assertIn("Dependency Graph Visualization", visualization)
        self.assertLessEqual(visualization_time, 2.0)  # Visualization should be fast
        
        print(f"Graph visualization ({num_components} components): {visualization_time:.2f}s")
    
    def test_memory_usage_large_graph(self):
        """Test memory usage with large graphs."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a very large graph
        num_components = 2000
        components = self._create_structured_components(num_components)
        
        graph = self.analyzer.create_dependency_graph(components)
        result = self.analyzer.analyze_graph(graph)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 2000 components)
        self.assertLess(memory_increase, 100)
        
        print(f"Memory usage for {num_components} components: {memory_increase:.1f}MB increase")
    
    def test_concurrent_analysis_performance(self):
        """Test performance of concurrent graph analysis."""
        import threading
        import concurrent.futures
        
        # Create multiple smaller graphs
        num_graphs = 10
        components_per_graph = 100
        
        def analyze_graph(graph_id):
            """Analyze a single graph."""
            analyzer = DependencyGraphAnalyzer()
            components = self._create_structured_components(components_per_graph, prefix=f"g{graph_id}")
            
            # Register components
            for i, component in enumerate(components):
                analyzer.register_component(component, {
                    "version": "1.0.0",
                    "installed_version": "1.0.0",
                    "is_installed": True,
                    "type": "library",
                    "dependencies": {}
                })
            
            graph = analyzer.create_dependency_graph(components)
            result = analyzer.analyze_graph(graph)
            return result.analysis_duration
        
        # Measure concurrent analysis time
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_graph, i) for i in range(num_graphs)]
            analysis_times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Should complete all analyses
        self.assertEqual(len(analysis_times), num_graphs)
        self.assertLessEqual(total_time, self.performance_threshold)
        
        avg_analysis_time = sum(analysis_times) / len(analysis_times)
        print(f"Concurrent analysis ({num_graphs} graphs): {total_time:.2f}s total, {avg_analysis_time:.3f}s avg per graph")
    
    def _create_structured_components(self, num_components: int, prefix: str = "comp") -> List[str]:
        """Create components with a structured dependency pattern."""
        components = []
        
        for i in range(num_components):
            component_name = f"{prefix}-{i}"
            components.append(component_name)
            
            # Create dependencies in a structured way
            dependencies = {}
            
            # Each component depends on a few previous components
            num_deps = min(3, i)  # Depend on up to 3 previous components
            for j in range(num_deps):
                dep_index = i - j - 1
                if dep_index >= 0:
                    dep_name = f"{prefix}-{dep_index}"
                    dependencies[dep_name] = {
                        "type": "required",
                        "version_constraint": ">=1.0.0"
                    }
            
            self.analyzer.register_component(component_name, {
                "version": "1.0.0",
                "installed_version": "1.0.0",
                "is_installed": True,
                "type": "library",
                "dependencies": dependencies
            })
        
        return components
    
    def _create_complex_conflict_scenario(self) -> List[str]:
        """Create a complex scenario with multiple types of conflicts."""
        components = []
        
        # Create shared libraries
        shared_libs = []
        for i in range(20):
            lib_name = f"shared-lib-{i}"
            shared_libs.append(lib_name)
            components.append(lib_name)
            
            self.analyzer.register_component(lib_name, {
                "version": "2.0.0",
                "installed_version": "1.5.0",  # Different from required
                "is_installed": True,
                "type": "library",
                "dependencies": {}
            })
        
        # Create applications that depend on shared libraries
        for i in range(50):
            app_name = f"app-{i}"
            components.append(app_name)
            
            # Each app depends on several shared libraries with different version requirements
            dependencies = {}
            for j in range(min(5, len(shared_libs))):
                lib_name = shared_libs[j]
                # Create conflicting version requirements
                version_req = random.choice([">=1.0.0", ">=2.0.0", "==1.5.0", "==2.0.0"])
                dependencies[lib_name] = {
                    "type": "required",
                    "version_constraint": version_req
                }
            
            self.analyzer.register_component(app_name, {
                "version": "1.0.0",
                "installed_version": "1.0.0",
                "is_installed": True,
                "type": "application",
                "dependencies": dependencies
            })
        
        return components


class TestDependencyGraphScalability(unittest.TestCase):
    """Scalability tests for dependency graph operations."""
    
    def test_scalability_with_increasing_size(self):
        """Test how performance scales with increasing graph size."""
        sizes = [50, 100, 200, 500]
        times = []
        
        for size in sizes:
            analyzer = DependencyGraphAnalyzer()
            
            # Create components
            components = []
            for i in range(size):
                component_name = f"comp-{i}"
                components.append(component_name)
                
                # Create dependencies (each component depends on 2-3 previous ones)
                dependencies = {}
                num_deps = min(3, i)
                for j in range(num_deps):
                    dep_name = f"comp-{i - j - 1}"
                    dependencies[dep_name] = {
                        "type": "required",
                        "version_constraint": ">=1.0.0"
                    }
                
                analyzer.register_component(component_name, {
                    "version": "1.0.0",
                    "installed_version": "1.0.0",
                    "is_installed": True,
                    "type": "library",
                    "dependencies": dependencies
                })
            
            # Measure time for complete analysis
            start_time = time.time()
            graph = analyzer.create_dependency_graph(components)
            result = analyzer.analyze_graph(graph)
            total_time = time.time() - start_time
            
            times.append(total_time)
            print(f"Size {size}: {total_time:.3f}s")
            
            analyzer.clear_registry()
        
        # Check that time complexity is reasonable (should be roughly O(n) or O(n log n))
        # Time shouldn't increase exponentially
        for i in range(1, len(times)):
            size_ratio = sizes[i] / sizes[i-1]
            time_ratio = times[i] / times[i-1]
            
            # Time ratio should not be much larger than size ratio squared
            self.assertLess(time_ratio, size_ratio ** 2, 
                          f"Performance degradation too severe: size ratio {size_ratio:.1f}, time ratio {time_ratio:.1f}")


if __name__ == '__main__':
    # Run performance tests with verbose output
    unittest.main(verbosity=2)