from asyncua_utils.server import server_from_yaml
import logging
import asyncio
from PLC.server import make_test_server

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def one_server(time_period):
    try:
        server, ts_store, _ = await make_test_server()

        _logger.info('Starting server!')
        async with server:
            # while True:
            await asyncio.sleep(time_period)
            await ts_store.propagate()
        raise TypeError  # non-zero exit code
    except TypeError:
        await asyncio.sleep(3)
        _logger.warning('server exited and starting again')


async def main():
    await one_server(5)
    while True:
        await one_server(30)


if __name__ == '__main__':
    asyncio.run(main())
