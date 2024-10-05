from tortoise import Tortoise

async def connectToDatabase():
    await Tortoise.init(
        db_url='postgres://bobcoingame:@TYDev@2024@POST@postgresql-bobcoingame.alwaysdata.net:5432/bobcoingame_db2',
        modules={'models': ['models']}
    )

# postgres://bobcoingame:@TYDev@2024@POST@postgresql-bobcoingame.alwaysdata.net:5432/bobcoingame_bob