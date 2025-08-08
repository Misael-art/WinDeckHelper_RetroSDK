#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core package for Environment Dev

This package contains the core functionality for the Environment Dev application,
including detection engines, installers, and suggestion systems.
"""

__version__ = "1.0.0"
__author__ = "Environment Dev Team"

# Import main classes for easier access
from .detection_engine import DetectionEngine, DetectedApplication
from .installer import Installer
from .suggestion_service import SuggestionService, create_suggestion_service
from .component_matcher import ComponentMatcher, ComponentMatch
from .component_metadata_manager import ComponentMetadataManager
from .intelligent_suggestions import IntelligentSuggestionEngine, EnhancedSuggestion

__all__ = [
    'DetectionEngine',
    'DetectedApplication', 
    'Installer',
    'SuggestionService',
    'create_suggestion_service',
    'ComponentMatcher',
    'ComponentMatch',
    'ComponentMetadataManager',
    'IntelligentSuggestionEngine',
    'EnhancedSuggestion'
]