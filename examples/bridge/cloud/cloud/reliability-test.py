import logging
import asyncio
from asyncua_utils.server import server_from_yaml
from asyncua_utils.bridge.yaml import bridge_from_yaml
from asyncua_utils.bridge.bridge_object import Bridge
import time
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    bridge = await Bridge.from_yaml('cloud_server_config.yaml', '/appdata/test_yaml/reliability_test.yaml')
    async with bridge.server:
        while True:
            await asyncio.sleep(5)
            _logger.warning('happening')
            await bridge.maintain_connections()

if __name__ == '__main__':
    asyncio.run(main())
