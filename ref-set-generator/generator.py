# This script generates the initial reference sets (before swapping) based on:
# 1) q-gram alphabet - decided by if the q-grams should include letters, integers, and special characters
# 2) q-gram length
# 3) k, the number of reference sets in which each q-gram must occur
# 4) length of each reference set
#
# Last modified: 2025-03-20

import string
import itertools
import random
import sys
import csv


def process_boolean_input(input_val):
    if int(input_val) == 1:
        return True
    else:
        return False


def q_gram_generator(q, does_take_ltr, does_take_dig, does_take_sc):
    # Generate the complete set of unique q-grams based on the input flags
    # for letters, digits, and special characters

    alphabet = ''
    if does_take_ltr:
        alphabet += string.ascii_lowercase  # a-z
    if does_take_dig:
        alphabet += string.digits  # 0-9
    if does_take_sc:
        alphabet += string.punctuation  # Special characters like !, @, #

    print("Length of alphabet is %d" % len(alphabet))

    q_grams = [''.join(comb) for comb in itertools.product(alphabet, repeat=q)]

    print("Generated %d q-grams" % len(q_grams))
    return q_grams


def check_q_gram_availability(q_gram_counter, k):
    for key, value in q_gram_counter.items():
        if key < k and len(value) > 0:
            return False
    return True


def update_q_gram_counter(q_gram_counter, q_grams, key):
    next_key = key + 1
    for q_gram in q_grams:
        q_gram_counter[key].remove(q_gram)
        if len(q_gram_counter[key]) == 0:
            del q_gram_counter[key]
        if next_key not in q_gram_counter:
            q_gram_counter[next_key] = []
        q_gram_counter[next_key].append(q_gram)
    return q_gram_counter


def ref_set_generator(r_length, q_c, random_seed, k):
    random.seed(random_seed)
    ref_sets = []
    q_gram_counter = {}

    for i in range(k + 1):
        if i == 0:
            q_gram_counter[i] = q_c
        else:
            q_gram_counter[i] = []

    while not check_q_gram_availability(q_gram_counter, k):
        counter_key = min(q_gram_counter.keys())
        q_grams_in_smallest_key = list(q_gram_counter[counter_key])
        did_generate_successfully = False
        try_counter = 0

        while not did_generate_successfully:
            try_counter += 1
            if len(q_grams_in_smallest_key) >= r_length:
                if len(q_grams_in_smallest_key) == r_length and try_counter > 1:
                    q_gram_from_smallest_key = random.sample(q_grams_in_smallest_key, k=1)
                    if r_length - 1 != 0 and len(q_gram_counter[counter_key + 1]) >= r_length - 1:
                        next_filler_key = counter_key + 1
                        q_grams_in_next_key = q_gram_counter[next_filler_key]
                        q_grams_from_next_key = random.sample(q_grams_in_next_key, k=(r_length - 1))
                        qs_r = set(q_gram_from_smallest_key + q_grams_from_next_key)
                        if qs_r not in ref_sets:
                            ref_sets.append(qs_r)
                            did_generate_successfully = True
                            q_gram_counter = update_q_gram_counter(q_gram_counter, q_gram_from_smallest_key.copy(),
                                                                   counter_key)
                            q_gram_counter = update_q_gram_counter(q_gram_counter, q_grams_from_next_key.copy(),
                                                                   next_filler_key)
                else:
                    random_q_grams = random.sample(q_grams_in_smallest_key.copy(), k=r_length)
                    # converting to a set in a separate step to ensure order of q-grams added to the counter,
                    # for reproducibility
                    qs_r = set(random_q_grams)
                    if qs_r not in ref_sets:
                        ref_sets.append(qs_r)
                        did_generate_successfully = True
                        q_gram_counter = update_q_gram_counter(q_gram_counter, random_q_grams, counter_key)
            else:
                slack_elements = r_length - len(q_grams_in_smallest_key)
                next_filler_key = counter_key + 1
                q_grams_in_next_key = q_gram_counter[next_filler_key]
                if len(q_grams_in_next_key) >= slack_elements:
                    q_grams_from_next_key = random.sample(q_grams_in_next_key, k=slack_elements)
                    qs_r = set(q_grams_in_smallest_key + q_grams_from_next_key)
                    if qs_r not in ref_sets:
                        ref_sets.append(qs_r)
                        did_generate_successfully = True
                        q_gram_counter = update_q_gram_counter(q_gram_counter, q_grams_in_smallest_key.copy(),
                                                               counter_key)
                        q_gram_counter = update_q_gram_counter(q_gram_counter, q_grams_from_next_key.copy(),
                                                               next_filler_key)
            if did_generate_successfully:
                assert len(qs_r) == r_length

    if (k + 1) in q_gram_counter:
        print("Elements in the k+1 key are: ", q_gram_counter[k + 1])
    return ref_sets


# This program takes in the following command line arguments:
# 1. The random seed value
# 2. Flag for if the q-grams should include letters (1 for True, 0 for False)
# 3. Flag for if the q-grams should include integers (1 for True, 0 for False)
# 4. Flag for if the q-grams should include special characters (1 for True, 0 for False)
# 5. Length of q-grams to be generated
# 6. Value of k, determining the number of reference sets in which each q-gram must occur
# 7. Length of each reference set
# 8. The output file name to which the reference sets will be written

if __name__ == "__main__":
    random_seed_val = str(sys.argv[1])
    print("Random seed value is %s" % random_seed_val)
    include_letters = process_boolean_input(sys.argv[2])
    include_digits = process_boolean_input(sys.argv[3])
    include_sc = process_boolean_input(sys.argv[4])
    q_gram_length = int(sys.argv[5])
    k = int(sys.argv[6])
    l_r = int(sys.argv[7])
    output_file_path = sys.argv[8]

    q_common = q_gram_generator(q_gram_length, include_letters, include_digits, include_sc)
    ref_set_col = ref_set_generator(l_r, q_common, random_seed_val, k)

    with open(output_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(ref_set_col)
