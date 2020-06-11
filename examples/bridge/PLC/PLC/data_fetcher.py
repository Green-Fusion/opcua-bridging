import numpy as np


class FakeTimeSeries:
    def __init__(self, start=100, std=1.):
        self.current_value = start
        self.std = std

    async def get_value(self):
        self._propagate_value()
        return self.current_value

    def _propagate_value(self):
        self.current_value = self.current_value + np.random.randn() * self.std


class TimeSeriesStorage:
    def __init__(self):
        self._ts_list = []

    def assign_timeseries(self, variable):
        ts = FakeTimeSeries()
        self.add_timeseries(variable, ts)

    def add_timeseries(self, variable, timeseries):
        self._ts_list.append({
            'var': variable,
            'timeseries': timeseries
        })

    async def propagate(self):
        for ts_dict in self._ts_list:
            val = await ts_dict['timeseries'].get_value()
            await ts_dict['var'].set_value(val)