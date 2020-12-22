from asyncua import Client, Server, ua
from asyncua_utils.bridge.node_mapping import DownstreamBridgeNodeMapping
from asyncua.common.events import Event
from asyncua_utils.node_utils import extract_node_id
import pprint as pp
import logging


class AlarmHandler:
    def __init__(self, downstream_client: Client, bridge_server: Server, node_mapping: DownstreamBridgeNodeMapping):
        self._client = downstream_client
        self._server = bridge_server
        self._node_mapping = node_mapping

    async def event_notification(self, event: Event):
        alarm_gen = await self._server.get_event_generator(event.EventType, emitting_node=ua.ObjectIds.Server)
        alarm_gen.event = event
        await alarm_gen.trigger()

