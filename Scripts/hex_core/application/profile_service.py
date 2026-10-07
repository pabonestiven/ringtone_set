import uuid
from typing import List
from hex_core.domain.profile import Profile, ProfileRepository

class ProfileService:
    def __init__(self, repository: ProfileRepository):
        self.repository = repository

    def list_profiles(self) -> List[dict]:
        return [p.to_dict() for p in self.repository.get_all()]

    def create_or_update_profile(self, data: dict) -> dict:
        profile_id = data.get('id')
        if not profile_id:
            profile_id = str(uuid.uuid4())
            data['id'] = profile_id
            
        # Add default empty strings or defaults if missing
        fields = ['name', 'airtable_token', 'airtable_base_id', 'airtable_table_id', 'baserow_token', 'baserow_table_id']
        for f in fields:
            if f not in data:
                data[f] = ""
                
        if 'target_folder' not in data or not data['target_folder']: data['target_folder'] = "base"
        if 'col_artist' not in data or not data['col_artist']: data['col_artist'] = "Subtitle"
        if 'col_title' not in data or not data['col_title']: data['col_title'] = "Title"
        if 'col_audio' not in data or not data['col_audio']: data['col_audio'] = "Ringtone"
        if 'col_icon' not in data or not data['col_icon']: data['col_icon'] = "Icon"

        profile = Profile.from_dict(data)
        self.repository.save(profile)
        return profile.to_dict()

    def delete_profile(self, profile_id: str):
        self.repository.delete(profile_id)

    def get_profile(self, profile_id: str) -> Profile:
        return self.repository.get_by_id(profile_id)
