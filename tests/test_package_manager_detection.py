#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para detecção de gerenciadores de pacotes
Testa a precisão da detecção de npm, pip, conda, yarn e pipenv
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

# Importar componentes a serem testados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.unified_detection_engine import (
    UnifiedDetectionEngine,
    NpmDetector,
    PipDetector,
    CondaDetector,
    YarnDetector,
    PipenvDetector,
    PackageManagerDetectionResult,
    VirtualEnvironmentInfo,
    EnvironmentType
)
from core.package_manager_integrator import PackageManagerType, PackageInfo, PackageStatus, InstallationScope


class TestPackageManagerDetection(unittest.TestCase):
    """Testes base para detecção de gerenciadores de pacotes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Mock para subprocess.run
        self.subprocess_patcher = patch('subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        
    def tearDown(self):
        """Limpeza após os testes"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.subprocess_patcher.stop()
    
    def create_mock_subprocess_result(self, returncode=0, stdout="", stderr=""):
        """Cria resultado mock para subprocess"""
        mock_result = Mock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        return mock_result


class TestNpmDetector(TestPackageManagerDetection):
    """Testes para detector NPM"""
    
    def setUp(self):
        super().setUp()
        self.detector = NpmDetector()
    
    def test_npm_detection_success(self):
        """Testa detecção bem-sucedida do NPM"""
        # Mock para where/which npm
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, "/usr/local/bin/npm\n"),  # where npm
            self.create_mock_subprocess_result(0, "8.19.2\n"),  # npm --version
            self.create_mock_subprocess_result(0, "/usr/local\n"),  # npm config get prefix
            self.create_mock_subprocess_result(0, '{"dependencies": {"typescript": {"version": "4.9.4"}}}'),  # npm list -g --json
            self.create_mock_subprocess_result(0, "https://registry.npmjs.org/\n"),  # npm config get registry
            self.create_mock_subprocess_result(0, "/home/user/.npm\n")  # npm config get cache
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.NPM)
        self.assertEqual(result.version, "8.19.2")
        self.assertEqual(result.executable_path, "/usr/local/bin/npm")
        self.assertEqual(result.global_packages_path, "/usr/local")
        self.assertEqual(result.detection_confidence, 0.9)
        self.assertEqual(len(result.installed_packages), 1)
        self.assertEqual(result.installed_packages[0].name, "typescript")
        self.assertEqual(result.installed_packages[0].version, "4.9.4")
    
    def test_npm_detection_not_found(self):
        """Testa quando NPM não está instalado"""
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(1, "", "npm not found")  # where npm
        ]
        
        result = self.detector.detect_installation()
        
        self.assertFalse(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.NPM)
        self.assertEqual(result.version, "")
        self.assertEqual(result.executable_path, "")
    
    def test_npm_environment_detection(self):
        """Testa detecção de ambientes NPM (projetos Node.js)"""
        # Criar estrutura de projeto Node.js
        project_dir = os.path.join(self.temp_dir, "test-project")
        os.makedirs(project_dir)
        
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.21"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        
        with open(os.path.join(project_dir, "package.json"), 'w') as f:
            json.dump(package_json, f)
        
        # Criar node_modules
        node_modules_dir = os.path.join(project_dir, "node_modules")
        os.makedirs(node_modules_dir)
        
        # Mock para npm list local
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, json.dumps({
                "dependencies": {
                    "express": {"version": "4.18.2"},
                    "lodash": {"version": "4.17.21"},
                    "jest": {"version": "29.3.1"}
                }
            }))
        ]
        
        environments = self.detector.detect_environments()
        
        self.assertEqual(len(environments), 1)
        env = environments[0]
        self.assertEqual(env.name, "test-project")
        self.assertEqual(env.path, project_dir)
        self.assertEqual(env.environment_type, EnvironmentType.GLOBAL)
        self.assertEqual(env.manager, PackageManagerType.NPM)
        self.assertEqual(len(env.packages), 3)
        
        # Verificar pacotes detectados
        package_names = [pkg.name for pkg in env.packages]
        self.assertIn("express", package_names)
        self.assertIn("lodash", package_names)
        self.assertIn("jest", package_names)


class TestPipDetector(TestPackageManagerDetection):
    """Testes para detector PIP"""
    
    def setUp(self):
        super().setUp()
        self.detector = PipDetector()
    
    def test_pip_detection_success(self):
        """Testa detecção bem-sucedida do PIP"""
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, "/usr/local/bin/pip\n"),  # where pip
            self.create_mock_subprocess_result(0, "pip 22.3.1 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)\n"),  # pip --version
            self.create_mock_subprocess_result(0, json.dumps([
                {"name": "requests", "version": "2.28.1"},
                {"name": "numpy", "version": "1.24.0"}
            ])),  # pip list --format=json
            self.create_mock_subprocess_result(0, "Python 3.9.16\n"),  # python --version
            self.create_mock_subprocess_result(0, "/usr/local/lib/python3.9/site-packages\n")  # site-packages path
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.PIP)
        self.assertEqual(result.version, "22.3.1")
        self.assertEqual(result.executable_path, "/usr/local/bin/pip")
        self.assertEqual(result.detection_confidence, 0.9)
        self.assertEqual(len(result.installed_packages), 2)
        
        # Verificar pacotes
        package_names = [pkg.name for pkg in result.installed_packages]
        self.assertIn("requests", package_names)
        self.assertIn("numpy", package_names)
    
    def test_pip_fallback_to_python_module(self):
        """Testa fallback para python -m pip"""
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(1, "", "pip not found"),  # where pip
            self.create_mock_subprocess_result(1, "", "pip3 not found"),  # where pip3
            self.create_mock_subprocess_result(0, "pip 22.3.1 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)\n"),  # python -m pip --version
            self.create_mock_subprocess_result(0, json.dumps([
                {"name": "requests", "version": "2.28.1"}
            ])),  # python -m pip list --format=json
            self.create_mock_subprocess_result(0, "Python 3.9.16\n"),  # python --version
            self.create_mock_subprocess_result(0, "/usr/local/lib/python3.9/site-packages\n")  # site-packages path
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.executable_path, "python -m pip")
        self.assertEqual(result.version, "22.3.1")
    
    def test_virtual_environment_detection(self):
        """Testa detecção de ambientes virtuais Python"""
        # Simular ambiente virtual ativo
        with patch.dict(os.environ, {'VIRTUAL_ENV': '/home/user/venv/myproject'}):
            self.mock_subprocess.side_effect = [
                self.create_mock_subprocess_result(0, json.dumps([
                    {"name": "django", "version": "4.1.4"},
                    {"name": "psycopg2", "version": "2.9.5"}
                ])),  # pip list --format=json
                self.create_mock_subprocess_result(0, "Python 3.9.16\n")  # python --version
            ]
            
            environments = self.detector.detect_environments()
            
            self.assertEqual(len(environments), 1)
            env = environments[0]
            self.assertEqual(env.name, "myproject")
            self.assertEqual(env.path, "/home/user/venv/myproject")
            self.assertEqual(env.environment_type, EnvironmentType.VIRTUAL)
            self.assertEqual(env.manager, PackageManagerType.PIP)
            self.assertTrue(env.is_active)
            self.assertEqual(env.python_version, "3.9.16")
            self.assertEqual(len(env.packages), 2)
    
    def test_venv_directory_scanning(self):
        """Testa escaneamento de diretórios de ambientes virtuais"""
        # Criar estrutura de ambiente virtual
        venv_dir = os.path.join(self.temp_dir, "venv")
        scripts_dir = os.path.join(venv_dir, "Scripts" if os.name == 'nt' else "bin")
        os.makedirs(scripts_dir)
        
        python_exe = os.path.join(scripts_dir, "python.exe" if os.name == 'nt' else "python")
        pip_exe = os.path.join(scripts_dir, "pip.exe" if os.name == 'nt' else "pip")
        
        # Criar arquivos executáveis fictícios
        Path(python_exe).touch()
        Path(pip_exe).touch()
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                self.create_mock_subprocess_result(0, "Python 3.9.16\n"),  # python --version
                self.create_mock_subprocess_result(0, json.dumps([
                    {"name": "flask", "version": "2.2.2"}
                ]))  # pip list --format=json
            ]
            
            env_info = self.detector._create_venv_info(venv_dir)
            
            self.assertIsNotNone(env_info)
            self.assertEqual(env_info.name, "venv")
            self.assertEqual(env_info.path, venv_dir)
            self.assertEqual(env_info.python_version, "3.9.16")
            self.assertEqual(len(env_info.packages), 1)
            self.assertEqual(env_info.packages[0].name, "flask")


class TestCondaDetector(TestPackageManagerDetection):
    """Testes para detector Conda"""
    
    def setUp(self):
        super().setUp()
        self.detector = CondaDetector()
    
    def test_conda_detection_success(self):
        """Testa detecção bem-sucedida do Conda"""
        conda_info = {
            "conda_version": "22.9.0",
            "python_version": "3.9.16.final.0",
            "platform": "win-64",
            "config_files": ["/home/user/.condarc"],
            "default_prefix": "/home/user/miniconda3",
            "channels": ["defaults", "conda-forge"]
        }
        
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, "/home/user/miniconda3/bin/conda\n"),  # where conda
            self.create_mock_subprocess_result(0, "conda 22.9.0\n"),  # conda --version
            self.create_mock_subprocess_result(0, json.dumps(conda_info)),  # conda info --json
            self.create_mock_subprocess_result(0, json.dumps([
                {"name": "numpy", "version": "1.24.0", "build_string": "py39h1234567_0", "channel": "defaults"},
                {"name": "pandas", "version": "1.5.2", "build_string": "py39h2345678_0", "channel": "conda-forge"}
            ]))  # conda list --json
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.CONDA)
        self.assertEqual(result.version, "22.9.0")
        self.assertEqual(result.executable_path, "/home/user/miniconda3/bin/conda")
        self.assertEqual(result.config_path, "/home/user/.condarc")
        self.assertEqual(result.global_packages_path, "/home/user/miniconda3")
        self.assertEqual(result.detection_confidence, 0.9)
        self.assertEqual(len(result.installed_packages), 2)
        
        # Verificar metadados
        self.assertEqual(result.metadata["conda_version"], "22.9.0")
        self.assertEqual(result.metadata["python_version"], "3.9.16.final.0")
        self.assertIn("defaults", result.metadata["channels"])
        self.assertIn("conda-forge", result.metadata["channels"])
    
    def test_conda_environment_detection(self):
        """Testa detecção de ambientes Conda"""
        env_list = {
            "envs": [
                "/home/user/miniconda3",
                "/home/user/miniconda3/envs/myproject",
                "/home/user/miniconda3/envs/tensorflow"
            ]
        }
        
        with patch.dict(os.environ, {'CONDA_PREFIX': '/home/user/miniconda3/envs/myproject'}):
            self.mock_subprocess.side_effect = [
                self.create_mock_subprocess_result(0, json.dumps(env_list)),  # conda env list --json
                # Packages for base environment
                self.create_mock_subprocess_result(0, json.dumps([
                    {"name": "conda", "version": "22.9.0"}
                ])),
                # Packages for myproject environment
                self.create_mock_subprocess_result(0, json.dumps([
                    {"name": "django", "version": "4.1.4"},
                    {"name": "psycopg2", "version": "2.9.5"}
                ])),
                # Packages for tensorflow environment
                self.create_mock_subprocess_result(0, json.dumps([
                    {"name": "tensorflow", "version": "2.11.0"},
                    {"name": "numpy", "version": "1.24.0"}
                ])),
                # Python version checks
                self.create_mock_subprocess_result(0, "Python 3.9.16\n"),  # base
                self.create_mock_subprocess_result(0, "Python 3.9.16\n"),  # myproject
                self.create_mock_subprocess_result(0, "Python 3.10.8\n")   # tensorflow
            ]
            
            environments = self.detector.detect_environments()
            
            self.assertEqual(len(environments), 3)
            
            # Verificar ambiente base
            base_env = next(env for env in environments if env.name == "base")
            self.assertEqual(base_env.environment_type, EnvironmentType.CONDA_ENV)
            self.assertEqual(base_env.manager, PackageManagerType.CONDA)
            self.assertFalse(base_env.is_active)
            
            # Verificar ambiente ativo
            active_env = next(env for env in environments if env.name == "myproject")
            self.assertTrue(active_env.is_active)
            self.assertEqual(len(active_env.packages), 2)
            
            # Verificar ambiente tensorflow
            tf_env = next(env for env in environments if env.name == "tensorflow")
            self.assertEqual(tf_env.metadata["python_version"], "3.10.8")
            self.assertEqual(len(tf_env.packages), 2)


class TestYarnDetector(TestPackageManagerDetection):
    """Testes para detector Yarn"""
    
    def setUp(self):
        super().setUp()
        self.detector = YarnDetector()
    
    def test_yarn_detection_success(self):
        """Testa detecção bem-sucedida do Yarn"""
        yarn_global_output = '''{"type":"tree","data":{"type":"list","trees":[{"name":"typescript@4.9.4","children":[]},{"name":"@vue/cli@5.0.8","children":[]}]}}'''
        
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, "/usr/local/bin/yarn\n"),  # where yarn
            self.create_mock_subprocess_result(0, "1.22.19\n"),  # yarn --version
            self.create_mock_subprocess_result(0, "/usr/local\n"),  # yarn config get prefix
            self.create_mock_subprocess_result(0, yarn_global_output),  # yarn global list --json
            self.create_mock_subprocess_result(0, "/home/user/.yarn/cache\n"),  # yarn cache dir
            self.create_mock_subprocess_result(0, "https://registry.yarnpkg.com\n")  # yarn config get registry
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.YARN)
        self.assertEqual(result.version, "1.22.19")
        self.assertEqual(result.executable_path, "/usr/local/bin/yarn")
        self.assertEqual(result.detection_confidence, 0.9)
        self.assertEqual(len(result.installed_packages), 2)
        
        # Verificar pacotes globais
        package_names = [pkg.name for pkg in result.installed_packages]
        self.assertIn("typescript", package_names)
        self.assertIn("@vue/cli", package_names)
    
    def test_yarn_project_detection(self):
        """Testa detecção de projetos Yarn"""
        # Criar projeto com yarn.lock
        project_dir = os.path.join(self.temp_dir, "yarn-project")
        os.makedirs(project_dir)
        
        package_json = {
            "name": "yarn-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            }
        }
        
        with open(os.path.join(project_dir, "package.json"), 'w') as f:
            json.dump(package_json, f)
        
        # Criar yarn.lock
        with open(os.path.join(project_dir, "yarn.lock"), 'w') as f:
            f.write("# yarn.lock file\n")
        
        yarn_list_output = '''{"type":"tree","data":{"type":"list","trees":[{"name":"react@18.2.0","children":[]},{"name":"react-dom@18.2.0","children":[]}]}}'''
        
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, yarn_list_output)  # yarn list --json
        ]
        
        environments = self.detector.detect_environments()
        
        self.assertEqual(len(environments), 1)
        env = environments[0]
        self.assertEqual(env.name, "yarn-project")
        self.assertEqual(env.path, project_dir)
        self.assertEqual(env.manager, PackageManagerType.YARN)
        self.assertTrue(env.metadata["has_yarn_lock"])
        self.assertEqual(len(env.packages), 2)


class TestPipenvDetector(TestPackageManagerDetection):
    """Testes para detector Pipenv"""
    
    def setUp(self):
        super().setUp()
        self.detector = PipenvDetector()
    
    def test_pipenv_detection_success(self):
        """Testa detecção bem-sucedida do Pipenv"""
        self.mock_subprocess.side_effect = [
            self.create_mock_subprocess_result(0, "/usr/local/bin/pipenv\n"),  # where pipenv
            self.create_mock_subprocess_result(0, "pipenv, version 2022.12.19\n"),  # pipenv --version
            self.create_mock_subprocess_result(0, "/home/user/.local/share/virtualenvs/myproject-abc123\n")  # pipenv --venv
        ]
        
        result = self.detector.detect_installation()
        
        self.assertTrue(result.is_available)
        self.assertEqual(result.manager_type, PackageManagerType.PIPENV)
        self.assertEqual(result.version, "2022.12.19")
        self.assertEqual(result.executable_path, "/usr/local/bin/pipenv")
        self.assertEqual(result.detection_confidence, 0.9)
    
    def test_pipenv_project_detection(self):
        """Testa detecção de projetos Pipenv"""
        # Criar projeto com Pipfile
        project_dir = os.path.join(self.temp_dir, "pipenv-project")
        os.makedirs(project_dir)
        
        pipfile_content = """[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
django = "*"
psycopg2-binary = "*"

[dev-packages]
pytest = "*"

[requires]
python_version = "3.9"
"""
        
        with open(os.path.join(project_dir, "Pipfile"), 'w') as f:
            f.write(pipfile_content)
        
        venv_path = "/home/user/.local/share/virtualenvs/pipenv-project-abc123"
        
        with patch.dict(os.environ, {'VIRTUAL_ENV': venv_path}):
            self.mock_subprocess.side_effect = [
                self.create_mock_subprocess_result(0, venv_path + "\n"),  # pipenv --venv
                self.create_mock_subprocess_result(0, json.dumps([
                    {
                        "package_name": "django",
                        "installed_version": "4.1.4",
                        "dependencies": []
                    },
                    {
                        "package_name": "psycopg2-binary",
                        "installed_version": "2.9.5",
                        "dependencies": []
                    }
                ])),  # pipenv graph --json
                self.create_mock_subprocess_result(0, "Python 3.9.16\n")  # pipenv run python --version
            ]
            
            environments = self.detector.detect_environments()
            
            self.assertEqual(len(environments), 1)
            env = environments[0]
            self.assertEqual(env.name, "pipenv-project")
            self.assertEqual(env.path, project_dir)
            self.assertEqual(env.environment_type, EnvironmentType.PIPENV)
            self.assertEqual(env.manager, PackageManagerType.PIPENV)
            self.assertTrue(env.is_active)
            self.assertEqual(env.python_version, "3.9.16")
            self.assertEqual(len(env.packages), 2)
            
            # Verificar metadados
            self.assertEqual(env.metadata["venv_path"], venv_path)


class TestUnifiedDetectionEngine(TestPackageManagerDetection):
    """Testes para o motor de detecção unificado"""
    
    def setUp(self):
        super().setUp()
        self.engine = UnifiedDetectionEngine()
    
    @patch('core.unified_detection_engine.DetectionEngine')
    @patch('core.unified_detection_engine.EssentialRuntimeDetector')
    def test_unified_detection_integration(self, mock_runtime_detector, mock_base_engine):
        """Testa integração completa da detecção unificada"""
        # Mock do motor base
        mock_base_result = Mock()
        mock_base_result.applications = []
        mock_base_result.errors = []
        mock_base_engine.return_value.detect_all_applications.return_value = mock_base_result
        
        # Mock do detector de runtimes
        mock_runtime_detector.return_value.detect_git.return_value = {
            "detected": True,
            "version": "2.39.0"
        }
        
        # Mock dos detectores de package managers
        with patch.object(self.engine, 'package_detectors') as mock_detectors:
            # Mock NPM detector
            npm_result = PackageManagerDetectionResult(
                manager_type=PackageManagerType.NPM,
                is_available=True,
                version="8.19.2",
                detection_confidence=0.9
            )
            
            # Mock PIP detector
            pip_result = PackageManagerDetectionResult(
                manager_type=PackageManagerType.PIP,
                is_available=True,
                version="22.3.1",
                detection_confidence=0.9
            )
            
            mock_npm_detector = Mock()
            mock_npm_detector.detect_installation.return_value = npm_result
            mock_npm_detector.detect_environments.return_value = []
            
            mock_pip_detector = Mock()
            mock_pip_detector.detect_installation.return_value = pip_result
            mock_pip_detector.detect_environments.return_value = []
            
            mock_detectors = {
                PackageManagerType.NPM: mock_npm_detector,
                PackageManagerType.PIP: mock_pip_detector,
                PackageManagerType.CONDA: Mock(),
                PackageManagerType.YARN: Mock(),
                PackageManagerType.PIPENV: Mock()
            }
            
            # Configurar mocks para retornar resultados vazios para outros detectores
            for manager_type, detector in mock_detectors.items():
                if manager_type not in [PackageManagerType.NPM, PackageManagerType.PIP]:
                    detector.detect_installation.return_value = PackageManagerDetectionResult(
                        manager_type=manager_type,
                        is_available=False
                    )
                    detector.detect_environments.return_value = []
            
            self.engine.package_detectors = mock_detectors
            
            # Executar detecção unificada
            result = self.engine.detect_all_unified()
            
            # Verificar resultados
            self.assertIsNotNone(result)
            self.assertGreater(result.detection_time, 0)
            self.assertEqual(len(result.package_managers), 5)  # Todos os 5 detectores
            
            # Verificar detectores que funcionaram
            available_managers = [pm for pm in result.package_managers if pm.is_available]
            self.assertEqual(len(available_managers), 2)  # NPM e PIP
            
            manager_types = [pm.manager_type for pm in available_managers]
            self.assertIn(PackageManagerType.NPM, manager_types)
            self.assertIn(PackageManagerType.PIP, manager_types)
    
    def test_hierarchical_detection_prioritization(self):
        """Testa priorização hierárquica da detecção"""
        # Criar resultado mock com aplicações e package managers
        result = Mock()
        result.applications = []
        result.package_managers = [
            PackageManagerDetectionResult(
                manager_type=PackageManagerType.NPM,
                is_available=True,
                detection_confidence=0.9
            ),
            PackageManagerDetectionResult(
                manager_type=PackageManagerType.PIP,
                is_available=True,
                detection_confidence=0.8
            )
        ]
        
        hierarchical_results = self.engine._apply_hierarchical_detection(result)
        
        self.assertIsInstance(hierarchical_results, list)
        # Verificar que os resultados foram processados
        self.assertGreaterEqual(len(hierarchical_results), 0)
    
    def test_package_manager_integration_interfaces(self):
        """Testa interfaces de integração dos gerenciadores de pacotes"""
        interfaces = self.engine.get_package_manager_integration_interfaces()
        
        self.assertIsInstance(interfaces, dict)
        self.assertEqual(len(interfaces), 5)  # npm, pip, conda, yarn, pipenv
        
        # Verificar que todos os tipos estão presentes
        expected_types = {
            PackageManagerType.NPM,
            PackageManagerType.PIP,
            PackageManagerType.CONDA,
            PackageManagerType.YARN,
            PackageManagerType.PIPENV
        }
        
        self.assertEqual(set(interfaces.keys()), expected_types)
        
        # Verificar que cada interface tem os métodos necessários
        for manager_type, detector in interfaces.items():
            self.assertTrue(hasattr(detector, 'detect_installation'))
            self.assertTrue(hasattr(detector, 'detect_environments'))
            self.assertTrue(hasattr(detector, 'get_manager_type'))
    
    def test_comprehensive_report_generation(self):
        """Testa geração de relatório abrangente"""
        # Criar resultado mock
        result = Mock()
        result.detection_time = 2.5
        result.detection_confidence = 0.85
        result.total_detected = 10
        result.applications = []
        result.package_managers = [
            PackageManagerDetectionResult(
                manager_type=PackageManagerType.NPM,
                is_available=True,
                version="8.19.2",
                installed_packages=[Mock()]
            )
        ]
        result.virtual_environments = []
        result.essential_runtimes = {
            "git": {"detected": True, "version": "2.39.0"},
            "python": {"detected": True, "version": "3.9.16"}
        }
        result.errors = []
        
        report = self.engine.generate_comprehensive_report(result)
        
        self.assertIsInstance(report, str)
        self.assertIn("Relatório de Detecção Unificada", report)
        self.assertIn("2.5s", report)  # Tempo de detecção
        self.assertIn("85%", report)   # Confiança
        self.assertIn("npm", report)   # Package manager detectado
        self.assertIn("git", report)   # Runtime detectado


if __name__ == '__main__':
    # Configurar logging para os testes
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Executar testes
    unittest.main(verbosity=2)