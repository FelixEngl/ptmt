from ldatranslate import PyDictionary, LoadedMetadataEx, DirectionMarker

if __name__ == '__main__':
    dictionary = PyDictionary.load("../../data/experiment1/my_dictionary.dat.zst")
    value: tuple[tuple[int, str, LoadedMetadataEx | None], tuple[int, str, LoadedMetadataEx | None], DirectionMarker] | None = next(iter(dictionary))
    valid_ct = 0
    for a, b, direction in dictionary:
        a: tuple[int, str, LoadedMetadataEx | None]
        b: tuple[int, str, LoadedMetadataEx | None]
        direction: DirectionMarker
        word_id_a, word_a, metadata_a = a
        word_id_b, word_b, metadata_b = b

        match direction:
            case DirectionMarker.AToB:
                continue
            case DirectionMarker.BToA:
                continue
            case _:
                pass

        if metadata_a is not None and metadata_b is not None:
            if metadata_a.meta_count().sum() > 0 and metadata_b.meta_count().sum() > 0:
                valid_ct += 1
    print(valid_ct)

