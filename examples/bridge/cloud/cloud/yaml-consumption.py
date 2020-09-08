import logging
import asyncio
from asyncua_utils.server import server_from_yaml
from asyncua_utils.bridge.yaml import bridge_from_yaml

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    server = await server_from_yaml('cloud_server_config.yaml')
    await bridge_from_yaml(server, '/appdata/test_yaml/test.yaml')
    async with server:
        while True:
            await asyncio.sleep(100)

if __name__ == '__main__':
    asyncio.run(main())
