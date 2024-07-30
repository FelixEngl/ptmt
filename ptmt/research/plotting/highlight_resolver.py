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
