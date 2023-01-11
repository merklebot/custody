from pydantic import BaseSettings, Field


class DBSettings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")


class IPFSSettings(BaseSettings):
    ORIGINAL_IPFS_NODE_ADDRESS = Field(default="localhost", env="IPFS_ADDRESS")


class WEB3Settings(BaseSettings):
    CRUST_MNEMONIC: str = Field(..., env="CRUST_MNEMONIC")


class Settings(BaseSettings):
    DB: DBSettings = DBSettings()
    WEB3: WEB3Settings = WEB3Settings()
    IPFS: IPFSSettings = IPFSSettings()


settings = Settings()
