from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class Profile:
    id: str
    name: str
    airtable_token: str
    airtable_base_id: str
    airtable_table_id: str
    baserow_token: str
    baserow_table_id: str
    target_folder: str = "base"
    col_artist: str = "Subtitle"
    col_title: str = "Title"
    col_audio: str = "Ringtone"
    col_icon: str = "Icon"
    download_folder_airtable: str = "Descargas/desde_airtable"
    download_folder_baserow: str = "Descargas/desde_baserow"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class ProfileRepository:
    def get_all(self) -> List[Profile]:
        raise NotImplementedError

    def get_by_id(self, profile_id: str) -> Profile:
        raise NotImplementedError

    def save(self, profile: Profile) -> None:
        raise NotImplementedError

    def delete(self, profile_id: str) -> None:
        raise NotImplementedError
