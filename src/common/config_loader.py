import os
from pathlib import Path
from configparser import ConfigParser
from typing import Any, Dict

import yaml  # Requires PyYAML (install via pip install pyyaml)


class ConfigLoader:
    """
    ConfigLoader: Utility class for loading and parsing application configuration files.
    """

    def __init__(self):
        """
        Initialize the ConfigLoader:
          - Detects the execution environment.
          - Loads the relevant configuration files.
        """
        self.base_dir = Path(__file__).resolve().parent
        self.environment = self._get_environment()
        self.config = {}  # Final configuration stored as a dictionary
        self.settings = None  # Cached settings object
        self._load_config()

    def _get_environment(self) -> str:
        """
        Detect the application's execution environment.

        Returns:
            str: The environment name (e.g., 'development', 'production').

        Raises:
            FileNotFoundError: If the environment configuration file is missing.
            KeyError: If the 'ENVIRONMENT' section or 'env' key is missing.
        """
        # Use the APP_ENV environment variable if available
        if env_var := os.getenv("APP_ENV"):
            return env_var.strip().lower()

        # Search for either bot-control-env.yaml or bot-control-env.ini in the environments directory.
        # YAML file is prioritized if both exist.
        base_env_dir = self.base_dir / "../../config/environments"
        yaml_env_file = base_env_dir / "bot-control-env.yaml"
        ini_env_file = base_env_dir / "bot-control-env.ini"

        if yaml_env_file.exists():
            with open(yaml_env_file, 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f)
            try:
                return env_config['ENVIRONMENT']['env'].strip().lower()
            except KeyError:
                raise KeyError("Missing 'ENVIRONMENT' section or 'env' key in bot-control-env.yaml")
        elif ini_env_file.exists():
            parser = ConfigParser()
            parser.read(ini_env_file, encoding='utf-8')
            try:
                return parser['ENVIRONMENT']['env'].strip().lower()
            except KeyError:
                raise KeyError("Missing 'ENVIRONMENT' section or 'env' key in bot-control-env.ini")
        else:
            raise FileNotFoundError(f"Environment configuration file not found in {base_env_dir}")

    def _load_config(self):
        """
        Load both common and environment-specific configuration files.
        Supports both INI and YAML formats. If both formats exist for the same configuration base,
        the YAML file is prioritized.
        """
        base_env_dir = self.base_dir / "../../config/environments"
        # Define configuration file bases
        file_bases = [
            "bot-control-env",
            f"bot-controller-{self.environment}"
        ]
        config_files = []
        for base in file_bases:
            # Prioritize YAML over INI if both exist
            yaml_path = base_env_dir / f"{base}.yaml"
            ini_path = base_env_dir / f"{base}.ini"
            if yaml_path.exists():
                config_files.append(yaml_path)
            elif ini_path.exists():
                config_files.append(ini_path)

        if not config_files:
            raise FileNotFoundError("No valid configuration files found.")

        # Merge configuration files into a single dictionary
        merged_config: Dict[str, Dict[str, Any]] = {}
        for config_path in config_files:
            if config_path.suffix.lower() in {".yaml", ".yml"}:
                with open(config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                # Assume yaml_config is a dictionary where each top-level key is a section
                for section, section_dict in yaml_config.items():
                    if not isinstance(section_dict, dict):
                        continue  # Skip sections that are not in dict format
                    if section in merged_config:
                        merged_config[section].update(section_dict)
                    else:
                        merged_config[section] = section_dict
            elif config_path.suffix.lower() == ".ini":
                parser = ConfigParser()
                parser.read(config_path, encoding='utf-8')
                for section in parser.sections():
                    section_dict = {}
                    for key in parser[section]:
                        section_dict[key] = parser[section][key]
                    if section in merged_config:
                        merged_config[section].update(section_dict)
                    else:
                        merged_config[section] = section_dict
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")

        self.config = merged_config

    def _parse_section(self, section: str) -> Any:
        """
        Parse a configuration section and return it as an object with attributes.

        Args:
            section (str): The name of the section to parse.

        Returns:
            Any: An object containing key-value pairs as attributes.

        Raises:
            ValueError: If the section is not found in the configuration.
        """
        if section not in self.config:
            raise ValueError(f"Section '{section}' not found in configuration.")

        class Section:
            def __init__(self, items: Dict[str, Any]):
                for key, value in items.items():
                    setattr(self, key, value)

        # Convert each key's value using _parse_value
        section_data = {key: self._parse_value(section, key) for key in self.config[section]}
        return Section(section_data)

    def _parse_value(self, section: str, key: str) -> Any:
        """
        Convert a configuration value to an appropriate data type.

        Args:
            section (str): The section name.
            key (str): The configuration key.

        Returns:
            Any: The converted configuration value.
        """
        value = self.config[section][key]
        # Values read from YAML may already be in the correct type.
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in {"true", "false"}:
                return lower_value == "true"

            try:
                # Attempt to convert to an integer or float
                return int(value) if '.' not in value else float(value)
            except ValueError:
                return value
        else:
            return value

    def get_settings(self) -> Any:
        """
        Load and cache all configuration settings as objects.

        Returns:
            Any: A settings object containing each section as attributes.
        """
        if self.settings:
            return self.settings

        class Settings:
            pass

        self.settings = Settings()
        # Add each section as a lowercase attribute (e.g., SERVICE -> service)
        for section in self.config.keys():
            setattr(self.settings, section.lower(), self._parse_section(section))

        return self.settings
