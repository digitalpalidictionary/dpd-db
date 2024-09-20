#!/usr/bin/env python3

"""Find super long words and hyphenate them."""

import json

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()
        self.antonym_dict: dict = self.load_antonym_dict()
        self.last_word: int = self.antonym_dict["last_word"]
        self.debug: bool = False
        
        # word in progress
        self.w1: DpdHeadword
        self.w1_orig_antonym: str

        # word being checked
        self.w2: DpdHeadword
        
        self.yes_no: str = "[white]y[green]es [white]n[green]o "


    def load_antonym_dict(self)-> dict:
        if self.pth.antonym_dict_path.exists():
            with open(self.pth.antonym_dict_path) as file:
                return json.load(file)
        else:
            print("[red]error opening antonym dict")
            return {}


    def save_antonym_dict(self):
        self.last_word = self.w1.id
        self.antonym_dict["last_word"] = self.w1.id
        with open(self.pth.antonym_dict_path, "w") as file:
            json.dump(
                self.antonym_dict, file, 
                ensure_ascii=False, indent=2)
    

    def update_exceptions(self):
        if not self.antonym_dict["exceptions"].get(self.w1.id, None):
            self.antonym_dict["exceptions"].update({self.w1.id: []})
        self.antonym_dict["exceptions"][self.w1.id].append(self.w2.id)
        self.save_antonym_dict()
        print(self.antonym_dict["exceptions"][self.w1.id])


    # def update_antonym_pairs(self):
    #     if not self.antonym_dict["exceptions"].get(self.w1.id, None):
    #         self.antonym_dict["exceptions"] = {self.w1.id: []}
    #     self.antonym_dict["exceptions"][self.w1.id].append(self.w2.id)
    #     self.save_antonym_dict()
    #     print(self.antonym_dict["exceptions"][self.w1.id])
    

    def update_last_word(self):
        self.antonym_dict["last_word"] = self.w1.id
        

def main():
    tic()
    print("[bright_yellow]find missing antonyms and mistakes in antonyms")
    g = ProgData()
    
    for i in g.db:
        if i.id > g.last_word:
            if i.meaning_1:
                g.w1 = i
                g.w2 = None
                check_w1(g)

    toc()


def check_w1(g):
    """Various tests and reroute as applicable."""

    def printer(w, colour):
        print(f"[{colour}]{w.id:>5} {w.lemma_1:<30}{w.pos:10}{w.antonym}")

    if g.w1.antonym:
        print("_"*100)
        print()
        printer(g.w1, "white")
            
        w1_antonyms = g.w1.antonym_list
        for w1_antonym in w1_antonyms:
            g.w1_orig_antonym = w1_antonym
            results = g.db_session \
                .query(DpdHeadword) \
                .filter(DpdHeadword.lemma_1.like(f"%{w1_antonym}%")) \
                .all()
            
            # FIXME here the results must test of the antonym is in the results

            
            if results:
                g.results = results
                no_results = True
                for r in results:
                    g.w2 = r
                    w2_antonyms = r.antonym_list
                    
                    
                    for w2_antonym in w2_antonyms:
                       
                        if r.lemma_clean == w1_antonym:

                            # antonym and pos matches
                            if (
                                g.w1.lemma_clean == w2_antonym
                                and r.pos == g.w1.pos
                            ):
                                printer(r, "light_green")
                                no_results = False
                                if g.debug:
                                    input()

                            # antonym matches, pos doesn't
                            elif (
                                g.w1.lemma_clean == w2_antonym
                                and r.pos != g.w1.pos
                            ):
                                # check if w2 not already in exceptions
                                if (
                                    g.w2.id not in g.antonym_dict\
                                        .get("exceptions")\
                                        .get(str(g.w1.id), {})
                                ):
                                    
                                    print()
                                    print("[red]pos does not match")
                                    print(f"[green]{'lemma_1':<30}{'pos':10}{'antonym':<20}meaning")
                                    print(f"{g.w1.lemma_1:<30}{g.w1.pos:10}{g.w1.antonym:<20}{g.w1.meaning_1}")
                                    print(f"{r.lemma_1:<30}[red]{r.pos:<10}[/red]{r.antonym:<20}{r.meaning_1}")
                                    if no_other_results(g):
                                        update_w2(g)
                                        no_results = False

                            # antonym does not match, pos does
                            elif (
                                not g.w1.lemma_clean == w2_antonym
                                and r.pos == g.w1.pos
                            ):
                                print()
                                print("[red]antonym does not match")
                                print(f"[green]{'lemma_1':<30}{'pos':10}{'antonym':<20}meaning")
                                print(f"{g.w1.lemma_1:<30}{g.w1.pos:10}{g.w1.antonym:<20}{g.w1.meaning_1}")
                                print(f"{r.lemma_1:<30}{r.pos:<10}[red]{r.antonym:<20}[/red]{r.meaning_1}")
                                
                                # check if w2 not already in exceptions
                                if (
                                    g.w2.id not in g.antonym_dict\
                                        .get("exceptions")\
                                        .get(str(g.w1.id), {})
                                ):
                                    # FIXME handle words with multiple antonyms
                                    if "," not in g.w2.antonym:
                                        update_w2(g)
                                        no_results = False
                                    else:
                                        print()
                                        print("[red]!!! gotta deal with multiple antonyms !!!")
                                        print()


                            # w2 has no antonym
                            elif (
                                not r.antonym 
                                and r.pos == g.w1.pos
                            ):
                                print()
                                print("[red]w2 has no antonym")
                                print(f"[green]{'lemma_1':<30}{'pos':10}{'antonym':<20}meaning")
                                print(f"{g.w1.lemma_1:<30}{g.w1.pos:10}{g.w1.antonym:<20}{g.w1.meaning_1}")
                                print(f"{r.lemma_1:<30}{r.pos:10}[red]None{r.antonym:<20}[/red]{r.meaning_1}")
                                update_w2(g)
                                no_results = False

                if no_results:
                    g.w2 = None
                    update_w2(g)


def no_other_results(g):
    """test if no other results contain the antonym and pos."""
    for r in g.results:
        if (
            r.lemma_clean == g.w1_orig_antonym
            and r.pos == g.w1.pos
        ):
            return False
    return True


def update_w2(g):
    print()
    print(f"[cyan]u [green] update w1 [white]{g.w1.lemma_1}[/white] antonym [white]{g.w1.antonym}")
    print(f"[cyan]d1[green] delete w1 [white]{g.w1.lemma_1}[/white] antonym [white]{g.w1.antonym}")
    if g.w2:
        print(f"[cyan]a [green] auto-update w2 [white]{g.w2.lemma_1}[/white] antonym [white]{g.w2.antonym}")
        print(f"[cyan]r [green] replace [white]{g.w2.lemma_1}[/white] antonym [white]{g.w2.antonym}")
        print(f"[cyan]m [green] manual update w2 [white]{g.w2.lemma_1}[/white] antonym [white]{g.w2.antonym}")
        print(f"[cyan]d2[green] delete w2 [white]{g.w2.lemma_1}[/white] antonym [white]{g.w2.antonym}")
        print("[cyan]e [green] add an exception")
    print("[cyan]p [green] pass", end=" ")
    route = input()

    if route == "u":
        """update w1 antonym"""
        print()
        print(f"[green]enter new antonym for [white]{g.w1.lemma_1}: ", end=" ")
        new_antonym = input()
        if new_antonym:
            g.w1.antonym = new_antonym
            g.db_session.commit()
            print(f"{g.w1.lemma_1} [green]antonym udpated with [white]{g.w1.antonym}")
    
    elif route == "d1":
        """delete w1 antonym"""
        print()
        g.w1.antonym = ""
        g.db_session.commit()
        print(f"{g.w1.lemma_1} [green]antonym deleted")
    
    if g.w2:
        if route == "a":
            """auto-update w2"""
            print()
            if g.w2.antonym:
                g.w2.antonym = f"{g.w2.antonym}, {g.w1.lemma_clean}"
            else:
                g.w2.antonym = g.w1.lemma_clean
            g.db_session.commit()
            print(f"{g.w2.lemma_1} [green]antonym udpated with [white]{g.w2.antonym}")

        elif route == "r":
            """reaplce w2"""
            print()
            g.w2.antonym = g.w1.lemma_clean
            g.db_session.commit()
            print(f"{g.w2.lemma_1} [green]antonym udpated with [white]{g.w2.antonym}")

        elif route == "m":
            """manual update w2"""
            print()
            print(f"[green]enter new antonym for [white]{g.w2.lemma_1}: ", end=" ")
            new_antonym = input()
            if new_antonym:
                g.w2.antonym = new_antonym
                g.db_session.commit()
                print(f"{g.w2.lemma_1} [green]antonym udpated with [white]{g.w2.antonym}")
        
        elif route == "d2":
            """delete w2 antonym"""
            print()
            g.w2.antonym = ""
            g.db_session.commit()
            print(f"{g.w2.lemma_1} [green]antonym deleted")
        
        elif route == "e":
            """add exception"""
            print()
            g.update_exceptions()



# def antonym_doesnt_exist(g):
#     """the antonym doesnt exists, what to do?"""
#     print()
#     print(f"[red][white]{g.w1.antonym} ({g.w1.pos})[/white] doesn't exist in the db. What to do?")
#     print(f"[green]1. update [white]{g.w1.antonym}")
#     print(f"[green]2. delete [white]{g.w1.antonym}")
#     print("[green]3. pass: ", end="")
#     route = input()
    
#     if route == "1":
#         print()
#         print("[green]What is the correct antonym? ", end="")
#         new_antonym = input()
#         if new_antonym:
#             g.new_antonym = new_antonym
#             g.w1.antonym = new_antonym
#             g.db_session.commit()
            
#             print()
#             print(f"[green]Would you like to add [white]{g.w1_orig_antonym}[/white] as an antonym of [white]{new_antonym} ({g.w2.pos})[/white]? {g.yes_no} ", end="")
#             route = input()
#             if route == "y":
#                 add_antonym_back(g)
    
#     if route == "2":
#         print()
#         g.w1.antonym = ""
#         g.db_session.commit()
#         print(f"{g.w1.lemma_1} [green]antonym deleted")


# def add_antonym_back(g):
#     results = g.db_session \
#         .query(DpdHeadword) \
#         .filter(DpdHeadword.lemma_1.like(g.new_antonym))
    
#     for r in results:
#         print()
#         print(f"{r.lemma_1} {r.pos} {r.antonym}")
#         print(f"[green]the new antonym will be [white]{g.w1_orig_antonym}[/white] {g.yes_no} ")

#         r.antoym = g.orig_antonym
#         g.db_session.commit()
#         print("[green]db updated")


# def delete_antonym(g):
#     print()
#     print("delete antonym logic goes here")
#     input("press enter to continue ")



# def update_w2_or_add_exceptions(g):
#     print()
#     print("update w2 or add exceptions logic goes here")
#     input("press enter to continue ")

if __name__ == "__main__":
    main()

   
# a few different appraches
# -------------------------
# 1. words that currently have an anytoms: enure the antonym 
#    has an antonym
# 2. neg word: if there's a positive with the same part of speech,
#    and the meaning is in the same ballpark, mark sure there is 
#    an antonym
# 3. check for words that have antonyms, but their opposite is a 
#    different part of speech, for example nt has an antonym that 
#    is an adjective.  
