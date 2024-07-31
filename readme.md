# Python Topic Model Translation (PTMT)

This repository contains our experiments for topic model translation.
The contents may change over time.

The original rust implementation of TMT is at https://github.com/FelixEngl/tmt/.

## How to build?
- Install Python 3.12 (https://www.python.org/)
- Install Rust (https://www.rust-lang.org/)
- Prepare the Dictionaries under ``data/dictionaries`` (Not all necessary)
- Prepare the testdata under ``data/aligned_articles_corpus`` (https://linguatools.org/tools/corpora/wikipedia-comparable-corpora/)
  - Download the deen: https://www.dropbox.com/s/0unb4xtnrfcf2zt/wikicomp-2014_deen.xml.bz2?dl=0
- Create a Virtualenv Environment
- Install the requirements.txt
- Call the following if necessary:
    ````commandline
    git submodule init
    git submodule update
    ````
- Activate the virtualenv and run ``init.py``
- Open the file ``experiment.py``
  - Change the parameters if necessary.
  - Start the program (This may take a while!)
- 6-9h