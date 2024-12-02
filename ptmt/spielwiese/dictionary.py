from ldatranslate import *

from ptmt.research.helpers.article_processor_creator import create_processor
from ptmt.research.tmt1.run import default_processor_kwargs

def create_base():
    d = PyDictionary.load(
        r"../../data/final_dict/dictionary_final2.dat.zst"
    )
    # d.create_html_view_in(r"E:\tmp\tmt_experiments\views\dictionary_final")
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
    print("Dropped all")
    x = d.translation_direction
    processor = create_processor(str(x[0]), str(x[1]), **default_processor_kwargs)

    print(processor.to_json())

    print("Processor")
    new = d.process_with_tokenizer(processor)
    print("New")
    d = None
    new.create_html_view_in(r"E:\tmp\tmt_experiments\views\dictionary_proc")
    new.save_as(
        r"E:\tmp\tmt_experiments\dictionaries\proc1",
        "b+c"
    )


if __name__ == "__main__":
    create_base()