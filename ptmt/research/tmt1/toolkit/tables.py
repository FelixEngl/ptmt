from collections import defaultdict

from ptmt.research.dirs import DataDirectory, LazyLoadingEntry


def output_table(paper_dir: DataDirectory, marker: str, ):

    table_configs = [
        "hspan=even",
        "colsep={3pt}",
        "rowsep={2pt}",
        "vlines",
        "hline{1,2}",
        "hline{3} = {2pt}",
        "cell{1}{1} = {r=2}{c}",
        "cell{1}{2} = {r=2}{c}",
        "cell{1}{3} = {c=6}{c}",
        "cell{2}{2} = {r=1}{c}",
        "cell{2}{3} = {r=1}{c}",
        "cell{2}{4} = {r=1}{c}",
        "row{1-2} = {c, font=\\bfseries}",
        "column{1-2} = {font=\\bfseries}",
        "column{2-8} = {c, colsep=2pt}",
    ]



    rows: defaultdict[str, list[LazyLoadingEntry]] = defaultdict(list)
    config_2 = ["", ""]
    for value in paper_dir.iter_all_translations(False):
        rows[value.name[0]].append(value)
        if value.name[1] not in config_2:
            config_2.append(value.name[1])
    table = [
        ["Voting Model", "vID", "tID"],
        config_2,
    ]

    last_value = None
    ct = 3
    for vID, row in rows.items():
        row_entry = []
        raw = None
        for value in row:
            new_raw = value.config.raw_voting_config()[2]
            if raw is None:
                raw = new_raw
            else:
                assert raw == new_raw
            if len(row_entry) == 0:
                row_entry.append(value.config.name_in_table)
                row_entry.append(vID)
            row_entry.append(value.name)
        assert raw is not None
        if last_value != raw:
            if last_value is not None:
                table_configs.append(f'hline{{{ct}}}')
            last_value = raw
        table.append(row_entry)
        ct += 1
    table_configs.append(f'hline{{{ct}}}')
    s = r"\begin{talltblr}[" + "\n"
    s += "    label=none,\n"
    s += "    entry=none,\n"
    s += "]{\n    "
    s += ",\n    ".join(table_configs)
    s += "\n}\n"
    for row in table:
        s += "    " + " & ".join(row) + r" \\" + "\n"
    s += r"\end{talltblr}"

    (paper_dir.root_dir.absolute() /f"table_{marker}.txt").write_text(s, encoding="UTF-8")
