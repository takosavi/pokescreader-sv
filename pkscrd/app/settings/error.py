class SettingsError(RuntimeError):
    """設定ミスに由来するエラー."""


class SettingsFileNotFoundError(SettingsError):
    """設定ファイルが存在しないエラー."""
