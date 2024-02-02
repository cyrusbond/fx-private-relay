"""Relay interface to EventsServerEventLogger generated by glean_parser."""

from datetime import datetime
from logging import getLogger
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest

from ipware import get_client_ip


from .glean.server_events import EventsServerEventLogger, GLEAN_EVENT_MOZLOG_TYPE
from .types import RELAY_CHANNEL_NAME


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

    def mask_created(
        self,
        *,
        request: HttpRequest | None = None,
        user: User | None = None,
        is_random_mask: bool,
        has_website: bool,
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
            if user is None and isinstance(request.user, User):
                user = request.user

        if user is None:
            fxa_id = ""
            n_masks = 0
            date_joined_relay = -1
            premium_status = ""
            date_joined_premium = -1
            has_extension = False
            date_got_extension = -1
        else:
            fxa_id = user.profile.fxa.uid if user.profile.fxa else ""
            n_masks = user.profile.total_masks
            date_joined_relay = int(user.date_joined.timestamp())

            date_subscribed = None
            if user.profile.has_premium:
                if user.profile.has_phone:
                    plan = "bundle" if user.profile.has_vpn else "phone"
                    date_subscribed = user.profile.date_subscribed_phone
                else:
                    plan = "email"
                    date_subscribed = user.profile.date_subscribed
            else:
                plan = "free"
            if date_subscribed:
                date_joined_premium = int(date_subscribed.timestamp())
            else:
                date_joined_premium = -1

            term = "unknown"
            if plan == "phone":
                start_date = user.profile.date_phone_subscription_start
                end_date = user.profile.date_phone_subscription_end
                if start_date and end_date:
                    span = end_date - start_date
                    term = "1_year" if span.days > 32 else "1_month"
            premium_status = plan if plan == "free" else f"{plan}_{term}"

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

        self.record_mask_created(
            user_agent=user_agent,
            ip_address=ip_address,
            user_id="",
            fxa_id=fxa_id,
            platform="",
            n_masks=n_masks,
            date_joined_relay=date_joined_relay,
            premium_status=premium_status,
            date_joined_premium=date_joined_premium,
            has_extension=has_extension,
            date_got_extension=date_got_extension,
            is_random_mask=is_random_mask,
            created_by_api=created_by_api,
            has_website=has_website,
        )

    def emit_record(self, now: datetime, ping: dict[str, Any]) -> None:
        """Emit record as a log instead of a print()"""
        self._logger.info(GLEAN_EVENT_MOZLOG_TYPE, extra=ping)
