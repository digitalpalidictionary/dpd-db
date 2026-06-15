def find_context(text, word, context_length=50):
    # Find the position of the word
    position = text.find(word)
    if position == -1:
        return "Word not found in text."

    # Calculate start and end indices
    start = max(0, position - context_length)
    end = min(len(text), position + len(word) + context_length)

    # Slice the string
    context = text[start:end]

    return context


# Example usage
text = "vītisāretvā ekamantaṃ nisīdi. ekamantaṃ nisinno kho, ānanda, ghaṭikāro kumbhakāro kassapaṃ bhagavantaṃ arahantaṃ sammāsambuddhaṃ etadavoca – ‘ayaṃ me, bhante, jotipālo māṇavo sahāyo piyasahāyo. imassa bhagavā dhammaṃ desetū’ti. atha kho, ānanda, kassapo bhagavā arahaṃ sammāsambuddho ghaṭikārañca kumbhakāraṃ jotipālañca māṇavaṃ dhammiyā kathāya sandassesi samādapesi samuttejesi sampahaṃsesi. atha kho, ānanda, ghaṭikāro ca kumbhakāro jotipālo ca māṇavo kassapena bhagavatā arahatā sammāsambuddhena dhammiyā kathāya sandassitā samādapitā samuttejitā sampahaṃsitā kassapassa bhagavato arahato sammāsambuddhassa bhāsitaṃ abhinanditvā anumoditvā uṭṭhāyāsanā kassapaṃ bhagavantaṃ arahantaṃ sammāsambuddhaṃ abhivādetvā padakkhiṇaṃ katvā pakkamiṃsu."
word = "ekamantaṃ"
context = find_context(text, word)
print(context)
