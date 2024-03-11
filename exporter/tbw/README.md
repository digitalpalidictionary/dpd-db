# tbw
Prototype Pāḷi word lookup system to integrate a lite version of DPD into websites.
- [The Buddha's Words](https://thebuddhaswords.net/home/index.html)
- [DhammaGift](https://find.dhamma.gift/)
- [Sutta Cental](https://suttacentral.net/ )


## Flowchart
Here's a visual representation of how the system works. 

![flowchart](https://github.com/digitalpalidictionary/dpd-db/blob/main/exporter/tbw/docs/dpd%20lookup%20systen.png)

## Examples

the word clicked on is **buddhena**

1. lookup word in dpd_i2h.json
2. the results are ["buddha 1", "buddha 2"]
3. lookup those headwords in dpd_ebts.json
4. lookup word in dpd_deconstructor.json
5. display all the results with your preferred styling

the word clicked on is **akatañca**

1. lookup word in dpd_i2h.json
2. it's not found there
3. then lookup word in dpd_deconstructor.json
4. display those results
