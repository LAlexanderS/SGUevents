import os
from datetime import datetime


def define_env(env):
    """
    Hook for mkdocs-macros-plugin.

    Provides env variables and helper filters for templates/markdown.
    """

    env.variables["SITE_DOMAIN"] = os.getenv("SITE_DOMAIN", "https://sguevents.ru")
    env.variables["TG_BOT_URL"] = os.getenv("TG_BOT_URL", "https://t.me/EventsSGUbot")
    env.variables["SUPPORT_EMAIL"] = os.getenv("SUPPORT_EMAIL", "support@sguevents.ru")
    env.variables["CURRENT_YEAR"] = datetime.utcnow().year

    @env.macro
    def hero(title: str, subtitle: str = ""):
        """Reusable hero section snippet."""
        return f"> **{title}**\n>\n> {subtitle}" if subtitle else f"> **{title}**"

