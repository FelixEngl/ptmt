from ldatranslate import *

from ptmt.research.helpers.article_processor_creator import create_processor
from ptmt.research.tmt1.run import default_processor_kwargs

def create_base():
    d = PyDictionary.load(
        r"E:\git\tmt\test\dictionary_final.dat.zst"
    )
    d.create_html_view_in(r"E:\tmp\tmt_experiments\views\dictionary_final")


    d.drop_all_except(
        MetaField.Domains,
        MetaField.Languages,
        MetaField.Registers,
        MetaField.Genders,
        MetaField.Pos,
        MetaField.PosTag,
        MetaField.Numbers,
        MetaField.Regions,
    )
    processor = create_processor(**default_processor_kwargs)
    new = d.process_with_tokenizer(processor)
    new.create_html_view_in(r"E:\tmp\tmt_experiments\views\dictionary_proc")
    new.save_as(
        r"E:\tmp\tmt_experiments\dictionaries\proc1",
        "b+c"
    )


if __name__ == "__main__":
    create_base()