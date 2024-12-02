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


from ptmt.research.tmt1.run import run

if __name__ == '__main__':
    """The experiments for the paper 'TMT: A Simple Way to Translate Topic Models Using Dictionaries'."""
    run(
        target_folder="../data/experiment2",
        path_to_original_dictionary="../data/final_dict/dictionary_20241130_proc3.dat.zst",
        path_to_raw_data="../data/aligned_articles_corpus/wikicomp-2014_deen.xml.bz2",
        temp_folder=r'E:\tmp\TempGen'
    )