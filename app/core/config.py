from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Planner API"
    db_connection: str = Field(alias="DB_CONNECTION")
    secret: str = Field(alias="SECRET")
    expires_in: str = Field(default="7d", alias="EXPIRESIN")
    host: str | None = Field(default=None, alias="HOST")
    port_mail: int | None = Field(default=None, alias="PORT_MAIL")
    user: str | None = Field(default=None, alias="USER")
    password_mail: str | None = Field(default=None, alias="PASS")
    service: str | None = Field(default=None, alias="SERVICE")
    base_url: str | None = Field(default=None, alias="BASE_URL")


settings = Settings()
