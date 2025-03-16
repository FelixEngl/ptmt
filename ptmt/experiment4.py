import pickle
import random
from pygad import pygad

from ptmt.experiment2 import create_run
from ptmt.genetic import gene_manager, Gene
from ptmt.genetic.watcher import GenesWatcher
from ptmt.research.plotting.plot_data import PlotData
from ptmt.research.tmt1.pipeline import NDCGKwArgs
from ptmt.research.tmt1.run import run


parameter_values: GenesWatcher = GenesWatcher(len(gene_manager))

def _fitness_func(ga_instance: pygad.GA, solution: Gene, solution_idx) -> float:
    info, cfg = create_run(
        "v3",
        "experiment6",
        "dictionary_20241130_proc3",
        "../data/ngrams/counts_with_proc.bin",
        **gene_manager.gene_to_args(solution),
        clean_translations=True,
        shared_dir=f"../data/experiment3/shared"
    )

    print(info)
    fitness = random.random()

    parameter_values.append(solution, fitness)


    return fitness

    data = run(**cfg)

    gp = data.gene_path()
    with gp.open('wb+') as f:
        pickle.dump(gp, f)

    ndcg_kwargs = { "top_n_weigts": (3, 2, 1) }
    if ndcg_kwargs is None:
        ndcg_kwargs: NDCGKwArgs = NDCGKwArgs()
    ndcg_kwargs.setdefault("top_n_weigts", (1, 1, 1))
    ndcg_kwargs.setdefault("save", True)
    ndcg_kwargs.setdefault("ignore_existing_file", False)
    for translation in data.iter_all_translations():
        translation.calculate_ndcg_for(**ndcg_kwargs)
    to_plot = PlotData(data, 3, mark_baselines=True)
    fitness = to_plot.ranking_sorted[0].ndcg_avg
    parameter_values.append(solution, fitness)
    return fitness


def _mutate_to_best_known(offspring, ga_instance: pygad.GA):
    if random.random() < 0.85:
        return ga_instance.mutation_randomly(offspring)
    for i in range(len(offspring)):
        if random.random() < 0.05:
            if parameter_values.len_of(i) > 1:
                offspring[i] = parameter_values.get_best_value(i)
    return offspring

# def _on_generation(ga_instance: pygad.GA):
#     print("Next Generation")
#     pass

if __name__ == '__main__':

    gene_manager.set_range("horizontal.factor", [0.5, 1.0, 1.5])
    gene_manager.set_range("horizontal.h_alpha", [0.5])
    gene_manager.set_range("horizontal.alpha", [1.0])
    gene_manager.set_values("horizontal.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("vertical.alpha", [1.0])
    gene_manager.set_range("vertical.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("vertical.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("ngram.boost_lang_a.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("ngram.boost_lang_a.only_positive_boost", [True], is_optional=False)

    gene_manager.set_range("ngram.boost_lang_b.factor", [0.5, 1.0, 1.5])
    gene_manager.set_values("ngram.boost_lang_b.only_positive_boost", [True], is_optional=False)

    print(gene_manager)

    ga = pygad.GA(
        gene_space=gene_manager.gene_space(),
        keep_elitism=2,
        gene_type=gene_manager.gene_type(),
        allow_duplicate_genes=True,
        initial_population=[gene_manager.rnd() for _ in range(0, 10)],
        num_generations=5,
        fitness_func=_fitness_func,
        num_parents_mating=4,
        # on_generation=_on_generation,
        # save_best_solutions=True,
        mutation_type=_mutate_to_best_known
    )

    ga.run()
    ga.summary()

    with open("data.bin", "wb") as f:
        pickle.dump(parameter_values, f)

    print(gene_manager.gene_type())

    print(parameter_values.create_best_gene())