"""Relay interface to EventsServerEventLogger generated by glean_parser."""

from __future__ import annotations
from datetime import datetime
from logging import getLogger
from typing import Any, TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest

from ipware import get_client_ip

from .glean.server_events import EventsServerEventLogger, GLEAN_EVENT_MOZLOG_TYPE
from .types import RELAY_CHANNEL_NAME

if TYPE_CHECKING:
    from emails.models import RelayAddress, DomainAddress


class RelayGleanLogger(EventsServerEventLogger):
    def __init__(
        self,
        application_id: str,
        app_display_version: str,
        channel: RELAY_CHANNEL_NAME,
    ):
        assert settings.GLEAN_EVENT_MOZLOG_TYPE == GLEAN_EVENT_MOZLOG_TYPE
        self._logger = getLogger(GLEAN_EVENT_MOZLOG_TYPE)
        super().__init__(
            application_id=application_id,
            app_display_version=app_display_version,
            channel=channel,
        )

    def log_email_mask_created(
        self,
        *,
        request: HttpRequest | None = None,
        mask: RelayAddress | DomainAddress,
        created_by_api: bool,
    ) -> None:
        from emails.models import RelayAddress

        if request is None:
            user_agent = ""
            ip_address = ""
        else:
            user_agent = request.headers.get("user-agent", "")
            client_ip, is_routable = get_client_ip(request)
            ip_address = client_ip if (client_ip and is_routable) else ""

        user = mask.user
        fxa_id = user.profile.fxa.uid if user.profile.fxa else ""
        n_random_masks = user.relayaddress_set.count()
        n_domain_masks = user.domainaddress_set.count()
        n_deleted_random_masks = user.profile.num_deleted_relay_addresses
        n_deleted_domain_masks = user.profile.num_deleted_domain_addresses
        date_joined_relay = int(user.date_joined.timestamp())

        date_subscribed = None
        if user.profile.has_premium:
            if user.profile.has_phone:
                date_subscribed = user.profile.date_subscribed_phone
            else:
                date_subscribed = user.profile.date_subscribed
        if date_subscribed:
            date_joined_premium = int(date_subscribed.timestamp())
        else:
            date_joined_premium = -1

        premium_status = user.profile.metrics_premium_status

        try:
            earliest_mask = user.relayaddress_set.exclude(
                generated_for__exact=""
            ).earliest("created_at")
        except RelayAddress.DoesNotExist:
            has_extension = False
            date_got_extension = -1
        else:
            has_extension = True
            date_got_extension = int(earliest_mask.created_at.timestamp())

        if isinstance(mask, RelayAddress):
            is_random_mask = True
            has_website = bool(mask.generated_for)
        else:
            is_random_mask = False
            has_website = False
        mask_id = mask.metrics_id

        self.record_email_mask_created(
            user_agent=user_agent,
            ip_address=ip_address,
            client_id="",
            fxa_id=fxa_id,
            platform="",
            n_random_masks=n_random_masks,
            n_domain_masks=n_domain_masks,
            n_deleted_random_masks=n_deleted_random_masks,
            n_deleted_domain_masks=n_deleted_domain_masks,
            date_joined_relay=date_joined_relay,
            premium_status=premium_status,
            date_joined_premium=date_joined_premium,
            has_extension=has_extension,
            date_got_extension=date_got_extension,
            mask_id=mask_id,
            is_random_mask=is_random_mask,
            created_by_api=created_by_api,
            has_website=has_website,
        )

    def log_email_mask_deleted(
        self,
        *,
        request: HttpRequest | None = None,
        user: User,
        mask_id: str,
        is_random_mask: bool
    ) -> None:
        from emails.models import RelayAddress

        if request is None:
            user_agent = ""
            ip_address = ""
        else:
            user_agent = request.headers.get("user-agent", "")
            client_ip, is_routable = get_client_ip(request)
            ip_address = client_ip if (client_ip and is_routable) else ""

        fxa_id = user.profile.fxa.uid if user.profile.fxa else ""
        n_random_masks = user.relayaddress_set.count()
        n_domain_masks = user.domainaddress_set.count()
        n_deleted_random_masks = user.profile.num_deleted_relay_addresses
        n_deleted_domain_masks = user.profile.num_deleted_domain_addresses
        date_joined_relay = int(user.date_joined.timestamp())

        date_subscribed = None
        if user.profile.has_premium:
            if user.profile.has_phone:
                date_subscribed = user.profile.date_subscribed_phone
            else:
                date_subscribed = user.profile.date_subscribed
        if date_subscribed:
            date_joined_premium = int(date_subscribed.timestamp())
        else:
            date_joined_premium = -1

        premium_status = user.profile.metrics_premium_status

        try:
            earliest_mask = user.relayaddress_set.exclude(
                generated_for__exact=""
            ).earliest("created_at")
        except RelayAddress.DoesNotExist:
            has_extension = False
            date_got_extension = -1
        else:
            has_extension = True
            date_got_extension = int(earliest_mask.created_at.timestamp())

        self.record_email_mask_deleted(
            user_agent=user_agent,
            ip_address=ip_address,
            client_id="",
            fxa_id=fxa_id,
            platform="",
            n_random_masks=n_random_masks,
            n_domain_masks=n_domain_masks,
            n_deleted_random_masks=n_deleted_random_masks,
            n_deleted_domain_masks=n_deleted_domain_masks,
            date_joined_relay=date_joined_relay,
            premium_status=premium_status,
            date_joined_premium=date_joined_premium,
            has_extension=has_extension,
            date_got_extension=date_got_extension,
            mask_id=mask_id,
            is_random_mask=is_random_mask,
        )

    def emit_record(self, now: datetime, ping: dict[str, Any]) -> None:
        """Emit record as a log instead of a print()"""
        self._logger.info(GLEAN_EVENT_MOZLOG_TYPE, extra=ping)
