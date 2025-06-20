import tortoise


AERICH_CONFIG = {
    "connections": {"default": "sqlite://data/db.sqlite3"},
    "apps": {
        "models": {
            "models": [
                "src.persistence.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
    "tortoise": {
        "use_tz": False,
        "timezone": "UTC",
    },
}


async def init_db(
    db_url: str,
    models: list[str],
) -> None:
    config = {
        "connections": {
            "default": db_url,
        },
        "apps": {
            "models": {
                "models": [
                    *models,
                ],
                "default_connection": "default",
            },
        },
    }

    await tortoise.Tortoise.init(config=config)
    await tortoise.Tortoise.generate_schemas(safe=True)
