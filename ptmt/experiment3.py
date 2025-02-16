import csv
import pprint
from typing import Callable

from ptmt.experiment2 import create_run
from ptmt.experiment2_support.functions import *
from ptmt.research.dirs import DataDirectory
from ptmt.research.plotting.plot_data import PlotData
from ptmt.research.protocols import TranslationConfig
from ptmt.research.tmt1.pipeline import NDCGKwArgs
from ptmt.research.tmt1.run import run, RunKwargs

statistical_data = list()
ct = set()
for i, hvn in enumerate(itertools.chain(
        [(None, None, None)],
        create_all_configs()
)):

    horizontal, vertical, ngram = hvn
    info, cfg = create_run(
        "v3",
        "experiment6",
        "dictionary_20241130_proc3",
        "../data/ngrams/counts_with_proc.bin",
        horizontal=horizontal,
        vertical=vertical,
        ngram=ngram,
        clean_translations=True,
        # configs=short_configs,
        shared_dir=f"../data/experiment3/shared"
    )

    ct.add(info['name'])

    data = DataDirectory(Path(cfg['target_folder']) / info['name'] / 'paper_filtered_dic')

    if not data.is_finished():
        continue

    ndcg_kwargs = { "top_n_weigts": (3, 2, 1) }

    if ndcg_kwargs is None:
        ndcg_kwargs: NDCGKwArgs = NDCGKwArgs()
    ndcg_kwargs.setdefault("top_n_weigts", (1, 1, 1))
    ndcg_kwargs.setdefault("save", False)
    ndcg_kwargs.setdefault("ignore_existing_file", True)

    print(info['name'])
    for translation in data.iter_all_translations():
        translation.calculate_ndcg_for(**ndcg_kwargs)

    to_plot = PlotData(data, 3, mark_baselines=True)

    statistical_data_entry: dict[str, float | None] = dict()
    statistical_data_entry['name'] = info['name']
    names = [x.name for value in to_plot.convolution_ndcg.values() for x in value]
    for name in sorted(names):
        statistical_data_entry[name] = None
    for avg_ndcg, plots in to_plot.convolution_ndcg.items():
        for plot in plots:
            statistical_data_entry[plot.name] = avg_ndcg
    statistical_data.append(statistical_data_entry)

with open("statistical_data.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, statistical_data[0].keys())
    writer.writeheader()
    writer.writerows(statistical_data)

# pprint.pprint(ct)
# print((len(ct) - 1)/3)
