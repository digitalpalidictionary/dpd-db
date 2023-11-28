from rich import print
from tools.cst_sc_text_sets import make_cst_text_list
from tools.paths import ProjectPaths

def main():
    pth = ProjectPaths()
    cst_test_list = make_cst_text_list(
        pth, ["kn8", "kn10"], dedupe=False)
    print(len(cst_test_list))

    name_list = []
    for c, word in enumerate(cst_test_list):
        if word == "thero":
            name = cst_test_list[c-1] 
            name_list += [remove_o(name)]
        
        elif (
            "thero" in word
            and word != "thero"
        ):
            name_list += [remove_o(word)]
        
        elif word.endswith("theragāthā"):
            name = word[:-len("ttheragāthā")]
            name_list += [remove_o(name)]

    seen = []
    final_list = []
    for n in name_list:
        if n not in seen:
            final_list += [n]
            seen += [n]

    with open("temp/theragatha_names.txt", "w") as f:
        for word in final_list:
            f.write(f"{word}\n")
    # print(final_list)
    print(len(final_list))


def remove_o(word):
    if word.endswith("o"):
        return f"{word[:-1]}a"
    else:
        return word




if __name__ == "__main__":
    main()