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

import dataclasses
import math
import typing
from collections import defaultdict
from typing import Callable

import adjustText as adjust_text
import cycler
import matplotlib
import more_itertools
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.pyplot import colormaps
from matplotlib.text import Annotation
from matplotlib.transforms import Bbox, Transform

from ptmt.research.helpers.fonts import FontSizes
from ptmt.research.plotting.highlight_resolver import resolve_highlight
from ptmt.research.plotting.plot_data import PlotData

# https://matplotlib.org/stable/users/explain/colors/colors.html
_MPLColors = str | float | tuple[float, float, float] | tuple[float, float, float, float] | cycler.Cycler[str, str]
MPLColor = _MPLColors | tuple[_MPLColors, float]


@dataclasses.dataclass
class TitlesAndLabels:
    complete_x_label: str
    bar_x_label: str
    line_x_label: str




def _render_bar_only(
        ax: Axes,
        n: int,
        names: list[str],
        top_n_eq: list[np.ndarray[typing.Any, np.dtype[int]]],
        width: float,
        highlight: list[str] | None,
        linewidth: float,
        edgecolor: None | str,
        font_sizes: FontSizes,
        y_label_rotation: str | float | None = None,
        y_label_labelpad: float = 0
):
    kept = set()
    bottom = np.zeros(len(names))
    for i, v in enumerate(top_n_eq):
        p: BarContainer = ax.bar(
            names,
            v,
            width,
            label=f'#{i}',
            bottom=bottom,
            edgecolor=edgecolor,
            linewidth=linewidth
        )
        bottom += v

        if highlight is not None:
            idxs = [names.index(h) for h in highlight]
            for idx in range(len(p)):
                if idx not in idxs:
                    bar: Rectangle = p[idx]
                    bar.set_alpha(0.5)
                else:
                    kept.add((names[idx], idx))

    y_label_rotation = 90 if y_label_rotation is None else y_label_rotation

    ax.set_ylabel('Number of aligned documents', fontsize=font_sizes.y_label_left, rotation=y_label_rotation, labelpad=y_label_labelpad)

    legend = ax.legend(loc="center left", ncols=4, title=f'Number of same top-{n} topics in original and translated',
                       reverse=True, fontsize=font_sizes.legend_font)

    if font_sizes.legend_title is not None:
        legend.get_title().set_fontsize(font_sizes.legend_title)


def _render_line_only(ax: Axes,
                      plot_data: PlotData,
                      font_sizes: FontSizes,
                      is_right: bool,
                      y_label_rotation: str | float | None = None,
                      y_label_labelpad: float = 0):
    ax = ax if not is_right else ax.twinx()
    ticks = ax.get_xticks()
    if ticks is None or len(ticks) < len(plot_data.ranking_sorted):
        ticks = list(range(0, len(plot_data.ranking_sorted)))
    sorted = [y.ndcg_avg for y in plot_data.ranking_sorted]
    ax.plot(
        ticks,
        sorted,
        linewidth=2.0,
        color='black',
    )
    ax.set_ylim(math.floor(min(sorted) * 10) / 10,
                math.ceil(max(sorted) * 10) / 10)
    y_label_rotation = 90 if y_label_rotation is None else y_label_rotation
    ax.set_ylabel(f'Average value of NDCG@{plot_data.ndcg_at}', fontsize=font_sizes.y_label_right, rotation=y_label_rotation, labelpad=y_label_labelpad)
    _configure_y_labels(ax, font_sizes)


def _render_x_labels(
        ax: Axes,
        id_rows: int,
        id_row_boost: float,
        id_row_delta: float,
        font_sizes: FontSizes,
        titles_and_labels: TitlesAndLabels,
        label_rotation: str | float = 'vertical',
        vertical_alignment: typing.Literal["bottom", "baseline", "center", "center_baseline", "top"] = 'bottom',
        horizontal_alignment: typing.Literal["left", "center", "right"] = 'center',
        delta_x: float | None = None,
        label_colors: dict[str, MPLColor] | Callable[[str], MPLColor | None] | None = None,
):
    labels: list[plt.Text] = ax.get_xticklabels()

    for i, lab in enumerate(labels):
        mad = id_rows - i % id_rows - 1
        lab: plt.Text
        lab.set_fontsize(font_sizes.x_ticks_bottom)
        x, y = lab.get_position()
        lab.set_rotation(label_rotation)
        lab.set_y(y - id_row_boost * mad + id_row_delta)
        if delta_x is not None:
            lab.set_x(x + delta_x)
        lab.set_verticalalignment(vertical_alignment)
        lab.set_horizontalalignment(horizontal_alignment)
        if label_colors is not None:
            if callable(label_colors):
                color = label_colors(lab.get_text())
            else:
                color = label_colors.get(lab.get_text(), None)
            if color is not None:
                lab.set_color(color)

    ax.set_xmargin(0.01)
    ax.set_xlabel(titles_and_labels.complete_x_label, fontsize=font_sizes.x_label_bottom)


def _configure_y_labels(ax: Axes, font_sizes: FontSizes, ):
    labels = ax.get_yticklabels()
    for lab in labels:
        lab.set_fontsize(font_sizes.y_ticks_left)


def _set_x_as_rank(ax: Axes, plot_data: PlotData, number_of_ndcg_value_ticks: int, font_sizes: FontSizes):
    left, right = ax.get_xlim()
    ticks = ax.get_xticks()
    if ticks is None or len(ticks) < len(plot_data.ranking_sorted):
        ticks = list(range(0, len(plot_data.ranking_sorted)))

    new_tick_positions = [int(((left + right) / (number_of_ndcg_value_ticks - 1)) * z) for z in
                          range(0, number_of_ndcg_value_ticks)]

    new_tick_values = [x - ticks[0] for x in new_tick_positions]

    ax.set_xlim(
        left, right
    )

    ax.set_xticks(
        new_tick_positions,
        [f'{a + 1}' for a in new_tick_values]
    )

    labels = ax.get_xticklabels()
    for lab in labels:
        lab.set_fontsize(font_sizes.x_ticks_bottom)


def _render_top_labels(ax: Axes, plot_data: PlotData, number_of_ndcg_value_ticks: int, font_sizes: FontSizes):
    ax2 = ax.secondary_xaxis('top')

    left, right = ax.get_xlim()
    ticks = ax.get_xticks()

    sorted = [dat.ndcg_avg for dat in plot_data.ranking_sorted]

    if ticks is None or len(ticks) < len(sorted):
        ticks = list(range(0, len(sorted)))

    new_tick_positions = [int(((left + right) / (number_of_ndcg_value_ticks - 1)) * z) for z in
                          range(0, number_of_ndcg_value_ticks)]

    new_tick_values = [(x - ticks[0], sorted[x - ticks[0]]) for x in new_tick_positions]

    ax2.set_xlim(
        left, right
    )

    ax2.set_xticks(
        new_tick_positions,
        [f'{b:1.3f}@{a + 1}' for a, b in new_tick_values]
    )

    labels = ax2.get_xticklabels()
    for lab in labels:
        lab.set_fontsize(font_sizes.x_ticks_top)

    ax2.set_xlabel(
        f'Average NDCG@{plot_data.ndcg_at} at rank X',
        fontsize=font_sizes.x_label_top
    )


def _render_bar_plot_to(
        ax: Axes,
        plot_data: PlotData,
        names: list[str],
        top_n_eq: list[np.ndarray[typing.Any, np.dtype[int]]],
        n: int,
        width: float,
        highlight: list[str] | None,
        id_rows: int,
        id_row_boost: float,
        id_row_delta: float,
        linewidth: float,
        edgecolor: None | str,
        number_of_ndcg_value_ticks: int,
        font_sizes: FontSizes,
        titles_and_labels: TitlesAndLabels,
        label_rotation: str | float = 'vertical',
        y_label_rotation: str | float | None = None,
        y_label_labelpad: float = 0,
        vertical_alignment: typing.Literal["bottom", "baseline", "center", "center_baseline", "top"] = 'bottom',
        horizontal_alignment: typing.Literal["left", "center", "right"] = 'center',
        delta_x: float | None = None,
        label_colors: dict[str, MPLColor] | Callable[[str], MPLColor | None] | None = None,
) -> Axes:
    _render_bar_only(
        ax,
        n,
        names,
        top_n_eq,
        width,
        highlight,
        linewidth,
        edgecolor,
        font_sizes,
        y_label_rotation,
        y_label_labelpad
    )

    _render_line_only(ax, plot_data, font_sizes, True, y_label_rotation, y_label_labelpad)

    _render_x_labels(ax, id_rows, id_row_boost, id_row_delta, font_sizes, titles_and_labels, label_rotation, vertical_alignment, horizontal_alignment, delta_x, label_colors)
    _configure_y_labels(ax, font_sizes)

    _render_top_labels(ax, plot_data, number_of_ndcg_value_ticks, font_sizes)

    return ax


def render_bar_plot(
        plot_data: PlotData,
        highlight: typing.Iterable[str | int],
        width: float = 0.5,
        fig: Figure | None = None,
        fig_width: float = 20.0,
        id_rows: int = 3,
        id_row_boost: float = 0.09,
        id_row_delta: float = 0.0,
        linewidth: float = 0,
        edgecolor: None | str = None,
        number_of_ndcg_value_ticks: int = 5,
        font_sizes: FontSizes | None = None,
        titles_and_labels: TitlesAndLabels | None = None,
        show_buildup: bool = False,
        label_rotation: str | float | None = None,
        y_label_rotation: str | float | None = None,
        y_label_labelpad: float = 0.0,
        vertical_alignment: typing.Literal["bottom", "baseline", "center", "center_baseline", "top"] = 'bottom',
        horizontal_alignment: typing.Literal["left", "center", "right"] = 'center',
        delta_x: float | None = None,
        label_colors: dict[str, MPLColor] | Callable[[str], MPLColor | None] | None = None
) -> tuple[Figure, Axes | list[Axes]]:
    """Renders the bar plot for the PlotData, highlighting the highlights"""

    if label_rotation is None:
        label_rotation = 'vertical'

    if font_sizes is None:
        font_sizes = FontSizes()

    highlight = resolve_highlight(plot_data.ranking_sorted, highlight)
    names, top_n_eq = plot_data.names_and_top_n_sorted

    titles_and_labels = titles_and_labels if titles_and_labels is not None else TitlesAndLabels(
        "Translated Model ID",
        f"Translated Model ID (sorted by NDCG@{plot_data.ndcg_at})",
        "Rank of translated model"
    )
    ax: list[Axes] | Axes
    if show_buildup:
        if fig is None:
            fig, ax = plt.subplots(nrows=3, layout="constrained")
        else:
            ax = fig.subplots(nrows=3)

        size = fig.get_size_inches().tolist()

        fig.set_size_inches(
            size[0],
            size[1] * 3.2,
            forward=True
        )
        # noinspection PyArgumentList
        fig.get_layout_engine().set(hspace=0.1)

        for a in ax:
            a.set_xmargin(0.01)

        line_ax: Axes | None
        bar_ax: Axes
        complete_ax: Axes

        line_ax = ax[0]
        bar_ax = ax[1]
        complete_ax = ax[2]

        _render_line_only(line_ax, plot_data, font_sizes, False, y_label_rotation)
        _configure_y_labels(line_ax, font_sizes)
        _render_top_labels(line_ax, plot_data, number_of_ndcg_value_ticks, font_sizes)
        _set_x_as_rank(line_ax, plot_data, number_of_ndcg_value_ticks, font_sizes)
        line_ax.set_xlabel(titles_and_labels.line_x_label, fontsize=font_sizes.x_label_bottom)

        _render_bar_only(
            bar_ax,
            plot_data.n_relevant,
            names,
            top_n_eq,
            width,
            highlight,
            linewidth,
            edgecolor,
            font_sizes,
            y_label_rotation,
            y_label_labelpad
        )
        _configure_y_labels(bar_ax, font_sizes)
        bar_ax.get_xaxis().set_ticklabels([])
        bar_ax.set_xlabel(titles_and_labels.bar_x_label, fontsize=font_sizes.x_label_bottom)

        _render_bar_plot_to(complete_ax, plot_data, names, top_n_eq, plot_data.n_relevant, width, highlight, id_rows,
                            id_row_boost,
                            id_row_delta, linewidth, edgecolor, number_of_ndcg_value_ticks, font_sizes,
                            titles_and_labels, label_rotation, y_label_rotation, y_label_labelpad,
            vertical_alignment,
            horizontal_alignment, delta_x, label_colors)
    else:
        if fig is None:
            fig, ax = plt.subplots(layout="constrained")
        else:
            ax = fig.subplots()

        ax.set_xmargin(0.01)
        ax = _render_bar_plot_to(ax, plot_data, names, top_n_eq, plot_data.n_relevant, width, highlight, id_rows,
                                 id_row_boost,
                                 id_row_delta, linewidth, edgecolor, number_of_ndcg_value_ticks, font_sizes,
                                 titles_and_labels, label_rotation, y_label_rotation, y_label_labelpad,
                                 vertical_alignment, horizontal_alignment, delta_x, label_colors)

    fig.set_figwidth(fig_width)
    return fig, ax


def get_midpoint(bbox):
    cx = (bbox.x0 + bbox.x1) / 2
    cy = (bbox.y0 + bbox.y1) / 2
    return cx, cy

def render_x_bars(
        plot_data: PlotData,
        targets: typing.Iterable[str | int],
        fig: Figure | None = None,
        colors: matplotlib.colors.ListedColormap | matplotlib.colors.LinearSegmentedColormap | None = None,
        fig_args: dict[str, typing.Any] | None = None,
) -> tuple[Figure, Axes, tuple[str, ...], dict[str, list[tuple[str, float, str, int]]]]:
    """Renders the detailed information about the targets in the plot data"""
    lst = plot_data.ranking_sorted
    targets = resolve_highlight(lst, targets)

    if colors is None:
        colors = colormaps.get("tab20")

    extracted = dict()

    targs = []

    all_keys = set()

    for x in lst:
        all_keys.update(x.convolution.keys())

    sorted_keys = sorted(all_keys)

    for i, v in enumerate(lst):
        if v.name in targets:
            sorted_docs = defaultdict(list, v.convolution)
            len_map = {k: len(sorted_docs[k]) for k in sorted_keys}
            # len_map = {k: len(v) for k, v in sorted_docs.items()}
            extracted[v.name] = (i + 1, (v.name, v.ndcg_avg, len_map))
            targs.append((i + 1, (v.name, v.ndcg_avg, len_map)))

    ax: Axes
    if fig is None:
        fig, ax = plt.subplots(**fig_args)
    else:
        ax = fig.subplots()


    def convert_to_list(extr: tuple[int, tuple[str, float, dict[float, int]]]) -> tuple[
        str, float, list[str], list[int]]:
        a = []
        b = []
        for k, v in sorted(extr[1][2].items(), key=lambda x: x[0], reverse=False):
            a.append(f'{k:0.2f}')
            b.append(v)
        # noinspection PyTypeChecker
        return extr[1][0:2] + (a, b)

    values: defaultdict[str, list[int]] = defaultdict(list)
    values_ret: defaultdict[str, list[tuple[str, float, str, int]]] = defaultdict(list)

    for value in targs:
        value = convert_to_list(value)
        for (a, b) in zip(value[2], value[3]):
            values[a].append(b)
            values_ret[a].append((value[0], value[1], a, b))

    names = tuple(f'{t[1][0]}\n(Rank {t[0]})\n(\u03bc={t[1][1]:1.3f})' for t in targs)

    #    names = (
    #        f'{best[1][0].short_str}\n(Rank {best[0]})',
    #        f'{second[1][0].short_str}\n(Rank {second[0]})',
    #        f'{middle[1][0].short_str}\n(Rank {middle[0]})',
    #        f'{last[1][0].short_str}\n(Rank {last[0]})',
    #    )

    if isinstance(colors, matplotlib.colors.LinearSegmentedColormap):
        colors = colors.resampled(len(values))
        colors = [colors(x) for x in range(len(values))]
    elif len(colors.colors) < len(values):
        colors = colors.resampled(len(values))
        colors = colors.colors[:len(values)]
    else:
        colors = colors.colors[:len(values)]

    bar_values: list[tuple[tuple[str, list[int]], typing.Any]] = list(zip(values.items(), colors))

    bottom = np.zeros(len(targets))

    annotations: defaultdict[str, list[tuple[Annotation, int, Rectangle, typing.Any]]] = defaultdict(list)

    bars_col = []

    ax.text(0.5, 1.5, " ")

    for (k, v), color in bar_values:
        bars: BarContainer = ax.bar(names, v, 0.5, label=k, bottom=bottom, color=color)
        bars_col.append(bars)
        bottom += v
        ann = ax.bar_label(bars, label_type="center")
        for (name, bar, a, x) in zip(names, bars, ann, v):
            annotations[name].append((a, x, bar, color))

    ax.spines[['right', 'top']].set_visible(False)

    # annotations: dict[str, np.ndarray] = {name: np.array(ls) for (name, ls) in annotations.items()}

    # Shrink current axis by 10%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

    handles, labels = ax.get_legend_handles_labels()

    ax.legend(
        handles[::-1],
        labels[::-1],
        bbox_to_anchor=(1.25, 0.5),
        loc='right',
        borderaxespad=0.,
        title='NDCG@3',
        ncol=max(math.ceil(len(labels[::-1]) / 15), 1),
    )

    r: RendererBase = adjust_text.get_renderer(ax.get_figure())

    extended_annotations: list[list[tuple[Annotation, int, Rectangle, typing.Any, Bbox]]] = []

    for x in annotations.values():
        e_annotations: list[tuple[Annotation, int, Rectangle, typing.Any, Bbox]] = []
        for v in x:
            (ann, val, rec, color) = tuple(v)
            bb_rec = rec.get_window_extent(r)
            e_annotations.append((ann, val, rec, color, bb_rec))
        extended_annotations.append(e_annotations)

    extended_annotations_with_spaces: list[list[tuple[Annotation, int, Rectangle, typing.Any, Bbox, float]]] = []

    av = 0.
    ct = 0

    for a, b in more_itertools.pairwise(extended_annotations):
        e_annotations: list[tuple[Annotation, int, Rectangle, typing.Any, Bbox, float]] = []
        for ai, bi in zip(a, b):
            ai: tuple[Annotation, int, Rectangle, typing.Any, Bbox]
            bi: tuple[Annotation, int, Rectangle, typing.Any, Bbox]
            value = bi[4].x0 - ai[4].x1
            av += value
            e_annotations.append(ai + (value, ))
            ct += 1
        extended_annotations_with_spaces.append(e_annotations)

    extended_annotations_with_spaces.append([v + ((av/ct), ) for v in extended_annotations[-1]])
    arrow_commands = []
    for annotation_collection in extended_annotations_with_spaces:

        arrow_command: list[tuple[int, tuple[float, float], tuple[float, float], Bbox, Transform, Transform, typing.Any]] = []
        arrow_commands.append(arrow_command)
        last_moved: Bbox | None = None
        for i, aa_values in enumerate(annotation_collection):
            ann: Annotation
            val: int
            rec: Rectangle
            colors: typing.Any
            bbox: Bbox
            d_add_global: float
            ann, val, rec, color, bb_rec, d_add_global = aa_values

            bb_ann_original = ann.get_window_extent(r)
            local_ann_to_global_render = ann.get_transform()
            global_render_to_local_ann = local_ann_to_global_render.inverted()
            global_pos = local_ann_to_global_render.transform(ann.get_position())

            if bb_ann_original.y0 < bb_rec.y0 or bb_rec.y1 < bb_ann_original.y1:
                new_pos = global_pos[0] + d_add_global, global_pos[1]
                ann.set_position(tuple(global_render_to_local_ann.transform(new_pos)))
                annotation_bb: Bbox = ann.get_window_extent(r)

                if last_moved is None:
                    if bb_rec.y0 > annotation_bb.y0:
                        new_pos = new_pos[0], new_pos[1] + abs(annotation_bb.y0 - bb_rec.y0)
                        ann.set_position(tuple(global_render_to_local_ann.transform(new_pos)))
                        annotation_bb: Bbox = ann.get_window_extent(r)
                else:
                    if annotation_bb.y0 <= last_moved.y1:
                        new_pos = new_pos[0], new_pos[1] + abs(annotation_bb.y0 - last_moved.y1) + 0.1
                        ann.set_position(tuple(global_render_to_local_ann.transform(new_pos)))
                        annotation_bb: Bbox = ann.get_window_extent(r)

                last_moved = annotation_bb

                xy = (bb_rec.x1, bb_rec.y1 - (bb_rec.y1 - bb_rec.y0)/2)
                xytext = new_pos[0] - (annotation_bb.x1 - annotation_bb.x0)/2, new_pos[1]

                # noinspection PyTypeChecker
                arrow_command.append(
                    (
                        i,
                        tuple(xy),
                        tuple(xytext),
                        annotation_bb,
                        local_ann_to_global_render,
                        global_render_to_local_ann,
                        color
                    )
                )

    for arrows in arrow_commands:
        it = iter(arrows)
        current: list[tuple[int, tuple[float, float], tuple[float, float], Bbox, Transform, Transform, typing.Any]] = []
        while True:
            try:
                v = next(it)
            except StopIteration:
                v = None

            if v is not None:
                if len(current) == 0:
                    current.append(v)
                    continue
                if current[-1][0] + 1 == v[0]:
                    current.append(v)
                    continue
            if len(current) == 1:
                pos, xy, xytext, _, local_ann_to_global_render, global_render_to_local_ann, color = current[0]
                # noinspection PyTypeChecker
                ax.annotate(
                    "",
                    xy=global_render_to_local_ann.transform(xy),
                    xytext=global_render_to_local_ann.transform(xytext),
                    arrowprops=dict(arrowstyle="->,head_length=0.5, head_width=0.25, widthA=1.5, widthB=1.5",
                                    color="black"),
                    xycoords=local_ann_to_global_render,
                    textcoords=local_ann_to_global_render,
                )
                current = []
            elif len(current) > 1:
                (best_text_x, biggest_text_y, smallest_text_y,
                 best_x, biggest_y, smallest_y) = (
                    math.inf, -math.inf, math.inf,
                    -math.inf, -math.inf, math.inf
                )

                for pos, xy, xytext, bbox, local_ann_to_global_render, global_render_to_local_ann, color in current:
                    best_text_x = min(best_text_x, xytext[0])
                    biggest_text_y = max(biggest_text_y, xytext[1], bbox.y0, bbox.y1)
                    smallest_text_y = min(smallest_text_y, xytext[1], bbox.y0, bbox.y1)
                    best_x = max(best_x, xy[0])
                    biggest_y = max(biggest_y, xy[1])
                    smallest_y = min(smallest_y, xy[1])

                # x = links rechts
                # y = hoch runter
                # xy = (min(xy_b[0], xy[0]), (xy_b[1] + xy[1])/2)
                # xytext = (min(xytext_b[0], xytext[0]), (xytext_b[1] + xytext[1])/2)

                best_text_x -= 2.5

                # noinspection PyUnboundLocalVariable
                # noinspection PyTypeChecker
                ax.annotate(
                    "",
                    xy=global_render_to_local_ann.transform((best_text_x, biggest_text_y)),
                    xytext=global_render_to_local_ann.transform((best_text_x, smallest_text_y)),
                    arrowprops=dict(arrowstyle="-",
                                    color="black"),
                    xycoords=local_ann_to_global_render,
                    textcoords=local_ann_to_global_render,
                )
                # noinspection PyTypeChecker
                ax.annotate(
                    "",
                    xy=global_render_to_local_ann.transform((best_x, (biggest_y + smallest_y) / 2)),
                    xytext=global_render_to_local_ann.transform((best_text_x, (biggest_text_y + smallest_text_y)/2)),
                    arrowprops=dict(arrowstyle="-",
                                    color="black"),
                    xycoords=local_ann_to_global_render,
                    textcoords=local_ann_to_global_render,
                )
                current = []
            if v is None:
                break
            current.append(v)

    return fig, ax, names, dict(values_ret)
