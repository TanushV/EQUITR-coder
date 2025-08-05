import os
import yaml
from typing import Dict, Any, List

class ProfileManager:
    def __init__(self, profiles_dir: str = 'equitrcoder/profiles'):
        self.profiles_dir = profiles_dir
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        profiles = {}
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                profile_name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.profiles_dir, filename)
                with open(filepath, 'r') as f:
                    profile_data = yaml.safe_load(f)
                    profiles[profile_name] = profile_data
        return profiles

    def get_profile(self, name: str) -> Dict[str, Any]:
        profile = self.profiles.get(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found.")
        return profile

    def list_profiles(self) -> List[str]:
        return list(self.profiles.keys()) 