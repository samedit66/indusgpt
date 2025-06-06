import tortoise


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
                    # "aerich.models" # include aerich.models if you add migrations later
                ],
                "default_connection": "default",
            },
        },
    }

    await tortoise.Tortoise.init(config=config)
    await tortoise.Tortoise.generate_schemas(safe=True)
