# -*- coding: utf-8 -*-
"""
Plugin Conflict Detection and Management System

This module implements automatic plugin conflict detection algorithms,
version management system for plugin updates, and plugin dependency resolution system.

Requirements addressed:
- 7.2: Automatic plugin conflict detection and version management
- 7.3: Plugin dependency resolution system
"""

import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque

try:
    from .plugin_base import PluginMetadata, PluginConflict, ValidationResult
    from .version_manager import version_manager
    from .security_manager import SecurityManager, SecurityLevel
except ImportError:
    from plugin_base import PluginMetadata, PluginConflict, ValidationResult
    from version_manager import version_manager
    from security_manager import SecurityManager, SecurityLevel


class ConflictType(Enum):
    """Types of plugin conflicts"""
    VERSION_CONFLICT = "version_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    API_CONFLICT = "api_conflict"
    RUNTIME_OVERLAP = "runtime_overlap"
    PERMISSION_CONFLICT = "permission_conflict"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_DEPENDENCY = "missing_dependency"
    INCOMPATIBLE_API = "incompatible_api"


class ConflictSeverity(Enum):
    """Severity levels for conflicts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(Enum):
    """Strategies for conflict resolution"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PRIORITY_BASED = "priority_based"
    USER_CHOICE = "user_choice"
    DISABLE_CONFLICTING = "disable_conflicting"
    UPDATE_DEPENDENCIES = "update_dependencies"
    DOWNGRADE_VERSION = "downgrade_version"
    ALTERNATIVE_PLUGIN = "alternative_plugin"


@dataclass
class ConflictDetails:
    """Detailed information about a plugin conflict"""
    id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_plugins: List[str]
    affected_versions: Dict[str, str]
    resolution_strategies: List[ResolutionStrategy]
    auto_resolvable: bool = False
    resolution_options: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_details: Optional[str] = None
    impact_assessment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionUpdate:
    """Information about plugin version updates"""
    plugin_name: str
    current_version: str
    available_version: str
    update_type: str  # "major", "minor", "patch"
    changelog: Optional[str] = None
    breaking_changes: bool = False
    security_fixes: bool = False
    dependencies_updated: List[str] = field(default_factory=list)
    update_url: Optional[str] = None
    requires_restart: bool = False
    compatibility_notes: Optional[str] = None


@dataclass
class DependencyNode:
    """Node in dependency graph"""
    plugin_name: str
    version: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    optional_dependencies: Set[str] = field(default_factory=set)
    conflicts_with: Set[str] = field(default_factory=set)


class PluginConflictManager:
    """
    Comprehensive Plugin Conflict Detection and Management System
    
    Provides:
    - Automatic plugin conflict detection algorithms
    - Version management system for plugin updates
    - Plugin dependency resolution system
    - Conflict resolution strategies
    - Impact assessment and reporting
    """
    
    def __init__(self, security_manager: Optional[SecurityManager] = None):
        """
        Initialize Plugin Conflict Manager
        
        Args:
            security_manager: Security manager instance for auditing
        """
        self.logger = logging.getLogger(__name__)
        self.security_manager = security_manager or SecurityManager()
        
        # Conflict storage and tracking
        self.detected_conflicts: Dict[str, ConflictDetails] = {}
        self.resolved_conflicts: Dict[str, ConflictDetails] = {}
        self.conflict_history: List[ConflictDetails] = []
        
        # Dependency management
        self.dependency_graph: Dict[str, DependencyNode] = {}
        self.version_constraints: Dict[str, Dict[str, str]] = {}
        self.plugin_priorities: Dict[str, int] = {}
        
        # Version management
        self.available_updates: Dict[str, VersionUpdate] = {}
        self.update_sources: List[str] = []
        self.auto_update_enabled: bool = False
        
        # Configuration
        self.conflict_detection_enabled = True
        self.auto_resolution_enabled = True
        self.max_resolution_attempts = 3
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load configuration
        self._load_conflict_manager_config()
        
        self.logger.info("Plugin Conflict Manager initialized")
    
    def detect_all_conflicts(self, plugins: List[PluginMetadata]) -> List[ConflictDetails]:
        """
        Detect all types of conflicts between plugins
        
        Args:
            plugins: List of plugin metadata to analyze
            
        Returns:
            List[ConflictDetails]: All detected conflicts
        """
        if not self.conflict_detection_enabled:
            return []
        
        conflicts = []
        
        try:
            with self._lock:
                # Build dependency graph
                self._build_dependency_graph(plugins)
                
                # Detect different types of conflicts
                version_conflicts = self._detect_version_conflicts(plugins)
                conflicts.extend(version_conflicts)
                
                dependency_conflicts = self._detect_dependency_conflicts(plugins)
                conflicts.extend(dependency_conflicts)
                
                circular_dependencies = self._detect_circular_dependencies()
                conflicts.extend(circular_dependencies)
                
                missing_dependencies = self._detect_missing_dependencies(plugins)
                conflicts.extend(missing_dependencies)
                
                resource_conflicts = self._detect_resource_conflicts(plugins)
                conflicts.extend(resource_conflicts)
                
                api_conflicts = self._detect_api_conflicts(plugins)
                conflicts.extend(api_conflicts)
                
                permission_conflicts = self._detect_permission_conflicts(plugins)
                conflicts.extend(permission_conflicts)
                
                # Store detected conflicts
                for conflict in conflicts:
                    self.detected_conflicts[conflict.id] = conflict
                    self.conflict_history.append(conflict)
                
                # Assess impact of conflicts
                self._assess_conflict_impact(conflicts)
                
                self.logger.info(f"Detected {len(conflicts)} plugin conflicts")
                
                # Audit conflict detection
                self.security_manager.audit_critical_operation(
                    operation="plugin_conflict_detection",
                    component="plugin_conflict_manager",
                    details={
                        "total_plugins": len(plugins),
                        "conflicts_detected": len(conflicts),
                        "conflict_types": list(set(c.conflict_type.value for c in conflicts))
                    },
                    success=True,
                    security_level=SecurityLevel.MEDIUM
                )
                
                return conflicts
                
        except Exception as e:
            self.logger.error(f"Error detecting plugin conflicts: {e}")
            return []
    
    def resolve_conflict(self, conflict_id: str, strategy: ResolutionStrategy, 
                        user_input: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resolve a specific plugin conflict
        
        Args:
            conflict_id: ID of conflict to resolve
            strategy: Resolution strategy to use
            user_input: Additional user input for resolution
            
        Returns:
            bool: True if conflict was successfully resolved
        """
        try:
            with self._lock:
                conflict = self.detected_conflicts.get(conflict_id)
                if not conflict:
                    self.logger.warning(f"Conflict {conflict_id} not found")
                    return False
                
                if conflict.resolved:
                    self.logger.info(f"Conflict {conflict_id} already resolved")
                    return True
                
                # Attempt resolution based on strategy
                success = False
                resolution_details = ""
                
                if strategy == ResolutionStrategy.AUTOMATIC:
                    success, resolution_details = self._resolve_automatically(conflict)
                elif strategy == ResolutionStrategy.PRIORITY_BASED:
                    success, resolution_details = self._resolve_by_priority(conflict)
                elif strategy == ResolutionStrategy.USER_CHOICE:
                    success, resolution_details = self._resolve_by_user_choice(conflict, user_input)
                elif strategy == ResolutionStrategy.DISABLE_CONFLICTING:
                    success, resolution_details = self._resolve_by_disabling(conflict)
                elif strategy == ResolutionStrategy.UPDATE_DEPENDENCIES:
                    success, resolution_details = self._resolve_by_updating(conflict)
                elif strategy == ResolutionStrategy.DOWNGRADE_VERSION:
                    success, resolution_details = self._resolve_by_downgrading(conflict)
                elif strategy == ResolutionStrategy.ALTERNATIVE_PLUGIN:
                    success, resolution_details = self._resolve_with_alternative(conflict, user_input)
                else:
                    self.logger.warning(f"Manual resolution required for conflict {conflict_id}")
                    return False
                
                if success:
                    conflict.resolved = True
                    conflict.resolution_details = resolution_details
                    self.resolved_conflicts[conflict_id] = conflict
                    
                    self.logger.info(f"Successfully resolved conflict {conflict_id}: {resolution_details}")
                    
                    # Audit successful resolution
                    self.security_manager.audit_critical_operation(
                        operation="plugin_conflict_resolution",
                        component="plugin_conflict_manager",
                        details={
                            "conflict_id": conflict_id,
                            "conflict_type": conflict.conflict_type.value,
                            "strategy": strategy.value,
                            "resolution_details": resolution_details
                        },
                        success=True,
                        security_level=SecurityLevel.MEDIUM
                    )
                else:
                    self.logger.error(f"Failed to resolve conflict {conflict_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error resolving conflict {conflict_id}: {e}")
            return False
    
    def check_for_updates(self, plugins: List[PluginMetadata]) -> List[VersionUpdate]:
        """
        Check for available plugin updates
        
        Args:
            plugins: List of plugins to check for updates
            
        Returns:
            List[VersionUpdate]: Available updates
        """
        updates = []
        
        try:
            for plugin in plugins:
                update = self._check_plugin_update(plugin)
                if update:
                    updates.append(update)
                    self.available_updates[plugin.name] = update
            
            self.logger.info(f"Found {len(updates)} available plugin updates")
            return updates
            
        except Exception as e:
            self.logger.error(f"Error checking for plugin updates: {e}")
            return []
    
    def resolve_dependencies(self, plugin_name: str, plugins: List[PluginMetadata]) -> List[str]:
        """
        Resolve plugin dependencies in correct installation order
        
        Args:
            plugin_name: Name of plugin to resolve dependencies for
            plugins: List of available plugins
            
        Returns:
            List[str]: Plugin names in dependency order
        """
        try:
            with self._lock:
                # Build dependency graph
                self._build_dependency_graph(plugins)
                
                # Use topological sort to resolve dependencies
                resolved_order = self._topological_sort(plugin_name)
                
                self.logger.info(f"Resolved dependencies for {plugin_name}: {resolved_order}")
                return resolved_order
                
        except Exception as e:
            self.logger.error(f"Error resolving dependencies for {plugin_name}: {e}")
            return [plugin_name]  # Return at least the plugin itself
    
    def get_conflict_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive conflict report
        
        Returns:
            Dict[str, Any]: Detailed conflict report
        """
        try:
            total_conflicts = len(self.detected_conflicts)
            resolved_conflicts = len(self.resolved_conflicts)
            active_conflicts = total_conflicts - resolved_conflicts
            
            # Group conflicts by type and severity
            conflicts_by_type = defaultdict(int)
            conflicts_by_severity = defaultdict(int)
            
            for conflict in self.detected_conflicts.values():
                conflicts_by_type[conflict.conflict_type.value] += 1
                conflicts_by_severity[conflict.severity.value] += 1
            
            # Recent conflict trends
            recent_conflicts = [
                c for c in self.conflict_history 
                if (datetime.now() - c.detected_at).days <= 7
            ]
            
            return {
                "summary": {
                    "total_conflicts": total_conflicts,
                    "active_conflicts": active_conflicts,
                    "resolved_conflicts": resolved_conflicts,
                    "recent_conflicts": len(recent_conflicts),
                    "auto_resolution_enabled": self.auto_resolution_enabled
                },
                "conflicts_by_type": dict(conflicts_by_type),
                "conflicts_by_severity": dict(conflicts_by_severity),
                "active_conflicts": {
                    conflict_id: {
                        "type": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "description": conflict.description,
                        "affected_plugins": conflict.affected_plugins,
                        "auto_resolvable": conflict.auto_resolvable,
                        "detected_at": conflict.detected_at.isoformat()
                    }
                    for conflict_id, conflict in self.detected_conflicts.items()
                    if not conflict.resolved
                },
                "available_updates": {
                    plugin_name: {
                        "current_version": update.current_version,
                        "available_version": update.available_version,
                        "update_type": update.update_type,
                        "breaking_changes": update.breaking_changes,
                        "security_fixes": update.security_fixes
                    }
                    for plugin_name, update in self.available_updates.items()
                },
                "dependency_graph_stats": {
                    "total_nodes": len(self.dependency_graph),
                    "total_dependencies": sum(len(node.dependencies) for node in self.dependency_graph.values()),
                    "circular_dependencies": len(self._find_circular_dependencies())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating conflict report: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _build_dependency_graph(self, plugins: List[PluginMetadata]):
        """Build dependency graph from plugin metadata"""
        self.dependency_graph.clear()
        
        # Create nodes for all plugins
        for plugin in plugins:
            node = DependencyNode(
                plugin_name=plugin.name,
                version=plugin.version,
                dependencies=set(plugin.dependencies)
            )
            self.dependency_graph[plugin.name] = node
        
        # Build dependency relationships
        for plugin in plugins:
            node = self.dependency_graph[plugin.name]
            for dep in plugin.dependencies:
                dep_name = self._extract_dependency_name(dep)
                if dep_name in self.dependency_graph:
                    self.dependency_graph[dep_name].dependents.add(plugin.name)
    
    def _detect_version_conflicts(self, plugins: List[PluginMetadata]) -> List[ConflictDetails]:
        """Detect version conflicts between plugins"""
        conflicts = []
        
        # Check for plugins requiring different versions of same dependency
        dependency_requirements = defaultdict(list)
        
        for plugin in plugins:
            for dep in plugin.dependencies:
                dep_name, version_constraint = self._parse_dependency(dep)
                dependency_requirements[dep_name].append((plugin.name, version_constraint))
        
        for dep_name, requirements in dependency_requirements.items():
            if len(requirements) > 1:
                # Check if version constraints are compatible
                compatible = self._check_version_compatibility(requirements)
                if not compatible:
                    conflict = ConflictDetails(
                        id=f"version_conflict_{dep_name}_{datetime.now().timestamp()}",
                        conflict_type=ConflictType.VERSION_CONFLICT,
                        severity=ConflictSeverity.HIGH,
                        description=f"Incompatible version requirements for {dep_name}",
                        affected_plugins=[req[0] for req in requirements],
                        affected_versions={req[0]: req[1] for req in requirements},
                        resolution_strategies=[
                            ResolutionStrategy.UPDATE_DEPENDENCIES,
                            ResolutionStrategy.DOWNGRADE_VERSION,
                            ResolutionStrategy.ALTERNATIVE_PLUGIN
                        ],
                        auto_resolvable=True
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_dependency_conflicts(self, plugins: List[PluginMetadata]) -> List[ConflictDetails]:
        """Detect dependency conflicts"""
        conflicts = []
        
        # Check for conflicting dependencies
        for plugin in plugins:
            for other_plugin in plugins:
                if plugin.name != other_plugin.name:
                    # Check if plugins have conflicting requirements
                    plugin_deps = set(self._extract_dependency_name(dep) for dep in plugin.dependencies)
                    other_deps = set(self._extract_dependency_name(dep) for dep in other_plugin.dependencies)
                    
                    # Check for explicit conflicts (if metadata supports it)
                    if hasattr(plugin, 'conflicts_with') and other_plugin.name in plugin.conflicts_with:
                        conflict = ConflictDetails(
                            id=f"dependency_conflict_{plugin.name}_{other_plugin.name}",
                            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                            severity=ConflictSeverity.MEDIUM,
                            description=f"Plugin {plugin.name} conflicts with {other_plugin.name}",
                            affected_plugins=[plugin.name, other_plugin.name],
                            affected_versions={plugin.name: plugin.version, other_plugin.name: other_plugin.version},
                            resolution_strategies=[
                                ResolutionStrategy.DISABLE_CONFLICTING,
                                ResolutionStrategy.ALTERNATIVE_PLUGIN
                            ],
                            auto_resolvable=False
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_circular_dependencies(self) -> List[ConflictDetails]:
        """Detect circular dependencies in plugin graph"""
        conflicts = []
        circular_deps = self._find_circular_dependencies()
        
        for cycle in circular_deps:
            conflict = ConflictDetails(
                id=f"circular_dependency_{'_'.join(cycle)}",
                conflict_type=ConflictType.CIRCULAR_DEPENDENCY,
                severity=ConflictSeverity.CRITICAL,
                description=f"Circular dependency detected: {' -> '.join(cycle + [cycle[0]])}",
                affected_plugins=cycle,
                affected_versions={},
                resolution_strategies=[
                    ResolutionStrategy.MANUAL,
                    ResolutionStrategy.DISABLE_CONFLICTING
                ],
                auto_resolvable=False
            )
            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_missing_dependencies(self, plugins: List[PluginMetadata]) -> List[ConflictDetails]:
        """Detect missing dependencies"""
        conflicts = []
        available_plugins = {plugin.name for plugin in plugins}
        
        for plugin in plugins:
            for dep in plugin.dependencies:
                dep_name = self._extract_dependency_name(dep)
                if dep_name not in available_plugins:
                    conflict = ConflictDetails(
                        id=f"missing_dependency_{plugin.name}_{dep_name}",
                        conflict_type=ConflictType.MISSING_DEPENDENCY,
                        severity=ConflictSeverity.HIGH,
                        description=f"Plugin {plugin.name} requires missing dependency: {dep_name}",
                        affected_plugins=[plugin.name],
                    onflicts    return c  
          ct)
flind(conflicts.appe   con             )
                       lse
 ble=Falva_reso     auto                       ],
                 
   LICTINGCONFISABLE_Strategy.Desolution     R                AL,
       tegy.MANUionStra    Resolut                    [
    trategies=esolution_s       r              
   rsion},gin.vename: pluons={plugin.versid_ affecte                 
      lugin.name],ugins=[pcted_pl        affe        
        ription}",e}: {descamlugin.nugin {pon=f"Plripti  desc                  .HIGH,
    rityevectS=Confli  severity                      ,
CTION_CONFLIype.PERMISSnflictT_type=Colictnf      co                  ",
estamp()}.timime.now()name}_{datet_{plugin.n_conflict"permissio       id=f                etails(
  = ConflictDonflict       c            ):
 ombongerous_crm in dans for pein_permissioin plugrm  all(pe    if          ns:
  combinatio dangerous_n incriptio, desrous_combofor dange                
      sions]
  .permisginr p in pluse str(p) fo 'value') elsattr(p,hap.value if ons = [_permissiugin    pl     lugins:
    plugin in p for  
         
        ]ion')
    natombiork cnetwege and  privilh-risk], 'Higss'twork_acce', 'neerationsrivileged_op   (['p   ),
      n risk'io exfiltratntial dataoteess'], 'Paccnetwork_stem', 'filesy  (['write_    
      rk access'),etwoand nm n of systes combinatio'Dangerouk_access'], s', 'networtem_command(['sys          [
  ions = s_combinat    dangerou    ents
equiremon rrmissing peconflicti for  Check #      
     
    licts = []        confns"""
gieen plubetwcts  conflisiont permisec"Det"    "   ils]:
 ConflictDeta-> List[) nMetadata]ist[Plugis: Lelf, pluginconflicts(ssion_t_permisec def _det  
    
 flictsrn con retu   
       t)
     iconfl.append(c   conflicts           
          )               True
 esolvable=      auto_r              ],
                 
           TINGE_CONFLICegy.DISABLionStratut  Resol                      CIES,
    TE_DEPENDENPDAStrategy.Ution      Resolu                   egies=[
   strattion_solu     re              {},
     d_versions=te  affec            
          in_names,s=plugected_plugin  aff               ",
       ugin_names)}, '.join(pl}: {'api_version version {APIe  incompatiblsingins uPlugcription=f"         des            GH,
   ty.HItSeverinflicseverity=Co             
           BLE_API,pe.INCOMPATI=ConflictTyct_type      confli               ",
   n}rsioi_veict_{ap_confl=f"api       id                
 etails(flictDict = Con      confl            on):
  rsion(api_veersile_api_vis_compatiblf._if not se             s():
   s.itemoni_versiames in applugin_nion, _vers api        for
     1:ions) >pi_versif len(a  
      ibilityheck compatons, cnt API versiwith differeave plugins we hf  # I              
me)
 (plugin.nappendrsion].agin.api_vepluersions[    api_v        plugins:
ugin in   for pl    
      
    ict(list)s = defaultdrsion  api_ve
      itiesatibilomp inc API version forckChe #   
             s = []
ctli       conf
 "ns""een plugiflicts betwt API con""Detec     "ils]:
   lictDetaist[Conf -> Ldata])etast[PluginMins: Lif, pluglicts(select_api_confet   def _d
    
 onflicts   return c  
   )
        (conflictendcts.app      confli
                )
          =Falseesolvableo_r    aut                      ],
             SED
 ITY_BAIOR.PRegyratesolutionSt        R             ANUAL,
   onStrategy.Mluti        Reso               
 rategies=[ution_st  resol                  ns={},
ected_versioaff                   s,
 gins=userlu affected_p                   
ers)}",', '.join(usesource}: {ver {r conflict oplugins mayultiple on=f"Mripti      desc            MEDIUM,
  tSeverity.onfliceverity=C   s               
  ONFLICT,RCE_Ce.RESOUlictTypct_type=Conffli con              
     stamp()}",meme.now().ti}_{datetiresource_{ictonflource_cf"res        id=           
 Details(flictnflict = Con    co            
) > 1: len(users     if
       ge.items():source_usas in resource, userfor re 
             ame)
  .nlugin'].append(pfile_systemrce_usage['resou              ():
  owern.lcription plugin.desnfig' ir() or 'coption.loweugin.descri' in pl if 'file
           lugin.name)].append(prts'work_ponetge['sae_u    resourc         ):
   lower(scription. plugin.deort' in 'p  if
          ptionsdescries/namgin erns in plue pattresourcr common  Check fo #           gins:
n in plu for plugi            
t(list)
   ultdicfa de =urce_usagereso        d analysis
tecaore sophisti medould neactice, won - in prmentatiified impleimpla s This is 
        # resourcessame use t mightins tha for plugheck# C  
        = []
      licts         conf"
plugins""ts between  conflicurceeso"Detect r      ""
  Details]:ctli-> List[ConfMetadata]) Pluginins: List[lugicts(self, pce_conflesourf _detect_r   
    des
 n conflict   retur        
lict)
     (confts.appendnflic    co                       )
             =False
_resolvable      auto            
         ],             
        INGLICTONFISABLE_Ctrategy.D ResolutionS                   N,
        _PLUGIVENATIategy.ALTERStrResolution                        
    gies=[teon_strasoluti re             
          },versiongin.in.name: plulugersions={pected_vff    a