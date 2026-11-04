# Sample new prompts (task 2.2)

## Fixed part (the same for every word)

````text
# Task
At the end of this message is one Pāḷi word as it appears in a text, with the sentences it occurs in and some related dictionary entries. Write a draft dictionary entry for it in the style of the Digital Pāḷi Dictionary (DPD).

# Answer
Return one JSON object with exactly these keys, in this order. Every value is a string. Use "" for a field that does not apply. No text before or after the JSON.
{"lemma_1": "", "lemma_2": "", "pos": "", "grammar": "", "meaning_2": "", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "", "construction": "", "stem": "", "pattern": "", "comment": ""}

# Example
Word in the text: lokanāyakaṃ
{
 "lemma_1": "lokanāyaka",
 "lemma_2": "lokanāyako",
 "pos": "masc",
 "grammar": "masc, comp",
 "meaning_2": "world leader; guide to the world; master of the earth",
 "root_key": "",
 "root_sign": "",
 "root_base": "",
 "family_root": "",
 "family_compound": "loka nāyaka",
 "construction": "loka + nāyaka",
 "stem": "lokanāyak",
 "pattern": "a masc",
 "comment": "An epithet of the Buddha. Accusative singular in the text."
}

# Field rules

## lemma_1 (the headword)
- Nouns and adjectives: the stem, without a case ending. a-stems end in -a (narena → nara), ī-stems in -ī (medhāvino → medhāvī), feminine ā-stems in -ā (vedanaṃ → vedanā), u-stems in -u (bhikkhavo → bhikkhu).
- Present, imperative, optative and future verbs: the present 3rd singular (gacchanti, gacchatu, gaccheyya, gacchissati → gacchati). The pos is then pr. Only an irregular future gets its own future headword (āhañchati, pos fut).
- Aorist: the aorist 3rd singular (upasaṅkamiṃsu → upasaṅkami).
- Participles: the masculine stem. Present participles end in -nta or -māna (vandanto → vandanta, bhuñjamāno → bhuñjamāna). Past and potential participles end in -a (nisinno → nisinna).
- Absolutives, gerunds, infinitives and indeclinables: the form as it is (gantvāna, kātave).
- An enclitic or quotation mark joined to the end (-ca, -va, -eva, -pi, -ti, -iti): leave it out and write the entry for the main word (buddhova → buddha, gacchāmīti → gacchati).
- Sandhi of two or more full words (kocañño = koci + añño): keep the form as it is. The pos is sandhi.
- A noun joined to its verb (agāramāvasati = agāraṃ + āvasati) is a compound verb. The pos is the verb's; the grammar is "pr, comp vb".

## lemma_2
- Nouns: the nominative singular (nara → naro, citta → cittaṃ, vedanā → vedanā).
- Adjectives, participles and every other part of speech: exactly lemma_1, never a nominative (pasannacitta → pasannacitta, not pasannacitto).

## pos
- Pick one from the list of real values below.
- -tvā, -tvāna, -itvā: abs. -ya, -iya, -yāna: ger. -tuṃ, -tave, -tāye: inf.
- Adverbs and all other indeclinables: ind.
- Words ending in -ādi are usually masc.

## grammar
- Compound noun or adjective: "masc, comp", "adj, comp".
- Noun or adjective made from another word: "adj, from sīla", "masc, from gāma", "nt, dimin of agāra", "fem, abstr, from mitta".
- Verbs: "pr", "pr, caus of bhavati", "aor of upasaṅkamati", "fut of āhanati".
- Other verb forms: the pos, "of", and the present 3rd singular: "prp of vandati", "pp of pasīdati", "abs of gacchati", "ger of paccavekkhati", "inf of gacchati", "abs of na paṭipucchati".
- Indeclinables: "ind, adv", "ind, prep", "ind, emph".
- Sandhi: "sandhi," and the pos of each part: "sandhi, pron + pron".

## meaning_2
- English meanings that fit the sentences, most likely first, separated by "; " (nara = man; person; human being).
- Present verbs in the 3rd singular (approaches; visits), aorists in the past (approached; drew near), futures with "will" (will attain), participles as "honouring" or "seated", absolutives as "having gone", infinitives as "to go".
- A preposition the word needs goes in brackets: "goes (to)", "goodwill (towards)".
- Proper names: "name of a mountain", "name of a river", with the story or text where it helps.
- In Vinaya texts, compounds ending in vatthu mean "case of ...".
- No explanation here. That goes in comment.

## root_key, root_sign, root_base, family_root
- These apply to words that go back to a verbal root: verbs, participles, absolutives, gerunds, infinitives, and nouns or adjectives made from them (bhikkhu, mettā).
- Leave all four empty for compounds of two or more words and for sandhi.
- root_key: pick one root from the list below, with its number (√kam 1). If no root fits, leave it empty.
- root_sign: pick one from the list below.
- root_base: for verbs and verb forms only. The root + sign > base, with (caus) or (irreg) where it applies: "√bhū + *e > bhāve (caus)", "√gam + a > gama > gaccha (irreg)". Empty for nouns and adjectives.
- family_root: the prefixes and the root, separated by spaces, without the root's number: "upa saṃ √kam", "pa √sad", "√gam".

## family_compound
- Compounds: the dictionary form of each part, separated by spaces, no +: "loka nāyaka", "akusala kamma patha". Suffixes such as -ka, -tā or -ya are not parts.
- Negative compounds show only the positive parts: nadhammagaruka = "dhamma garu".
- A noun or adjective made from another word: that word ("gāma" for gāmaṇi, "sīla" for sīlavant, "agāra" for agāraka).
- Verbs and participles: the same as lemma_1.
- Sandhi: empty.

## construction
- Pāḷi only, no English. Parts are joined with " + ".
- Compounds: the parts as they stand in the word: "loka + nāyaka", "agāraṃ + āvasati".
- Words made with a suffix: the base + the suffix: "agāra + ka", "sīla + vant", "gāma + aṇi".
- Verbs and verb forms: the prefixes + the base + the ending: "upa + saṃ + kama + ti", "bhuñja + māna", "bhāve + ti", "pa + √sad + na".
- Nouns made straight from a root: "√mar > mār + *a".
- Sandhi: the words as they stand: "koci + añño".

## stem and pattern
- pattern: pick one from the list below. Its first word is the ending of lemma_1. The stem is lemma_1 without that ending: lokanāyaka with "a masc" → "lokanāyak"; medhāvī with "ī masc" → "medhāv"; vandati with "ati pr" → "vand"; bhuñjamāna with "māna prp" → "bhuñja"; sīlavant with "ant adj" → "sīlav"; upasaṅkami with "i aor" → "upasaṅkam".
- Indeclinables, absolutives, gerunds, infinitives, sandhi and idioms: the stem is "-" and the pattern is empty.
- Use the stems and patterns of the related entries as a guide. Never use a pattern that is not in the list.

## comment
- Your own notes: how the word is used in the sentences, its case in the text, doubts, and other possible analyses.
- Keep it short. Nothing that is already in another field.

# Real dictionary values

## pos (pick one)
adj: adjective
nt: neuter noun
masc: masculine noun
fem: feminine noun
pr: present tense verb
pp: past participle
aor: aorist
prp: present participle
abs: absolutive
ind: indeclinable
sandhi: sandhi compound
ptp: potential participle
idiom: idiomatic expression
inf: infinitive
ger: gerund
pron: pronoun
card: cardinal number
fut: future verb
opt: optative verb
ordin: ordinal number
imperf: imperfect verb
prefix: prefix
imp: imperative verb
root: root
cond: conditional verb
suffix: suffix
cs: conjugational sign
letter: letter of the alphabet
ve: verbal ending
perf: perfect verb

## pattern (pick one, most common first)
a nt · a adj · a masc · ā fem · a pp · ati pr · ī adj · i aor · eti pr · i fem · a ptp · anta prp · māna prp · esi aor · ī fem · i masc · enta prp · u nt · ī masc · a masc pl · aka adj · ar masc · āti pr · u masc · ant adj · āsi aor · u fem · i adj · u adj · aī adj · as masc · oti pr · i nt · a ordin · ta pron · ā imperf · i card · a nt pl · ū adj · ū masc · ā card · rāja masc · a2 card · a pron · kamma nt · ahaṃ pron · ant masc · a1 card · a2 masc · hari aor · onta prp · ima pron · i aor isuṃ · ssati fut · āna prp · i aor issaṃ · tvaṃ pron · ati fut · mātar fem · issa cond · ya pron · issati fut · hanati pr · ar fem · ka pron · kaci pron · ar2 masc · kari aor · anta adj · i aor aṃsu · hiti fut · ddasa aor · hoti pr · santa prp · a nt east · atthi pr · brahma masc · catu card · eti pr 2 · parisā fem · ssa opt · ti card · lattha aor · a adj east · bhavant masc · eka adj · hosi aor · jāniyā opt · jāti fem · aī ordin · āsi aor irreg · ī masc pl · a nt irreg · dvi card · go masc · karoti pr · kubbati pr · santa masc · eyya opt · u masc pl · arahant masc · avoca aor · brūti pr · i masc pl · vī fem · āha perf · ū fem · a pp east · ekacca pron · ubha pron · ā root · a masc east · amu pron · dakkhati pr · eka card · siyā opt · ā fem pl · a perf · assosi aor · cha card · i2 card · vajjā opt · anta masc · nadī fem · natthi pr · addha masc · avaca imperf · dajjā opt · kati pron pl · kayirā opt · o letter · pokkharaṇī fem · ī fem pl · addasā imperf · dammi pr · jantu masc · pivi aor · ratti fem · santa adj · u nt pl · u root · u ve · ubhaya adj · ṃ ve · a ordin east · a pron east · essa cond · i fem pl · paccabyādhi aor · u fem pl · unta prp · yuva masc · ā letter

## root_sign (pick one, most common first)
a · *e · ya · *āpe · ṃa · nā · *aya · o · *a · ṇhā · iya · īya · sa · ṇā · uṇā · āya · *āpaya · *e iya · ṃa *e · ṃa *āpe · ṇo · *e īya · nā *āpe · ṇhā *āpe · ya *āpe · *āpe iya · *āpe īya · ṃa iya · ṃa īya · nā *e · ya *e · ya iya · ṃa *aya · ya īya · *ala · unā · ya *aya · yā e · *a iya · *e ya · no · sa *āpe · uṇā *āpe · yā · ṃa *āpe īya · ṇhā īya · *iya · *ssa · *ya · *īya · a ssa · aya · issa · nā ya · nā īya · ppa · sa iya · sa āpe · ta · uṇā īya · ya ssa · ya āpe · ā · ṇhā iya · ṇhā āya · ṇā *āpe

## root_key (pick one; the meaning is in brackets)
√acc 1 (shine, praise); √acc 2 (worship); √ad (eat); √add (afflict); √agg (move crookedly); √aggh (be worth); √ah (speak); √aj (go, drive); √akkh (see); √an (breathe, blow); √ap (reach, attain); √ar (move, attain); √arah (deserve, be worthy); √as 1 (be); √as 2 (throw, hurl); √as 3 (eat); √as 4 (eat); √atth (wish for); √añc (bend); √añch (extend, draw along); √añj 1 (distinguish); √añj 2 (smear, anoint); √añj 3 (pay respect); √aḍḍ (judge); √aṃs (divide, distribute); √aṅg (walk); √aṇ (recite); √aṭ (roam, wander); √badh (bind, tie); √bah 1 (be outside); √bah 2 (increase); √bal (be strong, live); √bandh (bind, tie); √bhad (be good, be lucky); √bhaj 1 (divide, distribute); √bhaj 2 (associate, keep company); √bhajj (cook); √bhakkh (eat); √bham (turn, revolve, buzz); √bhar (carry, support); √bhas 1 (fall down); √bhañj (break, destroy); √bhaṇ (talk, speak); √bhaṇḍ (blame, accuse); √bhid (break, split); √bhikkh (beg); √bhis (fear); √bhuj 1 (use, eat, enjoy); √bhuj 2 (bend); √bhus (fall heavily); √bhuss (bark); √bhā (shine, speak); √bhās 1 (speak); √bhās 2 (shine); √bhī (fear); √bhū (be, become); √bhūs (adorn, decorate); √bil (break, chop); √brah (increase); √brū (say); √brūh (increase); √budh (know, wake up); √buh (pluck out, uproot); √bādh (press, oppress); √cabb (chew, spit out); √caj (give up, let go); √cakkh (see); √cal (shake, tremble); √cam (wash, rinse); √cand (glow, be bright); √car 1 (move, walk); √car 2 (act, behave); √caṇḍ (be fierce, be violent); √chad (cover, conceal); √chand (desire, please); √chaḍḍ (discard, abandon); √chid (cut, divide); √chubh (throw out); √chup (touch); √chuṭ (cut off); √chā (be hungry); √ci 1 (gather, accumulate); √ci 2 (note, observe); √cikkh (show, tell); √cil (clothe); √cint (think); √cit 1 (think, intend); √cit 2 (mark); √citt (paint, design); √ciṭ (send, abuse); √cu (shift, fall away, die); √cud (impel, accuse); √cumb (kiss); √cup (move); √cur (steal); √cuṇṇ (grind, crush, powder); √cāy (honour); √dah (be strong); √dakkh (be able, please); √dal (split, tear apart); √dam (be tame); √dandh (be slow); √dap (be arrogant); √dar 1 (break, split apart); √dar 2 (fear); √dar 3 (respect, have affection); √day (be kind, have pity); √dev (lament); √dhaj (move, flap); √dham (blow, sound); √dhan 1 (be rich); √dhan 2 (sound); √dhar 1 (hold, carry, endure); √dhar 2 (wear, hold, carry); √dhaṃs (fall down, destroy); √dhe (drink, suck); √dhov (wash, sharpen); √dhur (be crooked, be corrupt); √dhuv (be firm, be solid); √dhā (place, support); √dhāv 1 (run, flow); √dhāv 2 (polish, sharpen); √dhī (think); √dhū (shake, smoke); √dhūp (smoke); √dih (accumulate, smear); √dikkh (consecrate); √dis 1 (see); √dis 2 (point out, explain); √dis 3 (dislike, hate); √div (shine); √dru (run, flow); √du (burn, torment); √dubbh (deceive, be treacherous); √duh (milk a cow); √dukkh (be painful); √dul (swing); √dus 1 (be angry, be corrupt); √dus 2 (hate, dislike); √dvar (obstruct, prohibit); √dā 1 (give); √dā 2 (be pure, be clean); √dā 3 (tie, bind); √dā 4 (cut, break apart); √dā 5 (sleep); √dī (be afflicted); √dīp (shine, explain); √dū (go, run); √edh (flourish, prosper); √ej (move, shake); √es (seek, search); √gabbh (be bold, be daring); √gad (speak); √gadh (bind, tie); √gah (grasp); √gaj (roar, make sound); √gajj (roar, thunder); √gal 1 (drip, flow); √gal 2 (eat); √gam (go); √gandh (hurt, harm); √ganth (tie, bind); √gar 1 (esteem, be heavy); √gar 2 (drip, swallow); √garah (blame); √gas (eat, swallow); √gaves (seek, search); √gaṇ (calculate, group); √ghar 1 (drip); √ghar 2 (burn, be hot); √ghas (eat); √ghaṃs (rub, grind, pound); √ghaṭ 1 (strike, kill); √ghaṭ 2 (join together); √ghaṭ 3 (be busy with, strive); √ghaṭṭ 1 (hit, strike); √ghaṭṭ 2 (join together); √ghur (scream, be awful); √ghus (shout, make noise); √ghā (smell); √gidh (be greedy); √gil (eat, swallow); √gilā (be sick, be tired); √gir 1 (raise); √gir 2 (call, speak); √guh (hide, conceal); √gumph (tie, string together); √gup 1 (dislike); √gup 2 (guard); √guḷ (roll around, protect); √guṇ (repeat, multiply); √guṇṭh (enclose, envelope); √gā (sing); √gādh (stand firmly); √gāh (dive, plunge); √gū (excrete); √had (excrete); √han (strike, kill); √har 1 (carry); √har 2 (take, seize); √har 3 (live); √har 4 (be ashamed); √hariy (like); √has (elate, laugh); √haṃs (rise, elate); √haṭ (shine); √heṭh (harass, annoy); √hi 1 (send); √hi 2 (impel); √hikk (hiccup); √hir (be ashamed); √his (hurt, harm); √hiṇḍ (roam, wander); √hu (pour, offer as oblation); √hā 1 (abandon); √hā 2 (decrease); √hīḷ (scorn); √hū (be); √i 1 (come, go); √i 2 (study, recite); √idh (succeed, accomplish); √ikkh (see, mark); √indh (fire, burn); √is (wish for); √iss (be envious, be jealous); √iñj (move, shake); √jagg (look after); √jaggh (laugh); √jakkh (eat); √jal 1 (shine, blaze); √jal 2 (hide, conceal); √jambh (yawn, stretch, wake up); √jan (be born, produce); √japp (mutter, pray); √jar (age); √jaṭ (twist, tangle); √jhap (burn, blaze); √jhe (burn, blaze); √jhā (think, meditate); √ji 1 (conquer); √ji 2 (conquer); √ju (be fast); √jus (like, please); √jut (shine); √jāgar 1 (be awake, be watchful); √jāgar 2 (be awake, be watchful); √jī (age, decay); √jīr (grow old, decay); √jīv (live); √kac (shine, bind); √kal 1 (spend time); √kal 2 (accomplish); √kal 3 (calculate, add); √kalah (argue); √kam 1 (go); √kam 2 (desire); √kamp (shake, tremble); √kan (shine, like); √kand (wail, cry out); √kap (take pity); √kapp 1 (be fit, be suitable); √kapp 2 (think); √kar (do, make); √kas 1 (drag, draw); √kas 2 (hurt, trouble); √kass (drag, draw along); √kat (cut); √kath (speak, narrate); √katth (boast); √kañc 1 (bind, cover); √kañc 2 (shine); √kaḍḍh (drag, plough); √kaṅkh 1 (wish for); √kaṅkh 2 (doubt); √kaṇ (make sound); √kaṇḍ (break, pierce); √kaṭh 1 (live in distress); √kaṭh 2 (boil, burn); √kel (care, cherish); √khac (adorn, inlay); √khal 1 (stumble, make mistake); √khal 2 (clean, rinse); √khal 3 (accumulate); √kham (tolerate, endure); √khambh (prop, be stiff); √khan (hurt, break); √khand (jump); √khandh (collect, accumulate); √khar (perish, break apart); √khañj (limp); √khaṇ (dig); √khaṇḍ (break); √khi (live, abide peacefully); √khip 1 (throw); √khip 2 (sneeze); √khiṭ (frighten, scare); √khubh (shake, agitate); √khud (be hungry); √khur (cut); √khuṃs (insult); √khyā (announce); √khā (tell, announce); √khād (chew); √khī (exhaust, destroy); √kilam (be weary); √kilid (be wet); √kilis 1 (be dirty, be molested); √kilis 2 (trouble); √kir (scatter, sprinkle); √kis (be thin); √kit 1 (heal, cure); √kit 2 (live); √kit 3 (know, doubt); √kitt (make known); √kiñc (crush); √ku (sing, sound); √kuc (contract); √kucch (revile); √kudh (be angry); √kuh (deceive); √kujj (turn); √kul (be close); √kunth (hurt, cause pain); √kup (shake, be angry); √kur (sound); √kus 1 (call, insult); √kus 2 (fill, enfold); √kus 3 (cut, tear); √kuth (boil, burn); √kuñc (be crooked, be bent); √kuṇ (be crooked, be bent); √kuṇḍ (bend, mutilate); √kuṇṭh (be blunt, be lame); √kuṭ 1 (be crooked, be bent); √kuṭ 2 (knock, beat); √kuṭ 3 (cut); √kuṭṭ (smash, powder); √kā (makes sound); √kās 1 (shine, be visible); √kās 2 (cough); √kī (buy); √kīḷ (play); √kūj (make sound); √kūl (obstruct, embank); √kūḷ (burn); √labh (get); √lag (stick, adhere); √lagg (stick, adhere); √lagh (lift up, jump); √lajj (be ashamed); √lakkh (mark); √lamb (hang); √lambh (deceive); √lap (speak, chat); √las (shine, be active); √lañch (mark); √laḷ (play, move about); √lih (lick, lap); √likh (scratch, write); √lip (coat, smear); √lis (be small); √liṅg 1 (embrace); √liṅg 2 (differentiate); √loc (see, illuminate); √lok (look); √lu (cut, reap, mow); √lubh 1 (be greedy); √lubh 2 (fool, bewilder); √luj (be broken apart); √lup (cut off, rob); √luñc (pluck out, tear); √luḷ (agitate, be greedy); √lā (take); √lī 1 (stick, hide); √lī 2 (stick, hide); √mad (be mad, be intoxicated); √madd (crush, grind); √magg (seek, search); √mah 1 (increase); √mah 2 (venerate); √majj (rub, polish); √makkh (rub, erase); √mal (dirty, stain); √man (think); √mant (counsel, invite); √manth (churn, crush); √mar (die); √maris (be patient); √mas 1 (touch, rub); √mas 2 (buzz, hum); √mas 3 (harm, destroy); √math (churn, stir); √mañc (hold up, support); √maṅg (be auspicious); √maṇ (abandon); √maṇḍ (adorn); √medh 1 (be wise); √medh 2 (hurt, harm); √mhi (smile); √mi (exchange, barter); √mid (be fat); √migh (sprinkle, shower); √mih 1 (urinate, excrete); √mih 2 (smile, chuckle); √milā (shrink, wither); √mis (wink, blink); √miss (mix, mingle); √mith (pair); √mitt (be friendly); √mokkh (be freed); √muc (release, free); √mucch (thicken, fixate); √mud (be soft, be happy); √muh (be deluded, be confused); √mujj (dive, sink, submerge); √mun (think, know); √mus 1 (lie, forget); √mus 2 (steal); √muṇḍ (be bald, shave); √mā (measure); √mīl (close eyes); √mūl (support); √nabh (burst, split); √nad (roar); √nadh (wrap, twist); √nah (bind, arm); √nakkh (attain, arrive); √nam (bend); √namass (bow, worship); √nand (delight, enjoy); √nar (lead); √nas (be lost, disappear); √nat (dance, act); √naṭ (bend, dance); √ness (take away); √nhā (bathe); √nind (blame, abuse); √nud (drive out, reject); √nādh (beg); √nāth (have power, protect); √nī (lead, carry); √nīl (be blue); √op (placing); √pabb (grow); √pac (cook, mature, ripen); √pad (go, step); √palus (burn); √palā (run away, flee); √panth (go, move); √par (be active); √pas (tie, bind); √pat 1 (fall); √pat 2 (command, control); √path 1 (go, move); √path 2 (expand); √pañc (expand, spread); √pañh (ask, question); √paṇ (trade, barter); √paṇḍ (mock, tease); √paṭ 1 (split, tear); √paṭ 2 (go); √paṭh (read, recite); √pel (move, propel); √phal 1 (split open); √phal 2 (fruit, ripen); √phand (shake, quiver); √phar (suffuse, pervade); √phaṇ (skim); √phull (expand, bloom); √phus 1 (touch); √phus 2 (sprinkle, splash); √phuṇ (suffers); √phuṭ 1 (beat, smash); √phuṭ 2 (swell, burst); √phā (swell, get fat); √pih (desire, envy); √pis 1 (send); √pis 2 (grind, hurt); √pis 3 (speak ill); √piṇḍ (collect); √piṭ (collect); √plu 1 (float, swim); √plu 2 (spring, swing); √pu (purify, cleanse); √pucch (ask, question); √pul (increase); √pupph (flower, expand); √pus (nourish, take care); √puth (expand); √puñch (wipe); √puṇ (be skilful, be precise); √puṭ (wrap, envelop); √puṭh (beat, hurt); √pā 1 (drink); √pā 2 (protect, guard); √pāl (protect); √pāy (increase); √pī (love, please); √pīḷ (press, crush); √pīṇ (please, swell); √pūj (honour, venerate); √pūr (fill, fulfil); √pūy (rot, fester); √rabh 1 (begin); √rabh 2 (be aroused, be violent); √rac (prepare, arrange); √rah (leave, desert); √raj 1 (desire); √raj 2 (colour); √rakkh (protect); √ram 1 (delight, please); √ram 2 (stop, abstain); √randh 1 (cook); √randh 2 (hurt, wound); √ras (taste); √rañj (dye, desire); √raṇ (conflict, make war); √ric (empty); √ris (hurt); √ru (cry, howl); √ruc (shine, like); √rud (cry); √rudh 1 (obstruct); √rudh 2 (please, accept); √ruh (ascend, grow); √ruj (hurt, be painful); √rup (be broken apart, hurt); √rus (be angry); √rādh (succeed, please); √rāj (rule, shine); √rūp (form, produce); √sad (sink, sit, settle); √sadd (sound); √sadh (mock, ridicule); √sah 1 (overcome, prevail); √sah 2 (be able); √saj 1 (stick, cling); √saj 2 (relinquish, let loose); √saj 3 (embrace); √sajj 1 (relinquish, let loose); √sajj 2 (prepare, decorate); √sak (be able, be powerful); √sakk (move); √sam 1 (be calm, be tired); √sam 2 (exert, strive); √sambh 1 (be calm, be confident); √sambh 2 (reach, attain); √san (like, love); √sand (flow); √sap (curse); √sapp (crawl); √sar 1 (go, flow); √sar 2 (remember); √sar 3 (make sound); √sar 4 (shine); √sar 5 (hurt, injure); √sas 1 (breath); √sas 2 (slaughter); √sañj (clasp, embrace); √saṃs 1 (proclaim, praise); √saṃs 2 (wish, desire); √saṅk (doubt, suspect); √saṇ (make sound); √saṭ (split); √saṭh (deceive); √sev (serve, associate); √si 1 (depend on, associate with); √si 2 (bind); √si 3 (sharpen); √si 4 (smile); √sic (sprinkle, pour); √sid 1 (sweat, steam); √sid 2 (be cool); √sidh 1 (prevent, prohibit); √sidh 2 (succeed, be accomplished); √sikkh (learn, train); √silis (embrace, cling); √silok (be famous); √silāgh (boast); √sinā (bathe); √sis (remain, distinguish); √sit (be white); √siv 1 (sew); √siv 2 (warm); √siḷ (whistle); √siṃs (hope, wish); √siṅgh (sniff, smell); √snih (love, be moist); √su 1 (hear); √su 2 (flow); √su 3 (extract, distil); √su 4 (generate, beget); √subh (shine, adorn); √suc 1 (grieve); √suc 2 (be pure, be bright); √sudh (be pure); √sukh (please, be comfortable); √sumbh (throw, strike); √sup (lie down, sleep); √sur (shine, be supreme); √sus (dry, wither); √sā (complete, accomplish); √sād (taste, relish); √sādh (accomplish); √sās (order, instruct); √sāy (taste); √sī (lie, sleep); √sīl (conduct oneself); √sūc (indicate); √sūd (set in order); √tacch (cut, chop); √tajj (frighten, threaten); √takk (think); √tal (support, rest on); √tam (faint); √tan (stretch, extend); √tand (be slow, be lazy); √tap (burn, radiate heat); √tapp 1 (regret); √tapp 2 (satisfy); √tar 1 (cross); √tar 2 (hurry); √tas 1 (tremble, fear); √tas 2 (thirst); √tas 3 (decorate, impale); √taḷ (beat); √thak (close); √thal (be firm); √tham (hang); √thambh (support, be stiff); √than (roar, thunder); √thar (spread, expand); √then (steal); √thom (praise); √thu 1 (moan, groan); √thu 2 (be familiar, praise); √thu 3 (praise); √thī (stiffen, be compact); √thūl (be fat, be coarse); √tij 1 (be sharp, be hot); √tij 2 (be sharp, be bitter); √tij 3 (endure); √tim (be wet); √tir (cross); √tis (satisfy); √tras (fear, shake); √tud (prick, stab); √tul (weigh); √tur 1 (hurt, be sick); √tur 2 (hurry, be quick); √tus (be content, be pleased); √tuvaṭṭ (lie down); √tuḍ (prick, stab); √tā (protect, preserve); √tīr (investigate, complete); √tūl (be light); √uc (comfort); √ud (be wet); √udrabh (eat); √uj (be straight); √ujjh (leave, discard); √ukkh (sprinkle, pour); √us (be hot); √usūy (be irritated, be jealous); √uñch (glean); √vac (say, speak); √vad 1 (say, speak); √vad 2 (salute, praise); √vaddh (grow, increase); √vadh (hurt, slaughter); √vagg (dance, jump); √vah (carry, bring); √vaj (go on); √vajj (turn, avoid); √val (turn); √vall (turn); √vam (eject, vomit); √vambh (despise); √van (like, desire); √vand (bow, honour); √vap (sow, shave); √var 1 (cover, dress, restrain); √var 2 (wish, choose); √vas 1 (live); √vas 2 (wear, dress); √vas 3 (want, control); √vass 1 (rain); √vass 2 (howl, roar, bark); √vat (be, proceed); √vatt (be, proceed); √vañc 1 (be bent, deceive); √vañc 2 (go around); √vaḍḍh (grow, increase); √vaḷañj (use); √vaṇ (injure, wound); √vaṇṇ (praise); √vaṭ (divide); √vaṭṭ (turn); √ve (weave); √vedh (shake, fear); √vell (shake, sway, curl); √veṭh (wind, twist); √vhe (call, name); √vi (weave); √vic (separate); √vid 1 (know, sense, feel); √vid 2 (know); √vid 3 (feel, like); √vid 4 (get, find); √vid 5 (know, understand); √vid 6 (be found, exist); √vidh (throw, pierce); √vij (shake, be afraid, be in awe); √vis 1 (enter); √vis 2 (be active, serve); √vu (weave, cover); √vyadh (strike, pierce); √vyath (fear, shake); √vā (blow, emit odour); √vās (perfume); √vī (go); √vīj (fan); √vīr (be heroic, be hostile); √yaj (honour, sacrifice); √yakkh (worship); √yam 1 (control, strive, end); √yam 2 (support, stretch); √yant (bind); √yas (strive, struggle); √yat 1 (arrange, hand over); √yat 2 (stretch, strive); √yu (unite, fasten); √yudh (fight); √yuj (yoke, join); √yā (go); √yāc (beg); √yūh (carry, bring); √ñā (know); √ādā (take, seize); √āgam (wait); √āp (be wet); √ās (sit); √īh (strive); √īr 1 (move, shake); √īr 2 (speak); √īs (have power); √ḍah (burn); √ḍaṃs (bite, sting); √ḍi 1 (fly); √ḍi 2 (trap); √ṭaṅk (seal, cover); √ṭhubh (spit); √ṭhā (stand)

````

## G: vīraka — gold ['vīraka'], leaked in related: none

old prompt 6098 chars (~1524 tokens), new prompt 28318 chars (~7079 tokens), of which word part 3201 chars

````text
---
# The word
Book: Jātaka (verse)
Word in the text: vīraka

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: 107. Api vīraka passesi, sakuṇaṃ mañjubhāṇakaṃ;
   English: “O Viraka, have you seen the bird, the sweet-voiced one,

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "tatha 1", "lemma_2": "tatha", "pos": "adj", "grammar": "adj, from tathā", "meaning_2": "true; real; actual", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "tathā", "construction": "tathā + a", "stem": "tath", "pattern": "a adj"}
{"lemma_1": "tatha 2", "lemma_2": "tathaṃ", "pos": "nt", "grammar": "nt, from tathā", "meaning_2": "truth; actuality", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "tathā", "construction": "tathā + a", "stem": "tath", "pattern": "a nt"}
{"lemma_1": "tatha 3", "lemma_2": "tatho", "pos": "masc", "grammar": "masc, from tathā", "meaning_2": "name of a privately awakened Buddha; lit. truth", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "tathā", "construction": "tathā + a", "stem": "tath", "pattern": "a masc"}
{"lemma_1": "anurūpa", "lemma_2": "anurūpa", "pos": "adj", "grammar": "adj", "meaning_2": "conforming (to); suitable (for); proper (for); in accordance (with); lit. following form", "root_key": "√rūp", "root_sign": "*e", "root_base": "", "family_root": "anu √rūp", "family_compound": "anurūpa", "construction": "anu + √rūp + a", "stem": "anurūp", "pattern": "a adj"}
{"lemma_1": "anurūpaṃ", "lemma_2": "anurūpaṃ", "pos": "ind", "grammar": "ind, adv, acc sg of anurūpa", "meaning_2": "suitably, accordingly", "root_key": "√rūp", "root_sign": "*e", "root_base": "", "family_root": "anu √rūp", "family_compound": "", "construction": "anu + √rūp + a + aṃ\nanurūpa + aṃ", "stem": "-", "pattern": ""}
{"lemma_1": "eva 1", "lemma_2": "eva", "pos": "ind", "grammar": "ind, emph", "meaning_2": "only; just; merely; exclusively", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "eva", "construction": "", "stem": "-", "pattern": ""}
{"lemma_1": "eva 2", "lemma_2": "eva", "pos": "ind", "grammar": "ind", "meaning_2": "still", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "eva", "construction": "", "stem": "-", "pattern": ""}
{"lemma_1": "eva 3", "lemma_2": "eva", "pos": "ind", "grammar": "ind, adv", "meaning_2": "even; too; as well", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "eva", "construction": "", "stem": "-", "pattern": ""}
{"lemma_1": "eva 4", "lemma_2": "eva", "pos": "ind", "grammar": "ind, emph", "meaning_2": "indeed; really; certainly; absolutely", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "eva", "construction": "eva", "stem": "-", "pattern": ""}
{"lemma_1": "eva 5", "lemma_2": "eva", "pos": "ind", "grammar": "ind, emph", "meaning_2": "as soon as", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "eva", "construction": "", "stem": "-", "pattern": ""}
````

## G: jhāpaye — gold ['jhāpayati'], leaked in related: none

old prompt 4887 chars (~1221 tokens), new prompt 27064 chars (~6766 tokens), of which word part 1947 chars

````text
---
# The word
Book: Cariyāpiṭaka (verse)
Word in the text: jhāpaye

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: Icchamāno cahaṃ tattha, nāsāvātena jhāpaye.
   English: had I wished, right there I could have burnt it up with a blast from my nose.

## Pali English Ultimate (PEU) entries
A guide to the split and the gender, not a source. Part of its English is machine translated. Gender codes: pu = masc, na = nt, thī = fem, ti = adj.
- jhāpaye: [ capra + ṇaya + eyraṃ ] (1) should be abandoned, ought to be renounced, worthy of abandoning (2) should be cremated, ought to be burnt

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "jhā", "lemma_2": "jhā", "pos": "imp", "grammar": "imp 2nd sg of jhāyati, irreg form of jhāya", "meaning_2": "meditate!; contemplate!", "root_key": "√jhā", "root_sign": "ya", "root_base": "", "family_root": "√jhā", "family_compound": "", "construction": "√jhā + ya > jhā", "stem": "!jhāy", "pattern": "ati pr"}
{"lemma_1": "payas 1", "lemma_2": "payo", "pos": "masc", "grammar": "masc, mano group", "meaning_2": "milk; lit. drink", "root_key": "√pā 1", "root_sign": "a", "root_base": "", "family_root": "√pā", "family_compound": "", "construction": "√pā + [y] + as", "stem": "pay", "pattern": "as masc"}
{"lemma_1": "payas 2", "lemma_2": "payas", "pos": "masc", "grammar": "masc, mano group", "meaning_2": "bovine colostrum; early milk; lit. drink", "root_key": "√pā 1", "root_sign": "a", "root_base": "", "family_root": "√pā", "family_compound": "payas", "construction": "√pā + [y] + as", "stem": "pay", "pattern": "as masc"}
{"lemma_1": "payāti", "lemma_2": "payāti", "pos": "pr", "grammar": "pr", "meaning_2": "goes forward, sets out, proceeds", "root_key": "√yā", "root_sign": "a", "root_base": "√yā + a > yā", "family_root": "pa √yā", "family_compound": "", "construction": "pa + yā + ti", "stem": "pay", "pattern": "āti pr"}
````

## G: dharaṇīruhaṃ — gold ['dharaṇīruha 1', 'dharaṇīruha 2'], leaked in related: none

old prompt 5187 chars (~1296 tokens), new prompt 27339 chars (~6834 tokens), of which word part 2222 chars

````text
---
# The word
Book: Cariyāpiṭaka (verse)
Word in the text: dharaṇīruhaṃ

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: vātova dharaṇīruhaṃ’. 
   English: like the wind a feeble tree.’ 
2. Pāḷi: Rammā cāvesi maṃ ṭhānā, vātova dharaṇīruhaṃ ’.
   English: You send me from this lovely place, like the wind a tree growing in the earth.’

## Pali English Ultimate (PEU) entries
A guide to the split and the gender, not a source. Part of its English is machine translated. Gender codes: pu = masc, na = nt, thī = fem, ti = adj.
- dharaṇīruha: [Dharaṇi+ruha] Growing on the ground.

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "dharaṇī", "lemma_2": "dharaṇī", "pos": "fem", "grammar": "fem, from dharaṇa", "meaning_2": "earth; world; lit. carrier", "root_key": "√dhar 1", "root_sign": "a", "root_base": "", "family_root": "√dhar", "family_compound": "dharaṇa", "construction": "√dhar + aṇa + ī\ndharaṇa + ī", "stem": "dharaṇ", "pattern": "ī fem"}
{"lemma_1": "ruha", "lemma_2": "ruha", "pos": "adj", "grammar": "adj, in comps, from rūhati", "meaning_2": "growing; growing in; growing on; lit. ascending", "root_key": "√ruh", "root_sign": "a", "root_base": "", "family_root": "√ruh", "family_compound": "", "construction": "√ruh + a", "stem": "ruh", "pattern": "a adj"}
{"lemma_1": "dhi 2.1", "lemma_2": "dhi", "pos": "masc", "grammar": "masc, in comps, from dahati", "meaning_2": "container; receptacle; place for", "root_key": "√dhā", "root_sign": "a", "root_base": "", "family_root": "√dhā", "family_compound": "dhi2", "construction": "√dhā + i", "stem": "dh", "pattern": "i masc"}
{"lemma_1": "araṇi", "lemma_2": "araṇi", "pos": "fem", "grammar": "fem", "meaning_2": "fire stick; rubbing stick", "root_key": "√ar", "root_sign": "a", "root_base": "", "family_root": "√ar", "family_compound": "", "construction": "√ar + aṇi", "stem": "araṇ", "pattern": "i fem"}
{"lemma_1": "araṇī", "lemma_2": "araṇī", "pos": "fem", "grammar": "fem", "meaning_2": "fire stick; rubbing stick", "root_key": "√ar", "root_sign": "a", "root_base": "", "family_root": "√ar", "family_compound": "", "construction": "√ar + aṇi", "stem": "araṇ", "pattern": "ī fem"}
````

## K: revatīvimānaṃ

old prompt 5009 chars (~1252 tokens), new prompt 27076 chars (~6769 tokens), of which word part 1959 chars

````text
---
# The word
Book: Vimānavatthu (verse)
Word in the text: revatīvimānaṃ

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: Revatīvimānaṃ dutiyaṃ.
   English: The Mansion Story of Revati, the Second.

## Pali English Ultimate (PEU) entries
A guide to the split and the gender, not a source. Part of its English is machine translated. Gender codes: pu = masc, na = nt, thī = fem, ti = adj.
- revatīvimāna: [Revatī+vimāna] (na) The temple of Revatī' husband (The rich man, Nandiya).

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "revatī", "lemma_2": "revatī", "pos": "fem", "grammar": "fem, from revata", "meaning_2": "name of a woman in a Vimānavatthu story", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "", "construction": "revata + ī", "stem": "revat", "pattern": "ī fem"}
{"lemma_1": "vimāna 1.1", "lemma_2": "vimāno", "pos": "masc", "grammar": "masc, from vimāneti", "meaning_2": "disrespect; disdain; contempt; lit. causing to think apart", "root_key": "√man", "root_sign": "*e", "root_base": "√man + *e > māne (caus)", "family_root": "vi √man", "family_compound": "vimāna", "construction": "vi + māne + a", "stem": "vimān", "pattern": "a masc"}
{"lemma_1": "vimāna 1.2", "lemma_2": "vimānaṃ", "pos": "nt", "grammar": "nt, from māna", "meaning_2": "conceit; self-measurement; (comm) conceit or rebirth; lit. causing to think apart", "root_key": "√man", "root_sign": "*e", "root_base": "√man + *e > māne (caus)", "family_root": "vi √man", "family_compound": "", "construction": "vi + māne + a", "stem": "vimān", "pattern": "a nt"}
{"lemma_1": "vimāna 2.1", "lemma_2": "vimānaṃ", "pos": "nt", "grammar": "nt", "meaning_2": "mansion; palace; lit. measuring", "root_key": "√mā", "root_sign": "nā", "root_base": "", "family_root": "vi √mā", "family_compound": "", "construction": "vi + √mā + ana", "stem": "vimān", "pattern": "a nt"}
````

## K: jinapabhuttamaṃ

old prompt 7506 chars (~1876 tokens), new prompt 30360 chars (~7590 tokens), of which word part 5243 chars

````text
---
# The word
Book: Buddhavaṃsa (verse)
Word in the text: jinapabhuttamaṃ

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: Sabbāpi tā hatā honti, patvā jinapabhuttamaṃ.
   English: all of them are overcome, having reached the supreme radiance of the Conqueror.

## Pali English Ultimate (PEU) entries
A guide to the split and the gender, not a source. Part of its English is machine translated. Gender codes: pu = masc, na = nt, thī = fem, ti = adj.
- jinapabhuttama: [Jina+pabhuttama] Divine radiance of the Buddha.

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "jina 1", "lemma_2": "jino", "pos": "masc", "grammar": "masc, pp of jināti", "meaning_2": "conqueror; victor; champion; epithet of the Buddha", "root_key": "√ji 2", "root_sign": "nā", "root_base": "", "family_root": "√ji", "family_compound": "", "construction": "√ji + na", "stem": "jin", "pattern": "a masc"}
{"lemma_1": "jina 2", "lemma_2": "jina", "pos": "pp", "grammar": "pp of jināti, in comps", "meaning_2": "who has conquered; who has overcome; lit. won", "root_key": "√ji 2", "root_sign": "nā", "root_base": "", "family_root": "√ji", "family_compound": "", "construction": "√ji + na", "stem": "jin", "pattern": "a pp"}
{"lemma_1": "jina 3", "lemma_2": "jino", "pos": "masc", "grammar": "masc, pp of jināti", "meaning_2": "loser; lit. defeated", "root_key": "√ji 2", "root_sign": "nā", "root_base": "", "family_root": "√ji", "family_compound": "", "construction": "√ji + na", "stem": "jin", "pattern": "a masc"}
{"lemma_1": "jinanta", "lemma_2": "jinanta", "pos": "prp", "grammar": "prp of jināti", "meaning_2": "conquering, subduing", "root_key": "√ji 2", "root_sign": "nā", "root_base": "√ji + nā > jinā", "family_root": "√ji", "family_compound": "", "construction": "jinā +", "stem": "jin", "pattern": "anta prp"}
{"lemma_1": "jināti 1", "lemma_2": "jināti", "pos": "pr", "grammar": "pr", "meaning_2": "conquers; overcomes; defeats", "root_key": "√ji 2", "root_sign": "nā", "root_base": "√ji + nā > jinā", "family_root": "√ji", "family_compound": "", "construction": "jinā + ti", "stem": "jin", "pattern": "āti pr"}
{"lemma_1": "jināti 2", "lemma_2": "jināti", "pos": "pr", "grammar": "pr", "meaning_2": "surpasses; beats; wins (over)", "root_key": "√ji 2", "root_sign": "nā", "root_base": "√ji + nā > jinā", "family_root": "√ji", "family_compound": "", "construction": "jinā + ti", "stem": "jin", "pattern": "āti pr"}
{"lemma_1": "jini", "lemma_2": "jini", "pos": "aor", "grammar": "aor of jināti", "meaning_2": "won; was victorious", "root_key": "√ji 2", "root_sign": "nā", "root_base": "√ji + nā > jinā", "family_root": "√ji", "family_compound": "", "construction": "jinā + i", "stem": "jin", "pattern": "i aor"}
{"lemma_1": "jināti 3", "lemma_2": "jināti", "pos": "pr", "grammar": "pr", "meaning_2": "wins; is victorious", "root_key": "√ji 2", "root_sign": "nā", "root_base": "√ji + nā > jinā", "family_root": "√ji", "family_compound": "", "construction": "jinā + ti", "stem": "jin", "pattern": "āti pr"}
{"lemma_1": "pabha", "lemma_2": "pabha", "pos": "adj", "grammar": "adj, in comps, from pabhāti", "meaning_2": "radiant; shining; luminous", "root_key": "√bhā", "root_sign": "a", "root_base": "", "family_root": "pa √bhā", "family_compound": "pabhā", "construction": "pa + √bhā + ā + a\npabhā + a", "stem": "pabh", "pattern": "a adj"}
{"lemma_1": "pabhā", "lemma_2": "pabhā", "pos": "fem", "grammar": "fem, from pabhāti", "meaning_2": "light; radiance; splendour", "root_key": "√bhā", "root_sign": "a", "root_base": "", "family_root": "pa √bhā", "family_compound": "", "construction": "pa + √bhā + ā", "stem": "pabh", "pattern": "ā fem"}
{"lemma_1": "uttama 1", "lemma_2": "uttama", "pos": "adj", "grammar": "adj, superl of ud", "meaning_2": "best; highest; ultimate; supreme; top", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "uttama", "construction": "ud + tama", "stem": "uttam", "pattern": "a adj"}
{"lemma_1": "uttama 3", "lemma_2": "uttama", "pos": "adj", "grammar": "adj, compar of ud", "meaning_2": "(gram) 1st (person); I; we; lit. last", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "uttama", "construction": "ud + tama", "stem": "uttam", "pattern": "a adj"}
{"lemma_1": "uttamā 1", "lemma_2": "uttamā", "pos": "fem", "grammar": "fem, from uttama", "meaning_2": "name of an arahant nun; lit. highest", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "uttamā", "construction": "ud + tama + ā\nuttama + ā", "stem": "uttam", "pattern": "ā fem"}
{"lemma_1": "uttamā 2", "lemma_2": "uttamā", "pos": "fem", "grammar": "fem, from uttama", "meaning_2": "name of an arahant nun; lit. highest", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "uttamā", "construction": "ud + tama + ā\nuttama + ā", "stem": "uttam", "pattern": "ā fem"}
{"lemma_1": "uttama 2", "lemma_2": "uttama", "pos": "adj", "grammar": "adj, superl of ud", "meaning_2": "first", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "uttama", "construction": "ud + tama", "stem": "uttam", "pattern": "a adj"}
````

## K: kapirājacariyā

old prompt 6471 chars (~1617 tokens), new prompt 28717 chars (~7179 tokens), of which word part 3600 chars

````text
---
# The word
Book: Cariyāpiṭaka (verse)
Word in the text: kapirājacariyā

## Sentences
The English may be a machine translation. Trust the Pāḷi.
1. Pāḷi: 7. Kapirājacariyā
   English: 7. The Conduct of the Monkey King

## Related dictionary entries
Real DPD entries for parts of the word. Copy their style.
{"lemma_1": "kapi", "lemma_2": "kapi", "pos": "masc", "grammar": "masc", "meaning_2": "monkey", "root_key": "", "root_sign": "", "root_base": "", "family_root": "", "family_compound": "", "construction": "", "stem": "kap", "pattern": "i masc"}
{"lemma_1": "rāja 1", "lemma_2": "rājā", "pos": "masc", "grammar": "masc, atta group", "meaning_2": "king; sovereign; lord; ruler", "root_key": "√rāj", "root_sign": "a", "root_base": "", "family_root": "√rāj", "family_compound": "", "construction": "√rāj + a", "stem": "*", "pattern": "rāja masc"}
{"lemma_1": "rāja 2", "lemma_2": "rāja", "pos": "adj", "grammar": "adj, in comps, from rājā", "meaning_2": "royal", "root_key": "√rāj", "root_sign": "a", "root_base": "", "family_root": "√rāj", "family_compound": "rāja", "construction": "√rāj + a + a\nrāja + a", "stem": "rāj", "pattern": "a adj"}
{"lemma_1": "rājati", "lemma_2": "rājati", "pos": "pr", "grammar": "pr", "meaning_2": "shines", "root_key": "√rāj", "root_sign": "a", "root_base": "√rāj + a > rāja", "family_root": "√rāj", "family_compound": "", "construction": "rāja +", "stem": "rāj", "pattern": "ati pr"}
{"lemma_1": "rāji 2.1", "lemma_2": "rāji", "pos": "aor", "grammar": "aor of rājati", "meaning_2": "shone", "root_key": "√rāj", "root_sign": "a", "root_base": "", "family_root": "√rāj", "family_compound": "", "construction": "√rāj +", "stem": "rāj", "pattern": "i aor"}
{"lemma_1": "rāja 3", "lemma_2": "rājo", "pos": "masc", "grammar": "masc, atta group", "meaning_2": "name of a daemon; lit. king", "root_key": "√rāj", "root_sign": "a", "root_base": "", "family_root": "√rāj", "family_compound": "", "construction": "√rāj + a", "stem": "*", "pattern": "rāja masc"}
{"lemma_1": "cariya", "lemma_2": "cariyaṃ", "pos": "nt", "grammar": "nt, in comps, from carati", "meaning_2": "conduct; behaviour; way of behaving; state of life", "root_key": "√car 2", "root_sign": "a", "root_base": "", "family_root": "√car", "family_compound": "cariyā", "construction": "√car + iya", "stem": "cariy", "pattern": "a nt"}
{"lemma_1": "cariyā 1.1", "lemma_2": "cariyā", "pos": "fem", "grammar": "fem, in comps, from carati", "meaning_2": "conduct; behaviour; way of behaving; state of being", "root_key": "√car 2", "root_sign": "a", "root_base": "", "family_root": "√car", "family_compound": "cariyā", "construction": "√car + iyā", "stem": "cariy", "pattern": "ā fem"}
{"lemma_1": "cariyā 2.1", "lemma_2": "cariyā", "pos": "fem", "grammar": "fem, abstr, from carati", "meaning_2": "roaming about; wandering", "root_key": "√car 1", "root_sign": "a", "root_base": "", "family_root": "√car", "family_compound": "cariyā", "construction": "√car + iyā", "stem": "cariy", "pattern": "ā fem"}
{"lemma_1": "cariyā 1.2", "lemma_2": "cariyā", "pos": "fem", "grammar": "fem, in comps, from carati", "meaning_2": "performance; act; undergoing (of)", "root_key": "√car 2", "root_sign": "a", "root_base": "", "family_root": "√car", "family_compound": "cariyā", "construction": "√car + iyā", "stem": "cariy", "pattern": "ā fem"}
{"lemma_1": "arāja", "lemma_2": "arāja", "pos": "masc", "grammar": "masc", "meaning_2": "not a king; not a ruler", "root_key": "√rāj", "root_sign": "", "root_base": "", "family_root": "√rāj", "family_compound": "", "construction": "na > a + rājan", "stem": "a", "pattern": "rāja masc"}
````
