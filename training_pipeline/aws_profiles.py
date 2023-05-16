"""A class for reading and listing AWS profiles from a user profile config file."""
import configparser
import os


class UserProfiles:
    def __init__(self, path=None) -> None:
        if path is None:
            self.path = os.path.expanduser("~/.aws/config")
        self.config = configparser.ConfigParser()
        self.config.read(self.path)

    def list_profiles(self):
        return [p.replace("profile ", "") for p in self.config.sections()]

    def get_profile_id(self, profile_name: str) -> str:
        if "default" not in profile_name:
            profile_name = f"profile {profile_name}"
        if profile_name not in self.config.sections():
            raise ValueError(f"Profile '{profile_name}' not found")
        return self.config[profile_name]["sso_account_id"]

    def get_profile_name(self, profile_id: str) -> str:
        for each_section in self.config.sections():
            for key, value in self.config.items(each_section):
                if value == profile_id:
                    return each_section.replace("profile ", "")

        raise ValueError(f"Profile with id: '{profile_id}' not found")
