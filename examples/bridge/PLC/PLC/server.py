import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.methods import uamethod
from asyncua_utils.server import server_from_yaml
from asyncua.server.users import UserRole

from PLC.data_fetcher import TimeSeriesStorage

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    server = await server_from_yaml('/server/PLC_server_config.yaml')

    idx = 0

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)

    # variables that should be able to be set by external client
    setobj = await server.nodes.objects.add_object(idx, 'Controlling')
    cntrl_1 = await setobj.add_variable(idx, 'Control1', True)
    cntrl_2 = await setobj.add_variable(idx, 'Control2', 'hello')
    cntrl_3 = await setobj.add_variable(idx, 'Control3', 6)

    ts_store = TimeSeriesStorage()
    tsobj = await server.nodes.objects.add_object(idx, 'TimeSeries')
    for jdx in range(5):
        ts = await tsobj.add_variable(idx, f'TimeSeries{jdx}', 0)
        ts_store.assign_timeseries(ts)

    await myvar.set_writable()
    await cntrl_1.set_writable()
    await cntrl_2.set_writable()
    await cntrl_3.set_writable()

    await ts_store.propagate()

    _logger.info('Starting server!')
    async with server:
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 0.1
            _logger.info('Set value of %s to %.1f', myvar, count)
            await myvar.write_value(count)
            await ts_store.propagate()

if __name__ == '__main__':
    asyncio.run(main())
