# -*- coding: utf-8 -*-
"""
Documentation Generator

This module implements comprehensive documentation generation for the Environment Dev Deep Evaluation system,
including analysis documents, architecture documentation, gap analysis reports, and developer documentation.

Requirements addressed:
- 12.3: Detailed analysis document with current vs. proposed architecture mapping
- 12.4: Comprehensive gap analysis report with prioritized fixes
- 12.3: Updated architecture diagrams and documentation
- 12.4: Developer documentation for system architecture and APIs
"""

import logging
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import markdown
import jinja2

try:
    from .security_manager import SecurityManager, SecurityLevel
    from .architecture_analysis_engine import ArchitectureAnalysisEngine, ArchitectureAnalysis, ComparisonResult
    from .unified_detection_engine import UnifiedDetectionEngine
    from .dependency_validation_system import DependencyValidationSystem
    from .robust_download_manager import RobustDownloadManager
    from .advanced_installation_manager import AdvancedInstallationManager
    from .steamdeck_integration_layer import SteamDeckIntegrationLayer
    from .intelligent_storage_manager import IntelligentStorageManager
    from .plugin_system_manager import PluginSystemManager
    from .modern_frontend_manager import ModernFrontendManager
except ImportError:
    from security_manager import SecurityManager, SecurityLevel
    from architecture_analysis_engine import ArchitectureAnalysisEngine, ArchitectureAnalysis, ComparisonResult
    from unified_detection_engine import UnifiedDetectionEngine
    from dependency_validation_system import DependencyValidationSystem
    from robust_download_manager import RobustDownloadManager
    from advanced_installation_manager import AdvancedInstallationManager
    from steamdeck_integration_layer import SteamDeckIntegrationLayer
    from intelligent_storage_manager import IntelligentStorageManager
    from plugin_system_manager import PluginSystemManager
    from modern_frontend_manager import ModernFrontendManager


class DocumentationType(Enum):
    """Types of documentation to generate"""
    ANALYSIS_DOCUMENT = "analysis_document"
    ARCHITECTURE_DOCUMENTATION = "architecture_documentation"
    GAP_ANALYSIS_REPORT = "gap_analysis_report"
    DEVELOPER_DOCUMENTATION = "developer_documentation"
    API_DOCUMENTATION = "api_documentation"
    USER_GUIDE = "user_guide"
    DEPLOYMENT_GUIDE = "deployment_guide"


class DocumentFormat(Enum):
    """Documentation output formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    RESTRUCTURED_TEXT = "rst"


@dataclass
class DocumentSection:
    """Documentation section definition"""
    section_id: str
    title: str
    content: str
    subsections: List['DocumentSection'] = field(default_factory=list)
    diagrams: List[str] = field(default_factory=list)
    code_examples: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureDiagram:
    """Architecture diagram definition"""
    diagram_id: str
    title: str
    description: str
    diagram_type: str  # mermaid, plantuml, etc.
    diagram_content: str
    components_shown: List[str] = field(default_factory=list)
    relationships_shown: List[str] = field(default_factory=list)


@dataclass
class GapAnalysisItem:
    """Gap analysis item"""
    gap_id: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    category: str  # security, stability, functionality, ux
    current_state: str
    desired_state: str
    impact_assessment: str
    recommended_actions: List[str] = field(default_factory=list)
    effort_estimate: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DocumentationResult:
    """Documentation generation result"""
    success: bool
    documents_generated: List[str] = field(default_factory=list)
    diagrams_generated: List[str] = field(default_factory=list)
    total_pages: int = 0
    total_sections: int = 0
    output_directory: str = ""
    error_message: Optional[str] = None
    generation_time: float = 0.0


class DocumentationGenerator:
    """
    Comprehensive Documentation Generator
    
    Provides:
    - Analysis document generation with architecture mapping
    - Gap analysis reports with prioritized fixes
    - Architecture diagrams and documentation
    - Developer documentation for APIs and system architecture
    - User guides and deployment documentation
    """
    
    def __init__(self,
                 security_manager: Optional[SecurityManager] = None,
                 output_directory: str = "documentation",
                 template_directory: str = "templates",
                 enable_diagrams: bool = True):
        """
        Initialize Documentation Generator
        
        Args:
            security_manager: Security manager for auditing
            output_directory: Directory for generated documentation
            template_directory: Directory containing documentation templates
            enable_diagrams: Whether to generate diagrams
        """
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.security_manager = security_manager or SecurityManager()
        
        # Configuration
        self.output_directory = Path(output_directory)
        self.template_directory = Path(template_directory)
        self.enable_diagrams = enable_diagrams
        
        # Documentation data
        self.document_sections: Dict[str, List[DocumentSection]] = {}
        self.architecture_diagrams: Dict[str, ArchitectureDiagram] = {}
        self.gap_analysis_items: List[GapAnalysisItem] = []
        
        # Component instances for analysis
        self.components: Dict[str, Any] = {}
        
        # Template engine
        self.template_env = None
        
        # Initialize generator
        self._initialize_generator()
        
        self.logger.info("Documentation Generator initialized")
    
    def generate_comprehensive_documentation(self) -> DocumentationResult:
        """
        Generate comprehensive documentation suite
        
        Returns:
            DocumentationResult: Result of documentation generation
        """
        try:
            self.logger.info("Starting comprehensive documentation generation")
            
            start_time = datetime.now()
            result = DocumentationResult(success=False)
            
            # Create output directory
            self.output_directory.mkdir(parents=True, exist_ok=True)
            result.output_directory = str(self.output_directory)
            
            # Initialize component instances for analysis
            components_initialized = self._initialize_component_instances()
            if not components_initialized:
                raise Exception("Failed to initialize component instances")
            
            # Generate analysis document
            analysis_doc = self._generate_analysis_document()
            if analysis_doc:
                result.documents_generated.append(analysis_doc)
            
            # Generate architecture documentation
            arch_doc = self._generate_architecture_documentation()
            if arch_doc:
                result.documents_generated.append(arch_doc)
            
            # Generate gap analysis report
            gap_report = self._generate_gap_analysis_report()
            if gap_report:
                result.documents_generated.append(gap_report)
            
            # Generate developer documentation
            dev_doc = self._generate_developer_documentation()
            if dev_doc:
                result.documents_generated.append(dev_doc)
            
            # Generate API documentation
            api_doc = self._generate_api_documentation()
            if api_doc:
                result.documents_generated.append(api_doc)
            
            # Generate architecture diagrams
            if self.enable_diagrams:
                diagrams = self._generate_architecture_diagrams()
                result.diagrams_generated.extend(diagrams)
            
            # Calculate statistics
            result.total_sections = sum(len(sections) for sections in self.document_sections.values())
            result.total_pages = len(result.documents_generated) * 10  # Estimate
            
            # Finalize result
            end_time = datetime.now()
            result.generation_time = (end_time - start_time).total_seconds()
            result.success = len(result.documents_generated) > 0
            
            self.logger.info(f"Documentation generation completed: {len(result.documents_generated)} documents, {len(result.diagrams_generated)} diagrams")
            
            # Audit documentation generation
            self.security_manager.audit_critical_operation(
                operation="comprehensive_documentation_generation",
                component="documentation_generator",
                details={
                    "documents_generated": len(result.documents_generated),
                    "diagrams_generated": len(result.diagrams_generated),
                    "generation_time": result.generation_time,
                    "output_directory": str(self.output_directory)
                },
                success=result.success,
                security_level=SecurityLevel.LOW
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive documentation: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e),
                generation_time=(datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0.0
            )
    
    def generate_analysis_document(self) -> DocumentationResult:
        """
        Generate detailed analysis document with current vs. proposed architecture mapping
        
        Returns:
            DocumentationResult: Analysis document generation result
        """
        try:
            self.logger.info("Generating analysis document")
            
            start_time = datetime.now()
            result = DocumentationResult(success=False)
            
            # Initialize components
            if not self.components:
                self._initialize_component_instances()
            
            # Generate analysis document
            analysis_doc = self._generate_analysis_document()
            
            if analysis_doc:
                result.documents_generated.append(analysis_doc)
                result.success = True
                result.output_directory = str(self.output_directory)
                result.total_sections = len(self.document_sections.get("analysis", []))
            
            result.generation_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating analysis document: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e)
            )
    
    def generate_gap_analysis_report(self) -> DocumentationResult:
        """
        Generate comprehensive gap analysis report with prioritized fixes
        
        Returns:
            DocumentationResult: Gap analysis report generation result
        """
        try:
            self.logger.info("Generating gap analysis report")
            
            start_time = datetime.now()
            result = DocumentationResult(success=False)
            
            # Initialize components
            if not self.components:
                self._initialize_component_instances()
            
            # Generate gap analysis report
            gap_report = self._generate_gap_analysis_report()
            
            if gap_report:
                result.documents_generated.append(gap_report)
                result.success = True
                result.output_directory = str(self.output_directory)
                result.total_sections = len(self.document_sections.get("gap_analysis", []))
            
            result.generation_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating gap analysis report: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e)
            )
    
    def generate_architecture_diagrams(self) -> DocumentationResult:
        """
        Generate updated architecture diagrams and documentation
        
        Returns:
            DocumentationResult: Architecture diagrams generation result
        """
        try:
            self.logger.info("Generating architecture diagrams")
            
            start_time = datetime.now()
            result = DocumentationResult(success=False)
            
            if self.enable_diagrams:
                # Generate architecture diagrams
                diagrams = self._generate_architecture_diagrams()
                result.diagrams_generated.extend(diagrams)
                
                # Generate architecture documentation
                arch_doc = self._generate_architecture_documentation()
                if arch_doc:
                    result.documents_generated.append(arch_doc)
                
                result.success = len(diagrams) > 0 or arch_doc is not None
                result.output_directory = str(self.output_directory)
            
            result.generation_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating architecture diagrams: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e)
            )
    
    def generate_developer_documentation(self) -> DocumentationResult:
        """
        Generate developer documentation for system architecture and APIs
        
        Returns:
            DocumentationResult: Developer documentation generation result
        """
        try:
            self.logger.info("Generating developer documentation")
            
            start_time = datetime.now()
            result = DocumentationResult(success=False)
            
            # Initialize components
            if not self.components:
                self._initialize_component_instances()
            
            # Generate developer documentation
            dev_doc = self._generate_developer_documentation()
            
            # Generate API documentation
            api_doc = self._generate_api_documentation()
            
            if dev_doc:
                result.documents_generated.append(dev_doc)
            if api_doc:
                result.documents_generated.append(api_doc)
            
            result.success = len(result.documents_generated) > 0
            result.output_directory = str(self.output_directory)
            result.total_sections = (len(self.document_sections.get("developer", [])) + 
                                   len(self.document_sections.get("api", [])))
            
            result.generation_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating developer documentation: {e}")
            return DocumentationResult(
                success=False,
                error_message=str(e)
            )
    
    def shutdown(self):
        """Shutdown the documentation generator"""
        self.logger.info("Shutting down Documentation Generator")
        
        # Cleanup component instances
        for component in self.components.values():
            if hasattr(component, 'shutdown'):
                component.shutdown()
        
        self.logger.info("Documentation Generator shutdown complete")
    
    # Private helper methods
    
    def _initialize_generator(self):
        """Initialize the documentation generator"""
        try:
            # Create output directory
            self.output_directory.mkdir(parents=True, exist_ok=True)
            
            # Create template directory if it doesn't exist
            self.template_directory.mkdir(parents=True, exist_ok=True)
            
            # Initialize template engine
            self._initialize_template_engine()
            
            # Setup logging
            self._setup_generator_logging()
            
            self.logger.info("Documentation generator initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing generator: {e}")
    
    def _initialize_template_engine(self):
        """Initialize Jinja2 template engine"""
        try:
            # Create template loader
            if self.template_directory.exists():
                loader = jinja2.FileSystemLoader(str(self.template_directory))
            else:
                # Use built-in templates
                loader = jinja2.DictLoader(self._get_builtin_templates())
            
            # Initialize environment
            self.template_env = jinja2.Environment(
                loader=loader,
                autoescape=jinja2.select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Add custom filters
            self.template_env.filters['markdown'] = self._markdown_filter
            self.template_env.filters['code_highlight'] = self._code_highlight_filter
            
        except Exception as e:
            self.logger.error(f"Error initializing template engine: {e}")
            self.template_env = None
    
    def _initialize_component_instances(self) -> bool:
        """Initialize component instances for analysis"""
        try:
            # Initialize all major components
            self.components = {
                'architecture_analysis': ArchitectureAnalysisEngine(self.security_manager),
                'unified_detection': UnifiedDetectionEngine(self.security_manager),
                'dependency_validation': DependencyValidationSystem(self.security_manager),
                'download_manager': RobustDownloadManager(self.security_manager),
                'installation_manager': AdvancedInstallationManager(self.security_manager),
                'steamdeck_integration': SteamDeckIntegrationLayer(self.security_manager),
                'storage_manager': IntelligentStorageManager(self.security_manager),
                'plugin_manager': PluginSystemManager(self.security_manager),
                'frontend_manager': ModernFrontendManager(self.security_manager)
            }
            
            self.logger.info(f"Initialized {len(self.components)} component instances")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing component instances: {e}")
            return False
    
    def _generate_analysis_document(self) -> Optional[str]:
        """Generate detailed analysis document"""
        try:
            self.logger.info("Generating analysis document")
            
            # Create document sections
            sections = []
            
            # Executive Summary
            sections.append(DocumentSection(
                section_id="executive_summary",
                title="Executive Summary",
                content=self._generate_executive_summary()
            ))
            
            # Current Architecture Analysis
            sections.append(DocumentSection(
                section_id="current_architecture",
                title="Current Architecture Analysis",
                content=self._analyze_current_architecture()
            ))
            
            # Proposed Architecture
            sections.append(DocumentSection(
                section_id="proposed_architecture",
                title="Proposed Architecture",
                content=self._describe_proposed_architecture()
            ))
            
            # Architecture Comparison
            sections.append(DocumentSection(
                section_id="architecture_comparison",
                title="Current vs. Proposed Architecture Mapping",
                content=self._generate_architecture_comparison()
            ))
            
            # Implementation Analysis
            sections.append(DocumentSection(
                section_id="implementation_analysis",
                title="Implementation Analysis",
                content=self._analyze_implementation_details()
            ))
            
            # Store sections
            self.document_sections["analysis"] = sections
            
            # Generate document
            document_path = self._render_document(
                "analysis_document",
                "Analysis Document",
                sections,
                DocumentFormat.MARKDOWN
            )
            
            return document_path
            
        except Exception as e:
            self.logger.error(f"Error generating analysis document: {e}")
            return None
    
    def _generate_gap_analysis_report(self) -> Optional[str]:
        """Generate comprehensive gap analysis report"""
        try:
            self.logger.info("Generating gap analysis report")
            
            # Identify gaps
            self._identify_system_gaps()
            
            # Create document sections
            sections = []
            
            # Gap Analysis Overview
            sections.append(DocumentSection(
                section_id="gap_overview",
                title="Gap Analysis Overview",
                content=self._generate_gap_overview()
            ))
            
            # Critical Gaps
            sections.append(DocumentSection(
                section_id="critical_gaps",
                title="Critical Priority Gaps",
                content=self._generate_critical_gaps_section()
            ))
            
            # High Priority Gaps
            sections.append(DocumentSection(
                section_id="high_priority_gaps",
                title="High Priority Gaps",
                content=self._generate_high_priority_gaps_section()
            ))
            
            # Medium Priority Gaps
            sections.append(DocumentSection(
                section_id="medium_priority_gaps",
                title="Medium Priority Gaps",
                content=self._generate_medium_priority_gaps_section()
            ))
            
            # Implementation Roadmap
            sections.append(DocumentSection(
                section_id="implementation_roadmap",
                title="Implementation Roadmap",
                content=self._generate_implementation_roadmap()
            ))
            
            # Store sections
            self.document_sections["gap_analysis"] = sections
            
            # Generate document
            document_path = self._render_document(
                "gap_analysis_report",
                "Gap Analysis Report",
                sections,
                DocumentFormat.MARKDOWN
            )
            
            return document_path
            
        except Exception as e:
            self.logger.error(f"Error generating gap analysis report: {e}")
            return None
    
    def _generate_architecture_documentation(self) -> Optional[str]:
        """Generate architecture documentation"""
        try:
            self.logger.info("Generating architecture documentation")
            
            # Create document sections
            sections = []
            
            # Architecture Overview
            sections.append(DocumentSection(
                section_id="architecture_overview",
                title="Architecture Overview",
                content=self._generate_architecture_overview()
            ))
            
            # System Components
            sections.append(DocumentSection(
                section_id="system_components",
                title="System Components",
                content=self._document_system_components()
            ))
            
            # Component Interactions
            sections.append(DocumentSection(
                section_id="component_interactions",
                title="Component Interactions",
                content=self._document_component_interactions()
            ))
            
            # Data Flow
            sections.append(DocumentSection(
                section_id="data_flow",
                title="Data Flow Architecture",
                content=self._document_data_flow()
            ))
            
            # Security Architecture
            sections.append(DocumentSection(
                section_id="security_architecture",
                title="Security Architecture",
                content=self._document_security_architecture()
            ))
            
            # Store sections
            self.document_sections["architecture"] = sections
            
            # Generate document
            document_path = self._render_document(
                "architecture_documentation",
                "Architecture Documentation",
                sections,
                DocumentFormat.MARKDOWN
            )
            
            return document_path
            
        except Exception as e:
            self.logger.error(f"Error generating architecture documentation: {e}")
            return None
    
    def _generate_developer_documentation(self) -> Optional[str]:
        """Generate developer documentation"""
        try:
            self.logger.info("Generating developer documentation")
            
            # Create document sections
            sections = []
            
            # Developer Guide Overview
            sections.append(DocumentSection(
                section_id="developer_overview",
                title="Developer Guide Overview",
                content=self._generate_developer_overview()
            ))
            
            # System Architecture for Developers
            sections.append(DocumentSection(
                section_id="developer_architecture",
                title="System Architecture for Developers",
                content=self._generate_developer_architecture_guide()
            ))
            
            # Component Development Guide
            sections.append(DocumentSection(
                section_id="component_development",
                title="Component Development Guide",
                content=self._generate_component_development_guide()
            ))
            
            # API Integration Guide
            sections.append(DocumentSection(
                section_id="api_integration",
                title="API Integration Guide",
                content=self._generate_api_integration_guide()
            ))
            
            # Testing and Debugging
            sections.append(DocumentSection(
                section_id="testing_debugging",
                title="Testing and Debugging",
                content=self._generate_testing_debugging_guide()
            ))
            
            # Store sections
            self.document_sections["developer"] = sections
            
            # Generate document
            document_path = self._render_document(
                "developer_documentation",
                "Developer Documentation",
                sections,
                DocumentFormat.MARKDOWN
            )
            
            return document_path
            
        except Exception as e:
            self.logger.error(f"Error generating developer documentation: {e}")
            return None
    
    def _generate_api_documentation(self) -> Optional[str]:
        """Generate API documentation"""
        try:
            self.logger.info("Generating API documentation")
            
            # Create document sections
            sections = []
            
            # API Overview
            sections.append(DocumentSection(
                section_id="api_overview",
                title="API Overview",
                content=self._generate_api_overview()
            ))
            
            # Component APIs
            for component_name, component in self.components.items():
                sections.append(DocumentSection(
                    section_id=f"api_{component_name}",
                    title=f"{component_name.replace('_', ' ').title()} API",
                    content=self._document_component_api(component_name, component)
                ))
            
            # Store sections
            self.document_sections["api"] = sections
            
            # Generate document
            document_path = self._render_document(
                "api_documentation",
                "API Documentation",
                sections,
                DocumentFormat.MARKDOWN
            )
            
            return document_path
            
        except Exception as e:
            self.logger.error(f"Error generating API documentation: {e}")
            return None  
  
    def _generate_architecture_diagrams(self) -> List[str]:
        """Generate architecture diagrams"""
        try:
            self.logger.info("Generating architecture diagrams")
            
            diagrams_generated = []
            
            # System Overview Diagram
            system_diagram = self._create_system_overview_diagram()
            if system_diagram:
                diagram_path = self._render_diagram(system_diagram)
                if diagram_path:
                    diagrams_generated.append(diagram_path)
            
            # Component Architecture Diagram
            component_diagram = self._create_component_architecture_diagram()
            if component_diagram:
                diagram_path = self._render_diagram(component_diagram)
                if diagram_path:
                    diagrams_generated.append(diagram_path)
            
            # Data Flow Diagram
            dataflow_diagram = self._create_data_flow_diagram()
            if dataflow_diagram:
                diagram_path = self._render_diagram(dataflow_diagram)
                if diagram_path:
                    diagrams_generated.append(diagram_path)
            
            # Deployment Architecture Diagram
            deployment_diagram = self._create_deployment_architecture_diagram()
            if deployment_diagram:
                diagram_path = self._render_diagram(deployment_diagram)
                if diagram_path:
                    diagrams_generated.append(diagram_path)
            
            return diagrams_generated
            
        except Exception as e:
            self.logger.error(f"Error generating architecture diagrams: {e}")
            return [