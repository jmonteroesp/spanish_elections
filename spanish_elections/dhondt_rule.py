import pdb
import pandas as pd


def argmax_dict(d):
    return sorted(d, key=lambda x: -d[x])[0]


def dhondt_rule(results: dict, n_seats) -> dict:
    '''
    results is a dictionary with the name of the parties as keys and
    the number of votes as values
    seats is a dictionary with the same keys as results and the
    number of seats as values

    Current implementation does not account for draws
    '''
    n_seats_remaining = n_seats
    seats = {party: 0 for party in results}
    transformed_results = results.copy()  # to modify using allocated seats
    while n_seats_remaining:
        most_voted_party = argmax_dict(transformed_results)
        seats[most_voted_party] += 1
        n_seats_remaining -= 1
        ratio_seats = seats[most_voted_party]/(1 + seats[most_voted_party])
        transformed_results[most_voted_party] *= ratio_seats
    return seats


def dhondt_rule_long_single_province(results: pd.DataFrame,
                                     n_seats: 'number of seats to allocate'=None,
                                     party_col='party',
                                     votes_col='votes',
                                     seats_col='seats',
                                     total_seats_col='total_seats',
                                     inplace=False) -> pd.DataFrame:
    '''
    Arguments:
    - results is a pd.DataFrame with a column with the name of the political
    parties and another column with votes for each party
    - n_seats is the number of total seats corresponding to this province. if None,
    method expects that results has a column named `total_seats_col` with an
    unique value, the total number of seats

    Outputs:
    - results with additional column with number of seats allocated to each
    political party, named `seats_col`
    '''
    if n_seats is None and total_seats_col not in results.columns:
        raise(ValueError('If n_seats is None, method requires that'
                         ' total number of seats is specified as a column with name'
                         ' `total_seats_col`(by default, "total_seats"'))
    elif n_seats is None and total_seats_col in results.columns:
        total_seats = results[total_seats_col].unique()
        if len(total_seats) > 1:
            raise(ValueError('there are more than one value in column `total_seats_col`.'
                             'There should only be one value of `total_seats_col` per province.'))
        n_seats = total_seats[0]
    if not inplace:
        results = results.copy()
    # set political party as index of DataFrame
    results.set_index(party_col, inplace=True)
    n_seats_remaining = n_seats
    results[seats_col] = 0
    # transformed_results is an auxiliary pandas Series with the votes taken
    # into account at each step
    transformed_results = results[votes_col].copy()
    while n_seats_remaining:
        most_voted_party = transformed_results.idxmax()
        # add seat to most voted party
        results.loc[most_voted_party, seats_col] += 1
        n_seats_remaining -= 1
        # apply new number of seats to transformed results
        seats_most_voted_party = results.loc[most_voted_party,
                                             seats_col]
        ratio_seats = seats_most_voted_party/(1 + seats_most_voted_party)
        transformed_results.loc[most_voted_party] *= ratio_seats
    results.reset_index(inplace=True)
    if not inplace:
        return results


def dhondt_rule_long(results: pd.DataFrame,
                     n_seats: dict,
                     province_col='province',
                     party_col='party',
                     votes_col='votes',
                     seats_col='seats') -> pd.DataFrame:
    '''
    Runs `dhondt_rule_long_single province` for each province in results dataframe.

    Never works in place.
    '''
    results = results.copy()
    results['total_seats'] = results[province_col].map(n_seats)
    results = \
    results.groupby(province_col).apply(dhondt_rule_long_single_province,
                                        party_col=party_col,
                                        votes_col=votes_col,
                                        seats_col=seats_col,
                                        total_seats_col='total_seats',
                                        inplace=False)
    return results.reset_index(drop=True)


dict_version = False
long_version_single_province = False
long_version = True
if __name__ == '__main__' and dict_version:
    results = {'PSOE': 15000,
               'PP': 20000,
                'Cs': 7500,
                'Podemos': 5500}
    seats = dhondt_rule(results, 7)
    pdb.set_trace()

if __name__ == '__main__' and long_version_single_province:
    results = pd.DataFrame({'political_parties': ['Podemos', 'PSOE', 'Cs'],
                            'votes': [10000, 7500, 2000]})
    dhondt_rule_long_single_province(results, n_seats=3,
                                     party_col='political_parties',
                                     seats_col='seats',
                                     inplace=True)
    # without n_seats
    results2 = pd.DataFrame({'political_parties': ['Podemos', 'PSOE', 'Cs'],
                            'votes': [10000, 7500, 2000],
                            'total_seats': 4})
    results2_with_seats = \
    dhondt_rule_long_single_province(results2,
                                    party_col='political_parties',
                                    seats_col='seats')
    pdb.set_trace()


if __name__ == '__main__' and long_version:
    out_dir = '../data/output/'
    general_data = pd.read_pickle(out_dir + 'general_data.pkl')
    results = pd.read_pickle(out_dir + 'results_by_province.pkl')
    votos = results[results.result == 'votos']
    n_seats = pd.Series(general_data.diputados.values,
                        index=general_data.provincia).to_dict()
    results_with_seats = \
    dhondt_rule_long(votos, n_seats, province_col='provincia',
                     party_col='party', votes_col='value',
                     seats_col='seats')
    pdb.set_trace()
