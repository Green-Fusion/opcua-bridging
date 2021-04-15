import logging
import asyncio
from asyncua_utils.server import server_from_yaml
from asyncua_utils.bridge.yaml import bridge_from_yaml
import sys

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    server = await server_from_yaml(sys.argv[1])
    await bridge_from_yaml(server, '/appdata/test_yaml/test.yaml')
    async with server:
        while True:
            _logger.warning('server is running')
            await asyncio.sleep(100)

if __name__ == '__main__':
    asyncio.run(main())
