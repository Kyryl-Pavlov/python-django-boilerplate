from django.apps import apps
from graphene_file_upload.django import FileUploadGraphQLView


class CustomGraphQLView(FileUploadGraphQLView):
    def get_context(self, request):
        app_config = apps.get_app_config("app")
        return {
            "request": request,
            "cache": app_config.cache,
            "logger": app_config.logger_adapter,
        }
