# Inspired by https://github.com/certbot/certbot/pull/5922
# and https://github.com/certbot/certbot/blob/master/certbot-dns-cloudflare/certbot_dns_cloudflare/_internal/dns_cloudflare.py
import logging
from typing import Callable, Any

from certbot import errors
from certbot.plugins import dns_common
from httpx import Client, RequestError

logger = logging.getLogger(__name__)


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for Alwaysdata

    This Authenticator uses the Alwaysdata API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using Alwaysdata for DNS)."
    ttl = 60

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: dns_common.CredentialsConfiguration | None = None

    @classmethod
    def add_parser_arguments(
        cls,
        add: Callable[..., None],
        default_propagation_seconds: int = 10,
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="Alwaysdata API credentials INI file")

    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a dns-01 challenge using the Alwaysdata API."

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "Alwaysdata API credentials INI file",
            {
                "api-key": "API key for Alwaysdata (eg. '123456789abcdef')",
                "account": "Name of the Alwaysdata account owning the domain (eg. 'nymous')",
            },
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_alwaysdata_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_alwaysdata_client().del_txt_record(
            domain, validation_name, validation
        )

    def _get_alwaysdata_client(self) -> "_AlwaysdataClient":
        if not self.credentials:
            raise errors.Error("Plugin has not been prepared")
        return _AlwaysdataClient(
            api_key=self.credentials.conf("api-key"),
            account=self.credentials.conf("account"),
        )


class _AlwaysdataClient:
    """
    Encapsulates all communication with the Alwaysdata API.
    """

    client: Client

    def __init__(self, api_key: str, account: str) -> None:
        self.client = Client(
            base_url="https://api.alwaysdata.com",
            auth=(f"{api_key} account={account}", ""),
            headers={
                "User-Agent": "certbot-dns-alwaysdata",
                "alwaysdata-synchronous": "yes",
            },
        )

    def add_txt_record(
        self,
        domain: str,
        record_name: str,
        record_content: str,
        record_ttl: int,
    ) -> None:
        """
        Add a TXT record using the supplied information.

        :param str domain: The domain to use to look up the Alwaysdata zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: If an error occurs communicating with the Alwaysdata API
        """
        domain_name, domain_id = self.find_domain(domain)
        record_data = {
            "domain": domain_id,
            "type": "TXT",
            "name": self.canonical_record_name(record_name, domain_name),
            "value": record_content,
            "ttl": record_ttl,
        }
        try:
            logger.debug(
                "Attempting to add record to domain %s: %s", domain_id, record_data
            )
            r = self.client.post("/v1/record/", json=record_data)
            r.raise_for_status()
        except RequestError as e:
            raise errors.PluginError(f"Error adding the TXT record: {e}")

    def del_txt_record(
        self,
        domain: str,
        record_name: str,
        record_content: str,
    ) -> None:
        domain_name, domain_id = self.find_domain(domain)
        record_data = {
            "domain": domain_id,
            "type": "TXT",
            "name": self.canonical_record_name(record_name, domain_name),
            "value": record_content,
        }
        try:
            r = self.client.get("/v1/record/", params=record_data)
            r.raise_for_status()
            records = r.json()
            if not records:
                logger.warning("No matching TXT record to delete, skipping cleanup")
                return
            if len(records) > 1:
                # prefer to not delete anything instead of deleting randomly
                logger.warning(
                    "Too many matching TXT records to delete, skipping cleanup"
                )
                return
            record = records[0]
        except RequestError as e:
            logger.warning(
                "Encountered error searching TXT record to delete, skipping cleanup: %s",
                e,
            )
            return
        try:
            r = self.client.delete(record["href"])
            r.raise_for_status()
            logger.debug("Deleted Alwaysdata TXT record: %s", record["href"])
        except RequestError as e:
            logger.warning(
                "Encountered error deleting TXT record, skipping cleanup: %s", e
            )

    def find_domain(self, domain_name: str) -> tuple[str, int]:
        """
        Find the Alwaysdata domain for a given domain name.
        :param str domain_name: The domain name for which to find the Alwaysdata domain.
        :returns: The domain name and domain ID, if found.
        :raises certbot.errors.PluginError: If the domain cannot be found.
        """
        zone_names = dns_common.base_domain_name_guesses(domain_name)

        for zone_name in zone_names:
            try:
                response = self.client.get("/v1/domain/", params={"name": zone_name})
                if response.is_success:
                    for domain in response.json():
                        # check for exact match
                        if domain["name"] == zone_name:
                            return zone_name, domain["id"]
            except RequestError as e:
                raise errors.PluginError(f"Encountered error finding zone domain: {e}")

        raise errors.PluginError(
            f"Unable to determine domain for {domain_name} using zone names: {zone_names}."
        )

    @staticmethod
    def canonical_record_name(record_name: str, domain_name: str) -> str:
        """
        Strip the domain name from the record name, as Alwaysdata expects name ``foo.bar`` when
        adding the ``foo.bar.domain.com`` record.
        :param str record_name: The full record name
        :param str domain_name: The domain name managing the DNS record
        """
        return record_name.removesuffix(f".{domain_name}")
