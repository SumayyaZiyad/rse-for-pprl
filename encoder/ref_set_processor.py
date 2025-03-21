# This script post-processes the initial reference sets using frequency-based q-gram swapping
#
# Last modified: 21st March 2025

import time
import csv

RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ = "random_q_gram_set_with_freq"
RANDOM_SET_ONLY_ATTR = "random_set_only"
WEIGHTED_SCORE_ATTR = "weighted_score"


def frequency_based_rank_swapping(weighed_random_sets):
    """Modifies the reference sets by swapping the most and least frequent q-grams of the random sets with the highest
    and lowest weighted scores (calculated using the frequencies of their containing q-grams) respectively
    input:
        weighed_random_sets: the dictionary containing the random reference sets and their frequency information

    output:
        weighed_random_sets: the dictionary containing the modified random reference sets
    """
    random_sets = {tuple(item[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ]) for item in weighed_random_sets.values()}
    swaps_tracker = {}
    successful_modifications = 0
    stop_processing = False

    while not stop_processing:
        min_key, min_set = min(weighed_random_sets.items(), key=lambda x: (x[1][WEIGHTED_SCORE_ATTR], x[0]))
        max_key, max_set = max(weighed_random_sets.items(), key=lambda x: (x[1][WEIGHTED_SCORE_ATTR], x[0]))

        sorted_max_set = sorted(max_set[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ], key=lambda x: (x[1], x[0]), reverse=True)
        sorted_min_set = sorted(min_set[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ], key=lambda x: (x[1], x[0]))

        while True:
            successfully_swapped = False
            min_element_index = 0
            for min_element in sorted_min_set:
                if min_element not in sorted_max_set:
                    max_element_index = 0
                    for max_element in sorted_max_set:
                        if max_element not in sorted_min_set and max_element[1] > min_element[1]:
                            modified_min_value = {max_element if element == min_element else element for
                                                  element in min_set[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ]}
                            modified_max_value = {min_element if element == max_element else element for
                                                  element in max_set[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ]}
                            modified_min_value_weight = sum(x[1] for x in modified_min_value) / len(modified_min_value)
                            modified_max_value_weight = sum(x[1] for x in modified_max_value) / len(modified_max_value)
                            old_range = max_set[WEIGHTED_SCORE_ATTR] - min_set[WEIGHTED_SCORE_ATTR]
                            new_range = abs(modified_max_value_weight - modified_min_value_weight)
                            if new_range < old_range and modified_min_value not in random_sets and modified_max_value not in random_sets:
                                if min_key not in swaps_tracker:
                                    swaps_tracker[min_key] = 0
                                if max_key not in swaps_tracker:
                                    swaps_tracker[max_key] = 0
                                swaps_tracker[min_key] += 1
                                swaps_tracker[max_key] += 1

                                assert len(modified_min_value) == len(min_set[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ]), \
                                    "Length of modified ref sets are different to the original"

                                # update all attributes of the modified reference sets
                                weighed_random_sets[min_key][RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ] = modified_min_value
                                weighed_random_sets[min_key][WEIGHTED_SCORE_ATTR] = modified_min_value_weight
                                weighed_random_sets[min_key][RANDOM_SET_ONLY_ATTR] = set(
                                    [x[0] for x in modified_min_value])

                                weighed_random_sets[max_key][RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ] = modified_max_value
                                weighed_random_sets[max_key][WEIGHTED_SCORE_ATTR] = modified_max_value_weight
                                weighed_random_sets[max_key][RANDOM_SET_ONLY_ATTR] = set(
                                    [x[0] for x in modified_max_value])

                                # update flag to detect successful modification
                                successfully_swapped = True
                                successful_modifications += 1
                                break

                        max_element_index += 1
                min_element_index += 1

                if successfully_swapped or stop_processing:
                    break

            if not successfully_swapped:
                # assert that the process only quitting after all possible combinations have been tried
                assert len(sorted_max_set) == max_element_index
                assert len(sorted_min_set) == min_element_index
                print("Could not find a combination. Quitting swapping")
                stop_processing = True
            break

    print("Total number of modifications completed: %d" % successful_modifications)
    print("Unique number of random sets modified: %d" % len(swaps_tracker))
    print("Percentage of random sets modified: %f" % (len(swaps_tracker) / len(weighed_random_sets) * 100))

    return weighed_random_sets


def read_init_random_sets(random_set_file):
    random_set_dict = {}

    with open(random_set_file, mode='r') as file:
        csv_reader = csv.reader(file)

        # Iterate over each row in the csv file
        for index, row in enumerate(csv_reader):
            random_set_dict[index] = row

        print("Number of random sets read: %d" % len(random_set_dict))

    return random_set_dict


def read_q_gram_freq_info(q_gram_freq_file):
    frequent_q_gram_dict = {}

    with open(q_gram_freq_file, mode='r') as file:
        csv_reader = csv.reader(file)

        # Iterate over each row in the csv file
        for row in csv_reader:
            frequent_q_gram_dict[row[0]] = int(row[1])

        print("Number of q-grams read: %d" % len(frequent_q_gram_dict))

    return frequent_q_gram_dict


def weigh_random_sets(random_sets, q_gram_freq):
    """Weighs the random sets based on the frequency of the q-grams in the public database
    input:
        random_sets: the dictionary containing the random reference sets
        q_gram_freq: the dictionary containing the frequency of the q-grams in the public database

    return:
        weighed_random_sets: the dictionary containing the random reference sets and their weighted scores
    """
    weighed_random_sets = {}

    for index, qs_r in random_sets.items():
        qs_r_with_freq = []
        freq_sum = 0
        for q_gram in qs_r:
            if q_gram in q_gram_freq:
                qs_r_with_freq.append((q_gram, q_gram_freq[q_gram]))
                freq_sum += q_gram_freq[q_gram]
            else:
                qs_r_with_freq.append((q_gram, 1))
                freq_sum += 1

        weighed_random_sets[index] = {
            RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ: qs_r_with_freq,
            RANDOM_SET_ONLY_ATTR: set(qs_r),
            WEIGHTED_SCORE_ATTR: freq_sum / len(qs_r_with_freq)
        }

    return weighed_random_sets


class RandomQgramSetGenerator:
    def __init__(self, init_random_set_file, q_gram_freq_file, do_swap, seed):
        self.seed = seed
        self.init_random_set_file = init_random_set_file
        self.init_random_sets = read_init_random_sets(init_random_set_file)
        self.frequent_q_grams = read_q_gram_freq_info(q_gram_freq_file)
        self.do_swapping = do_swap
        self.freq_q_gram_file = q_gram_freq_file

    def generate_random_q_gram_sets(self):
        start_weighing_r = time.time()
        weighed_random_sets = weigh_random_sets(self.init_random_sets, self.frequent_q_grams)
        assert len(self.init_random_sets) == len(weighed_random_sets)
        finished_weighing_r = time.time()
        print("Time taken to weigh R: %d" % ((finished_weighing_r - start_weighing_r) * 1000))

        # Extracts the index and random set of the minimum and maximum weighted random sets
        min_key, min_value = min(weighed_random_sets.items(), key=lambda x: x[1][WEIGHTED_SCORE_ATTR])
        max_key, max_value = max(weighed_random_sets.items(), key=lambda x: x[1][WEIGHTED_SCORE_ATTR])

        print("--------------------- Initial max weight")
        print("Maximum weight of random sets: %f" % max_value[WEIGHTED_SCORE_ATTR])
        print("Elements and frequency of the maximum weighed random set: %s" % max_value[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ])

        print("--------------------- Initial min weight")
        print("Minimum weight of random sets: %f" % min_value[WEIGHTED_SCORE_ATTR])
        print("Elements and frequency of the minimum weighed random set: %s" % min_value[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ])

        if self.do_swapping:
            print("--- Beginning frequency-based swapping ----")
            qs_r_swapping_start_time = time.time()
            processed_indexed_r, successful_modifications = frequency_based_rank_swapping(weighed_random_sets)
            qs_r_swapping_end_time = time.time()

            print("Time taken for frequency based swapping is %d" % (
                    (qs_r_swapping_end_time - qs_r_swapping_start_time) * 1000))

            # Extracts the index and random set of the minimum and maximum weighted random sets
            min_key, min_value = min(processed_indexed_r.items(), key=lambda x: x[1][WEIGHTED_SCORE_ATTR])
            max_key, max_value = max(processed_indexed_r.items(), key=lambda x: x[1][WEIGHTED_SCORE_ATTR])

            print("--------------------- Maximum weight")
            print("Maximum weight of random sets: %f" % max_value[WEIGHTED_SCORE_ATTR])
            print(
                "Elements and frequency of the maximum weighed random set: %s" % max_value[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ])

            print("--------------------- Minimum weight")
            print("Minimum weight of random sets: %f" % min_value[WEIGHTED_SCORE_ATTR])
            print(
                "Elements and frequency of the minimum weighed random set: %s" % min_value[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ])
        else:
            processed_indexed_r = weighed_random_sets

        print("Total time taken to generate random q-gram sets is %d" % ((time.time() - start_weighing_r) * 1000))

        # additional assertions for the experimental setup
        for key, value in processed_indexed_r.items():
            assert all(len(item) == 2 for item in value[RANDOM_SET_ONLY_ATTR]), "Length of q-grams are not 2"
            assert len(value[RANDOM_SET_ONLY_ATTR]) == len(value[RANDOM_Q_GRAM_SET_ATTR_WITH_FREQ])
            processed_indexed_r[key] = value[RANDOM_SET_ONLY_ATTR]

        return processed_indexed_r
