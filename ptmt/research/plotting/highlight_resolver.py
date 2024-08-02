# Copyright 2024 Felix Engl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import typing

from ptmt.research.plotting.plot_data import PlotDataEntry


def resolve_highlight_to_idx(plot_data: list[PlotDataEntry], highlight: typing.Iterable[str | int]) -> list[int]:
    plot_data = list(enumerate(plot_data))
    result = []
    for h in highlight:
        if isinstance(h, int):
            result.append(h)
        else:
            result.append(next(filter(lambda x: x[1].name == h, plot_data))[0])
    return result


def resolve_highlight(plot_data: list[PlotDataEntry], highlight: typing.Iterable[str | int]) -> list[str]:
    result = []
    for h in highlight:
        if isinstance(h, str):
            result.append(h)
        else:
            result.append(plot_data[h].name)
    return result
