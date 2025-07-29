#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para resolução e detecção de dependências circulares.

Este módulo contém funções para detectar dependências circulares e resolver
a ordem correta de instalação de componentes.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class CircularDependencyError(Exception):
    """Exceção levantada quando uma dependência circular é detectada."""
    
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Dependência circular detectada: {cycle_str}")

class DependencyResolver:
    """
    Classe para resolver dependências e detectar ciclos.
    """
    
    def __init__(self, components: Dict[str, Dict]):
        """
        Inicializa o resolvedor de dependências.
        
        Args:
            components: Dicionário de componentes com suas configurações
        """
        self.components = components
        self.dependency_graph = self._build_dependency_graph()
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Constrói o grafo de dependências a partir dos componentes.
        
        Returns:
            Dicionário onde cada chave é um componente e o valor é uma lista
            de suas dependências diretas
        """
        graph = {}
        
        for component_name, component_data in self.components.items():
            dependencies = component_data.get('dependencies', [])
            
            # Filtrar dependências que existem nos componentes
            valid_dependencies = []
            for dep in dependencies:
                if dep in self.components:
                    valid_dependencies.append(dep)
                else:
                    logger.warning(f"Componente '{component_name}' depende de '{dep}' que não existe")
            
            graph[component_name] = valid_dependencies
        
        return graph
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detecta todas as dependências circulares no grafo usando algoritmo melhorado.
        
        Returns:
            Lista de ciclos encontrados, onde cada ciclo é uma lista de componentes
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            """
            Busca em profundidade para detectar ciclos.
            
            Args:
                node: Nó atual sendo visitado
                
            Returns:
                True se um ciclo foi encontrado, False caso contrário
            """
            if node in rec_stack:
                # Encontrou um ciclo - extrair o ciclo do path
                try:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    
                    # Evitar ciclos duplicados
                    normalized_cycle = self._normalize_cycle(cycle)
                    if normalized_cycle not in [self._normalize_cycle(c) for c in cycles]:
                        cycles.append(cycle)
                        logger.warning(f"Dependência circular detectada: {' -> '.join(cycle)}")
                    
                    return True
                except ValueError:
                    # Node não encontrado no path (não deveria acontecer)
                    logger.error(f"Erro interno: nó '{node}' não encontrado no path durante detecção de ciclo")
                    return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visitar todas as dependências
            for dependency in self.dependency_graph.get(node, []):
                if dependency in self.components:  # Verificar se dependência existe
                    if dfs(dependency):
                        # Continuar procurando outros ciclos ao invés de parar no primeiro
                        pass
                else:
                    logger.warning(f"Dependência '{dependency}' de '{node}' não existe nos componentes")
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        # Verificar todos os componentes
        for component in self.components:
            if component not in visited:
                dfs(component)
        
        return cycles
    
    def _normalize_cycle(self, cycle: List[str]) -> Tuple[str, ...]:
        """
        Normaliza um ciclo para comparação (remove duplicatas rotacionais).
        
        Args:
            cycle: Lista representando um ciclo
            
        Returns:
            Tupla normalizada do ciclo
        """
        if not cycle:
            return tuple()
        
        # Remover o último elemento se for igual ao primeiro (fechamento do ciclo)
        if len(cycle) > 1 and cycle[0] == cycle[-1]:
            cycle = cycle[:-1]
        
        # Encontrar o menor elemento e rotacionar o ciclo para começar com ele
        if cycle:
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            return tuple(normalized)
        
        return tuple()
    
    def has_circular_dependencies(self) -> bool:
        """
        Verifica se existem dependências circulares.
        
        Returns:
            True se existem dependências circulares, False caso contrário
        """
        return len(self.detect_circular_dependencies()) > 0
    
    def topological_sort(self) -> List[str]:
        """
        Realiza ordenação topológica dos componentes.
        
        Returns:
            Lista de componentes em ordem topológica (dependências primeiro)
            
        Raises:
            CircularDependencyError: Se dependências circulares forem encontradas
        """
        # Primeiro verificar se há dependências circulares
        cycles = self.detect_circular_dependencies()
        if cycles:
            raise CircularDependencyError(cycles[0])
        
        # Algoritmo de Kahn para ordenação topológica
        in_degree = defaultdict(int)
        
        # Calcular grau de entrada para cada nó
        for node in self.components:
            in_degree[node] = 0
        
        for node, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                in_degree[node] += 1
        
        # Fila com nós que não têm dependências
        queue = deque([node for node in self.components if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Para cada componente que depende do atual
            for node, dependencies in self.dependency_graph.items():
                if current in dependencies:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)
        
        # Verificar se todos os nós foram processados
        if len(result) != len(self.components):
            # Isso não deveria acontecer se a verificação de ciclos funcionou
            remaining = set(self.components.keys()) - set(result)
            logger.error(f"Ordenação topológica incompleta. Nós restantes: {remaining}")
            raise CircularDependencyError(list(remaining))
        
        return result
    
    def get_installation_order(self, components_to_install: List[str]) -> List[str]:
        """
        Obtém a ordem de instalação para um conjunto específico de componentes.
        
        Args:
            components_to_install: Lista de componentes a serem instalados
            
        Returns:
            Lista de componentes em ordem de instalação (dependências primeiro)
            
        Raises:
            CircularDependencyError: Se dependências circulares forem encontradas
        """
        # Obter todas as dependências necessárias
        all_needed = set()
        
        def collect_dependencies(component: str):
            """Coleta recursivamente todas as dependências de um componente."""
            if component in all_needed:
                return
            
            if component not in self.components:
                logger.warning(f"Componente '{component}' não encontrado")
                return
            
            all_needed.add(component)
            
            for dep in self.dependency_graph.get(component, []):
                collect_dependencies(dep)
        
        # Coletar dependências para todos os componentes solicitados
        for component in components_to_install:
            collect_dependencies(component)
        
        # Criar um subgrafo apenas com os componentes necessários
        subgraph_components = {name: data for name, data in self.components.items() 
                              if name in all_needed}
        
        # Criar um novo resolvedor para o subgrafo
        sub_resolver = DependencyResolver(subgraph_components)
        
        # Retornar a ordem topológica do subgrafo
        return sub_resolver.topological_sort()
    
    def get_dependents(self, component: str) -> List[str]:
        """
        Obtém todos os componentes que dependem do componente especificado.
        
        Args:
            component: Nome do componente
            
        Returns:
            Lista de componentes que dependem do componente especificado
        """
        dependents = []
        
        for name, dependencies in self.dependency_graph.items():
            if component in dependencies:
                dependents.append(name)
        
        return dependents
    
    def get_all_dependencies(self, component: str) -> Set[str]:
        """
        Obtém todas as dependências (diretas e indiretas) de um componente.
        
        Args:
            component: Nome do componente
            
        Returns:
            Conjunto com todas as dependências
        """
        if component not in self.components:
            return set()
        
        all_deps = set()
        visited = set()
        
        def collect_deps(comp: str):
            if comp in visited:
                return
            visited.add(comp)
            
            for dep in self.dependency_graph.get(comp, []):
                all_deps.add(dep)
                collect_deps(dep)
        
        collect_deps(component)
        return all_deps
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Valida todas as dependências do sistema.
        
        Returns:
            Tupla (é_válido, lista_de_erros)
        """
        errors = []
        
        # Verificar dependências circulares
        cycles = self.detect_circular_dependencies()
        for cycle in cycles:
            cycle_str = " -> ".join(cycle + [cycle[0]])
            errors.append(f"Dependência circular: {cycle_str}")
        
        # Verificar dependências inexistentes
        for component, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                if dep not in self.components:
                    errors.append(f"Componente '{component}' depende de '{dep}' que não existe")
        
        return len(errors) == 0, errors

def detect_circular_dependencies(components: Dict[str, Dict]) -> List[List[str]]:
    """
    Função utilitária para detectar dependências circulares.
    
    Args:
        components: Dicionário de componentes
        
    Returns:
        Lista de ciclos encontrados
    """
    resolver = DependencyResolver(components)
    return resolver.detect_circular_dependencies()

def get_installation_order(components: Dict[str, Dict], 
                          components_to_install: List[str] = None) -> List[str]:
    """
    Função utilitária para obter ordem de instalação.
    
    Args:
        components: Dicionário de componentes
        components_to_install: Lista de componentes a instalar (None para todos)
        
    Returns:
        Lista de componentes em ordem de instalação
        
    Raises:
        CircularDependencyError: Se dependências circulares forem encontradas
    """
    resolver = DependencyResolver(components)
    
    if components_to_install is None:
        return resolver.topological_sort()
    else:
        return resolver.get_installation_order(components_to_install)

if __name__ == "__main__":
    # Teste básico
    logging.basicConfig(level=logging.INFO)
    
    # Exemplo de componentes com dependência circular
    test_components = {
        "A": {"dependencies": ["B"]},
        "B": {"dependencies": ["C"]},
        "C": {"dependencies": ["A"]},  # Cria ciclo A -> B -> C -> A
        "D": {"dependencies": ["B"]},
        "E": {"dependencies": []}
    }
    
    resolver = DependencyResolver(test_components)
    
    print("Testando detecção de dependências circulares...")
    cycles = resolver.detect_circular_dependencies()
    
    if cycles:
        print(f"Dependências circulares encontradas: {cycles}")
    else:
        print("Nenhuma dependência circular encontrada")
    
    # Teste com componentes sem ciclos
    test_components_valid = {
        "A": {"dependencies": ["B", "C"]},
        "B": {"dependencies": ["D"]},
        "C": {"dependencies": ["D"]},
        "D": {"dependencies": []},
        "E": {"dependencies": ["A"]}
    }
    
    resolver_valid = DependencyResolver(test_components_valid)
    
    print("\nTestando ordenação topológica...")
    try:
        order = resolver_valid.topological_sort()
        print(f"Ordem de instalação: {order}")
    except CircularDependencyError as e:
        print(f"Erro: {e}")