import json
import os
from typing import List, Optional
from hex_core.domain.profile import Profile, ProfileRepository

class JsonProfileRepository(ProfileRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _read_data(self) -> List[dict]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _write_data(self, data: List[dict]):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all(self) -> List[Profile]:
        data = self._read_data()
        return [Profile.from_dict(p) for p in data]

    def get_by_id(self, profile_id: str) -> Optional[Profile]:
        data = self._read_data()
        for p in data:
            if p.get('id') == profile_id:
                return Profile.from_dict(p)
        return None

    def save(self, profile: Profile) -> None:
        data = self._read_data()
        updated = False
        profile_dict = profile.to_dict()
        for i, p in enumerate(data):
            if p.get('id') == profile.id:
                data[i] = profile_dict
                updated = True
                break
        if not updated:
            data.append(profile_dict)
        self._write_data(data)

    def delete(self, profile_id: str) -> None:
        data = self._read_data()
        data = [p for p in data if p.get('id') != profile_id]
        self._write_data(data)
