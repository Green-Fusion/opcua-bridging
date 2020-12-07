import logging
import asyncio

from asyncua import ua, Server
from asyncua.ua import Variant, VariantType
from asyncua.common.methods import uamethod
from asyncua_utils.server import server_from_yaml
from asyncua.ua.uaerrors import BadInvalidArgument
from asyncua.server.users import UserRole
from asyncua.ua.status_codes import StatusCodes

from PLC.data_fetcher import TimeSeriesStorage

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')


def func(parent, variant: Variant):
    print("func method call with parameters: ", variant.Value)
    ret = False
    if not isinstance(variant.Value, int):
        return ua.StatusCode(StatusCodes.BadInvalidArgument)
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


async def main():
    server = await server_from_yaml('/server/PLC_server_config.yaml')

    idx = 0

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable('s=my_var', 'MyVariable', 6.7)

    # variables that should be able to be set by external client
    setobj = await server.nodes.objects.add_object(idx, 'Controlling')
    cntrl_1 = await setobj.add_variable('s=control_1', 'Control1', True)
    cntrl_2 = await setobj.add_variable('s=control_2', 'Control2', 'hello')
    cntrl_3 = await setobj.add_variable('s=control_3', 'Control3', 6)
    cntrl_4 = await setobj.add_method(idx, "mymethod", func, [ua.VariantType.Int64], [ua.VariantType.Boolean])

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
        while True:
            await asyncio.sleep(1)
            # old_val = await myvar.read_value()
            # count = old_val + 0.1
            # _logger.info('Set value of %s to %.1f', myvar, count)
            # await myvar.write_value(count)
            await ts_store.propagate()

if __name__ == '__main__':
    asyncio.run(main())
