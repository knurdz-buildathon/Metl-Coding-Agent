from enum import Enum
from typing import Optional


class ResourceCatalogEntry:
    def __init__(
        self,
        resource_type: str,
        name: str,
        description: str,
        env_vars: list[str],
        required: bool = False,
    ):
        self.resource_type = resource_type
        self.name = name
        self.description = description
        self.env_vars = env_vars
        self.required = required


class ResourceCatalog:
    """Registry of available/template resources the agent can request."""

    def __init__(self):
        self._entries: dict[str, ResourceCatalogEntry] = {
            "postgresql": ResourceCatalogEntry(
                resource_type="database",
                name="PostgreSQL",
                description="PostgreSQL relational database",
                env_vars=["DATABASE_URL", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME"],
            ),
            "mysql": ResourceCatalogEntry(
                resource_type="database",
                name="MySQL",
                description="MySQL relational database",
                env_vars=["DATABASE_URL", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME"],
            ),
            "sqlite": ResourceCatalogEntry(
                resource_type="database",
                name="SQLite",
                description="SQLite file-based database (preview only)",
                env_vars=[],
            ),
            "redis": ResourceCatalogEntry(
                resource_type="cache",
                name="Redis",
                description="Redis cache and message broker",
                env_vars=["REDIS_URL"],
            ),
            "s3": ResourceCatalogEntry(
                resource_type="file_storage",
                name="S3",
                description="AWS S3-compatible object storage",
                env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET", "AWS_REGION"],
            ),
            "sendgrid": ResourceCatalogEntry(
                resource_type="email",
                name="SendGrid",
                description="SendGrid email service",
                env_vars=["SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL"],
            ),
            "resend": ResourceCatalogEntry(
                resource_type="email",
                name="Resend",
                description="Resend email service",
                env_vars=["RESEND_API_KEY", "RESEND_FROM_EMAIL"],
            ),
            "auth0": ResourceCatalogEntry(
                resource_type="auth",
                name="Auth0",
                description="Auth0 authentication service",
                env_vars=["AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET"],
            ),
            "clerk": ResourceCatalogEntry(
                resource_type="auth",
                name="Clerk",
                description="Clerk authentication service",
                env_vars=["NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY"],
            ),
            "stripe": ResourceCatalogEntry(
                resource_type="payment",
                name="Stripe",
                description="Stripe payment processing",
                env_vars=["STRIPE_SECRET_KEY", "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"],
            ),
            "elasticsearch": ResourceCatalogEntry(
                resource_type="search",
                name="Elasticsearch",
                description="Elasticsearch search engine",
                env_vars=["ELASTICSEARCH_URL", "ELASTICSEARCH_API_KEY"],
            ),
            "meilisearch": ResourceCatalogEntry(
                resource_type="search",
                name="Meilisearch",
                description="Meilisearch search engine",
                env_vars=["MEILISEARCH_URL", "MEILISEARCH_API_KEY"],
            ),
        }

    def get(self, name: str) -> Optional[ResourceCatalogEntry]:
        return self._entries.get(name.lower())

    def list_by_type(self, resource_type: str) -> list[ResourceCatalogEntry]:
        return [e for e in self._entries.values() if e.resource_type == resource_type]

    def list_all(self) -> list[ResourceCatalogEntry]:
        return list(self._entries.values())

    def add_custom(self, entry: ResourceCatalogEntry) -> None:
        self._entries[entry.name.lower()] = entry