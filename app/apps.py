import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AppAppConfig(AppConfig):
    name = "app"
    default_auto_field = "django.db.models.BigAutoField"

    logger_adapter = None
    cache = None

    def ready(self):
        from django.conf import settings

        from app.logging.cloudwatch_logger import CloudWatchLogger
        from app.logging.logger import AppLogger, ConsoleLogger
        from app.logging.loki_logger import LokiLogger
        from app.services.cache_service import CacheService

        env = os.getenv("DJANGO_SETTINGS_MODULE", "app.settings.development").split(".")[-1]

        loggers = [ConsoleLogger(debug=getattr(settings, "DEBUG", False))]

        if getattr(settings, "SENTRY_DSN", None):
            from app.logging.sentry_logger import SentryLogger

            loggers.append(SentryLogger(dsn=settings.SENTRY_DSN, environment=env))

        if getattr(settings, "CLOUDWATCH_LOG_GROUP", None):
            try:
                loggers.append(
                    CloudWatchLogger(
                        log_group=settings.CLOUDWATCH_LOG_GROUP,
                        stream_name=settings.CLOUDWATCH_STREAM_NAME,
                        region=settings.AWS_DEFAULT_REGION,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        endpoint_url=settings.CLOUDWATCH_ENDPOINT_URL,
                    )
                )
            except Exception as e:
                logger.warning("CloudWatch logger unavailable, skipping: %s", e)

        if getattr(settings, "LOKI_URL", None):
            loggers.append(
                LokiLogger(
                    url=settings.LOKI_URL,
                    labels={"app": "django-boilerplate", "env": env},
                )
            )

        AppAppConfig.logger_adapter = AppLogger(*loggers)
        AppAppConfig.cache = (
            CacheService.from_url(settings.REDIS_URL) if getattr(settings, "REDIS_URL", None) else None
        )
