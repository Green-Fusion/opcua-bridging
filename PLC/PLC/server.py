import logging
import asyncio

from asyncua import ua, Server
from asyncua.common.methods import uamethod
from asyncua.crypto.certificate_handler import CertificateHandler
from asyncua.server.user_managers import CertificateUserManager
from asyncua.server.users import UserRole

from PLC.data_fetcher import TimeSeriesStorage

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


async def main():
    # setup our server
    cert_handler = CertificateHandler()
    await cert_handler.trust_certificate("/credentials/cloud_cert.der",
                                         user_role=UserRole.Admin, label='cloud')
    await cert_handler.trust_certificate("/credentials/user_admin_cert.der",
                                         user_role=UserRole.User, label='end_client')

    server = Server(user_manager=CertificateUserManager(cert_handler))
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
                               certificate_handler=cert_handler)

    await server.load_certificate("/credentials/PLC_cert.der")
    await server.load_private_key("/credentials/PLC_private_key.pem")

    idx = 0

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)
    # Set MyVariable to be writable by clients

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
