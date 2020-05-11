import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.methods import uamethod

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')

    idx = 0

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)
    # Set MyVariable to be writable by clients

    await myvar.set_writable()
    _logger.info('Starting server!')
    async with server:
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 0.1
            _logger.info('Set value of %s to %.1f', myvar, count)
            await myvar.write_value(count)


if __name__ == '__main__':
    asyncio.run(main())
