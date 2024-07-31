from ptmt.research.tmt1.run import run

if __name__ == '__main__':
    run(
        target_folder="../data/experiment1",
        path_to_raw_dictionaries="../data/dictionaries",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=None
    )