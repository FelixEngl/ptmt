# Python Topic Model Translation (PTMT)

> Please Note: Currently the code is broken due some API changes in requirements of the Rust implementation. I'll will fix the issues in the upcomming months.

This repository contains our experiments for topic model translation.
The contents may change over time.

The original rust implementation of TMT is at https://github.com/FelixEngl/tmt/.

## How to build?
- Install Python 3.12 (https://www.python.org/)
- Install Rust >1.80 (https://www.rust-lang.org/)
- Prepare the Dictionaries under ``data/dictionaries`` (Not all necessary!)
- Prepare the testdata under ``data/aligned_articles_corpus`` (https://linguatools.org/tools/corpora/wikipedia-comparable-corpora/)
  - Link to wikicomp-2014_deen: https://www.dropbox.com/s/0unb4xtnrfcf2zt/wikicomp-2014_deen.xml.bz2?dl=0
- Create a Virtualenv Environment
- Install the requirements.txt
  - (Optional, ``./init.py`` does the same) Call the following if necessary:
      ````commandline
      git submodule init
      git submodule update
      cd tmt
      git checkout master
      git pull
      ````
- Activate the virtualenv
- Run ``./init.py``
  - Make sure you have updated ptmt from main before calling this script.
  - Note: We tested our code on Windows. But TMT should also compile on most Unix/Linux systems.

## Run paper specific code
Contains descriptions for running paper specific code

### General Requirements
If your PC is equal to or better than **Recommended** you can run all experiments in sequential order.
When talking about **Free memory** we refer to SSD memory. HDDs are usually too slow.

|                 | **Minimum**   | **Recommended**      |
|-----------------|---------------|----------------------|
| **CPU**         | Any Multicore | i7-10700 (or better) |
| **RAM**         | 16 GB         | 64 GB                |
| **Free memory** | 150 GB        | 300 GB               |

### TMT: A Simple Way to Translate Topic Models Using Dictionaries
The first paper about TMT.

#### Execution
- Open the file ``experiment1.py``
  - Change the parameters if necessary.
    - The temp_folder parameter has to point at a folder where you can store up to 150 Gb of data.
      It will be used for storing temporary files when processing the original dataset.
- Activate the virtualenv and run ``experiment1.py``
  - The whole process takes about 6-9h depending on your computer. The limiting factor is the number of CPUs available.
  - Results for the translation may vary depending on the random seed used by tomotopy and the order of the 
    threads when training the original tomotopy model. 


