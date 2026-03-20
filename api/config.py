from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://xpose:xpose@postgres:5432/xpose"
    DATABASE_URL_SYNC: str = "postgresql://xpose:xpose@postgres:5432/xpose"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-please-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    HIBP_API_KEY: str = ""
    MAXMIND_LICENSE: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

# Master list of all configurable API services
# module=None means the integration doesn't have a scanner yet
ALL_API_SERVICES = [
    # Existing modules
    {
        "key": "HIBP_API_KEY",
        "name": "Have I Been Pwned",
        "description": "Breach + paste detection ($3.50/mo)",
        "url": "https://haveibeenpwned.com/API/Key",
        "free": False,
        "module": "hibp",
    },
    {
        "key": "MAXMIND_LICENSE",
        "name": "MaxMind GeoLite2",
        "description": "IP geolocation database (free tier)",
        "url": "https://www.maxmind.com/en/geolite2/signup",
        "free": True,
        "module": "maxmind_geo",
    },
    {
        "key": "FULLCONTACT_API_KEY",
        "name": "FullContact",
        "description": "Person enrichment — name, age, social, company (100 free/mo)",
        "url": "https://www.fullcontact.com/developer/",
        "free": True,
        "module": "fullcontact",
    },
    # New services
    {
        "key": "GITHUB_TOKEN",
        "name": "GitHub Personal Token",
        "description": "Increases API rate from 60 to 5000 req/hr (free)",
        "url": "https://github.com/settings/tokens",
        "free": True,
        "module": "github_deep",
    },
    {
        "key": "SHODAN_API_KEY",
        "name": "Shodan",
        "description": "Internet-connected device search (free tier)",
        "url": "https://account.shodan.io/",
        "free": True,
        "module": None,
    },
    {
        "key": "VIRUSTOTAL_API_KEY",
        "name": "VirusTotal",
        "description": "URL/domain reputation (free tier: 4 req/min)",
        "url": "https://www.virustotal.com/gui/my-apikey",
        "free": True,
        "module": None,
    },
    {
        "key": "INTELX_API_KEY",
        "name": "Intelligence X",
        "description": "Darkweb, paste, breach search (free tier)",
        "url": "https://intelx.io/account?tab=developer",
        "free": True,
        "module": None,
    },
    {
        "key": "DEHASHED_API_KEY",
        "name": "Dehashed",
        "description": "Breach credential search ($5/mo)",
        "url": "https://dehashed.com/",
        "free": False,
        "module": None,
    },
    {
        "key": "HUNTER_API_KEY",
        "name": "Hunter.io",
        "description": "Email finder + domain search (25 free/mo)",
        "url": "https://hunter.io/api",
        "free": True,
        "module": None,
    },
    {
        "key": "PIMEYES_API_KEY",
        "name": "PimEyes",
        "description": "Reverse face search (paid)",
        "url": "https://pimeyes.com/en",
        "free": False,
        "module": "reverse_image",
    },
    # OAuth providers (SaaS connectors)
    {
        "key": "GOOGLE_CLIENT_ID",
        "name": "Google OAuth (Client ID)",
        "description": "Google OAuth2 client ID for account auditing",
        "url": "https://console.cloud.google.com/apis/credentials",
        "free": True,
        "module": "google_audit",
    },
    {
        "key": "GOOGLE_CLIENT_SECRET",
        "name": "Google OAuth (Client Secret)",
        "description": "Google OAuth2 client secret",
        "url": "https://console.cloud.google.com/apis/credentials",
        "free": True,
        "module": "google_audit",
    },
    {
        "key": "MICROSOFT_CLIENT_ID",
        "name": "Microsoft OAuth (Client ID)",
        "description": "Microsoft OAuth2 client ID for account auditing",
        "url": "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps",
        "free": True,
        "module": "microsoft_audit",
    },
    {
        "key": "MICROSOFT_CLIENT_SECRET",
        "name": "Microsoft OAuth (Client Secret)",
        "description": "Microsoft OAuth2 client secret",
        "url": "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps",
        "free": True,
        "module": "microsoft_audit",
    },
]
