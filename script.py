import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def loadNamesData():
    years = range(1880, 2011)
    pieces = []
    columns = ['name', 'sex', 'births']
    
    for year in years:
        path = 'names/yob%d.txt' % year
        frame = pd.read_csv(path, names=columns)
        
        frame['year'] = year
        pieces.append(frame)
    
    return pd.concat(pieces, ignore_index=True)

names = loadNamesData()
total_births = names.pivot_table('births', rows='year', cols='sex', aggfunc=sum)

# Plot total births
total_births.plot(title = 'Total births by sex and year')

def add_prop(group):
    births = group.births.astype(float)
    group['prop'] = births / births.sum()
    return group

names = names.groupby(['year', 'sex']).apply(add_prop)

def get_top1000(group):
    return group.sort_index(by='births', ascending=False)[:1000]


grouped = names.groupby(['year', 'sex'])
top1000 = grouped.apply(get_top1000)
total_births = top1000.pivot_table('births', rows='year', cols='name', aggfunc=sum)
subset = total_births[['John', 'Harry', 'Mary', 'Marilyn']]
subset.plot(subplots=True, figsize=(12,20), grid=False, title = "Number of births per year")

table = top1000.pivot_table('prop', rows = 'year', cols = 'sex', aggfunc=sum)
table.plot(title = 'Sum of table1000.prop by year and sex', 
    yticks=np.linspace(0, 1.2, 13), xticks=range(1880, 2020, 10))

boys = top1000[top1000.sex == 'M']
girls = top1000[top1000.sex == 'F']
df = boys[boys.year == 2010]
prop_cumsum = df.sort_index(by='prop', ascending=False).prop.cumsum()
print("Number of names to accumulate 50%% in 2010 is %d" % prop_cumsum.searchsorted(0.5))
df1880 = boys[boys.year == 1880]
prop_cumsum = df1880.sort_index(by='prop', ascending=False).prop.cumsum()
print("Number of names to accumulate 50%% in 1880 is %d" % prop_cumsum.searchsorted(0.5))


def get_quantile_count(group, q=0.5):
    group = group.sort_index(by='prop', ascending=False)
    return group.prop.cumsum().searchsorted(q) + 1


diversity = top1000.groupby(['year', 'sex']).apply(get_quantile_count).unstack('sex')
diversity.plot(title = "Number of popular names in top 50%")

get_last_letter = lambda x: x[-1]
last_letters = names.name.map(get_last_letter)
last_letters.name = 'last_letter'

table = names.pivot_table('births', rows=last_letters, cols=['sex', 'year'], aggfunc=sum)
subtable = table.reindex(columns=[1910, 1960, 2010], level='year')

letter_prop = subtable / subtable.sum().astype(float)
fig, axes = plt.subplots(2, 1, figsize=(10, 8))
letter_prop['M'].plot(kind='bar', rot=0, ax=axes[0], title='Male')
letter_prop['F'].plot(kind='bar', rot=0, ax=axes[1], title='Female', legend=False)
plt.show()


