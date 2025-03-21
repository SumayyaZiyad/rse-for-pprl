# This script performs the encoding of two data sets using the RSE protocol.
# It takes the following as input:
# 1. secret seed for PRNG
# 2. file path to the first database
# 3. sensitive attributes to be encoded from the first database
# 4. file path to the second database
# 5. sensitive attributes to be encoded from the second database
# 6. k - the number of reference sets in which each q-gram must occur
# 7. path to the initial set of references (as generated using the ref-set-generator directory)
# 8. True/False flag to indicate if frequency-based swapping must be performed on the reference sets
# 9. path to the q-gram frequency information extracted from the public database
#       expectations: a CSV file with two columns: q-gram and frequency


# Last modified: 21st March 2025

import csv
import gzip
import sys
import time

import bitarray

import random_qgram_generator

Q_GRAM_ATTR = "record_q_gram"
SIGNATURE_ATTR = "signature"


def generate_database_q_gram_sets(file_name, id_column, sensitive_attrs, q):
    """Load the data set and generate the record q-gram sets for the sensitive attributes.
    The q-gram sets are stored in a dictionary with record identifiers (detected using the id_column parameter) as keys.

     Parameter Description:
       file_name      : file path of the database to be read (CSV or CSV.GZ file)
       rec_id_col     : record identifier column of the data file
       sens_attr_list : list of attributes to extract q-grams from
       q              : length of the q-grams to generate

     returns:
       qs_dict        : dictionary containing the record q-gram sets
       headers_used   : names of sensitive attributes used, to ensure that the same attributes are compared for both datasets
    """

    # Open a CSV for Gzipped (compressed) CSV.GZ file
    if file_name.endswith('gz'):
        in_f = gzip.open(file_name, 'rt', encoding="utf8")
    else:
        in_f = open(file_name, encoding="utf8")

    csv_reader = csv.reader(in_f)  # returns iterator where each iteration is a line of the input file

    print('Load data set from file: ' + file_name)

    headers_used = []

    header_list = next(csv_reader)
    print('  Record identifier attribute: ' + str(header_list[id_column]))

    print('  Sensitive attributes to use:')
    for attr_num in sensitive_attrs:
        print('    ' + header_list[attr_num])
        headers_used.append(header_list[attr_num])

    rec_num = 0
    qs_dict = {}

    # Iterate through the records in the file
    for rec_list in csv_reader:
        # Get the record identifier
        rec_id = rec_list[id_column].strip().lower()  # strips the value and transforms to lowercase to get key
        qs = set()

        missing_val = False

        # Generate the q-gram set using the sensitive attributes
        for attr_id in range(len(rec_list)):
            if attr_id in sensitive_attrs:
                if (rec_list[attr_id]).strip() == "":
                    missing_val = True
                    break

                attr_val = rec_list[attr_id].strip().lower().replace(' ', '') # strips the value,
                                                                       # converts to lowercase, and removes whitespaces
                attr_q_gram_set = set([attr_val[i:i + q] for i in range(len(attr_val) - (q - 1))])
                qs = qs.union(attr_q_gram_set)

        if missing_val:
            # skip if any of the sensitive attributes are missing
            continue
        elif len(qs) == 0:
            # skip if the generated q-gram set has no elements
            continue

        qs_dict[rec_id] = {
            Q_GRAM_ATTR: qs
        }

    in_f.close()

    print("Generated %d record q-gram sets from the %s file" % (len(qs_dict), file_name))
    if rec_num > len(qs_dict):
        print("Warning: %d duplicate records were detected" % (rec_num - len(qs_dict)))

    return qs_dict, headers_used


def calculate_average_len(record_q_gram_sets):
    """Calculate the average length of the q-gram sets generated for the records.

     Parameter Description:
       record_q_gram_sets           : list of q-gram sets generated for the records

     returns:
        shortest_record_q_gram_set  : length of the shortest record q-gram set
        avg_len                     : average length of all record q-gram sets
    """

    shortest_record_q_gram_set = min(record_q_gram_sets, key=len)
    print("Length of shortest record q-gram set is %d" % len(shortest_record_q_gram_set))
    print("The shortest q-gram set is: %s" % shortest_record_q_gram_set)

    longest_record_q_gram_set = max(record_q_gram_sets, key=len)
    print("Length of longest record q-gram set is %d" % len(longest_record_q_gram_set))

    lengths = [len(i) for i in record_q_gram_sets]
    return len(shortest_record_q_gram_set), 0 if len(lengths) == 0 else round(sum(lengths) / len(lengths))


def q_gram_jacc_sim(q_gram_set1, q_gram_set2):
      """Calculate the Jaccard similarity between the two given sets of q-grams.

         Jaccard similarity is calculated between two sets A and B as

            Jaccard similarity (A,B) = |A intersection B|
                                       ------------------
                                          | A union B|

         Returns a similarity value between 0 and 1.
      """

      q_gram_intersection_set = q_gram_set1 & q_gram_set2
      q_gram_union_set =        q_gram_set1 | q_gram_set2

      jacc_sim = float(len(q_gram_intersection_set)) / len(q_gram_union_set)

      assert 0 <= jacc_sim <= 1.0

      return jacc_sim


def gen_init_int_signature(record_store, indexed_r, init_sign_length):
    """ For each record q-gram set, calculates the similarity against every random set, then extracts the initial
    integer signature

     Parameter Description:
       record_store     : dictionary containing the record q-gram sets
       indexed_r        : dictionary containing the indexed reference q-gram sets
       init_sign_length : length of the initial integer signature

     returns:
        min_1_bits      : minimum number of ref sets that every record has a non-zero similarity with
        record_store    : updated record store with initial integer signature
    """

    for rec_id, rec_obj in record_store.items():
        record_sim_store = {}  # stores the similarity calculated against each random set
        non_zero_count_per_record = 0  # counts the random sets that the record has a non-zero similarity with
        for qs_r_index, qs_r in indexed_r.items():
            if qs_r.intersection(rec_obj[Q_GRAM_ATTR]):  # checks if there is an intersection, otherwise sim == 0
                non_zero_count_per_record += 1
                record_sim_store[qs_r_index] = q_gram_jacc_sim(rec_obj[Q_GRAM_ATTR], qs_r)

        sorted_sim_store = sorted(record_sim_store.items(), key=lambda item: item[1], reverse=True)

        # Updates the record dictionary with the similarities against random sets
        record_store[rec_id] = {
            Q_GRAM_ATTR: rec_obj[Q_GRAM_ATTR],
            SIGNATURE_ATTR: sorted_sim_store[:min(init_sign_length, non_zero_count_per_record)]
        }

    min_1_bits = min(len(rec[SIGNATURE_ATTR]) for rec in record_store.values())
    return min_1_bits, record_store


def generate_bit_array_signature(bit_array_length, positions):
    """ Generates the bit array signature by setting all bits corresponding to the reference sets in the integer
        signature to 1
        Parameter Description:
            bit_array_length: the length of the bit array signature to be generated
            positions       : the bit positions (corresponding to the indices of the similar reference sets) to set to 1

        return:
            encoded_ba      : the bit array generated
    """
    encoded_ba = bitarray.bitarray(bit_array_length)
    encoded_ba.setall(0)

    for pos in positions:
        assert 0 <= pos < bit_array_length
        encoded_ba[pos] = 1

    return encoded_ba


def extract_signatures(indexed_ref_sets, record_store, n1_bits):
    """ For each record q-gram set, extracts the indices of the k-most similar random sets and generates the bit array

     Parameter Description:
       indexed_ref_sets : dictionary containing the indexed reference sets
       record_store     : dictionary containing the initial integer signatures generated
       n1_bits          : number of 1-bits to be set in the bit array

     returns
       record_store  : the updated record dictionary with the generated bit array encodings
    """

    qs_r_count = len(indexed_ref_sets)

    for rec_id, rec_obj in record_store.items():
        record_sim_store = rec_obj[SIGNATURE_ATTR]
        assert len(record_sim_store) >= n1_bits
        qs_r_signature = [qs_r[0] for qs_r in record_sim_store[:n1_bits]]
        signature = generate_bit_array_signature(qs_r_count, qs_r_signature)

        # Updates the record dictionary with the signature
        record_store[rec_id] = {
            Q_GRAM_ATTR: rec_obj[Q_GRAM_ATTR],
            SIGNATURE_ATTR: signature
        }

    return record_store


if __name__ == '__main__':
    q = 2
    id_col = 0

    seed = sys.argv[1]
    input_file_1 = sys.argv[2]
    sens_attr_list_1 = sys.argv[3]
    sens_attr_list_1 = [int(i) for i in sens_attr_list_1.split(",")]

    input_file_2 = sys.argv[4]
    sens_attr_list_2 = sys.argv[5]
    sens_attr_list_2 = [int(i) for i in sens_attr_list_2.split(",")]

    k = int(sys.argv[6])

    init_ref_set_file = sys.argv[7]
    must_swap = eval(sys.argv[8])
    q_gram_frequency_file = sys.argv[9]

    start_time = time.time()

    # read data files and generate q-gram sets
    data_dic1, headers1 = generate_database_q_gram_sets(input_file_1, id_col, sens_attr_list_1, q)
    data_dic2, headers2 = generate_database_q_gram_sets(input_file_2, id_col, sens_attr_list_2, q)

    assert headers1 == headers2, "The sensitive attributes of the two data files are not the same"

    gt_tm_count = len(set(data_dic1.keys()) & set(data_dic2.keys()))
    print("Number of true matches in the ground truth: %d" % gt_tm_count)

    finished_qs_gen = time.time()
    print("Time taken to read the data file and generate q-gram sets is %d" % (
            (finished_qs_gen - start_time) * 1000))

    db1_qs = [item[Q_GRAM_ATTR] for item in data_dic1.values()]
    db2_qs = [item[Q_GRAM_ATTR] for item in data_dic2.values()]

    min_q_gram_length, avg_q_gram_length = calculate_average_len(db1_qs + db2_qs)
    print("Average length of the database q-gram sets is: %d" % avg_q_gram_length)

    RANDOM_GENERATOR = random_qgram_generator.RandomQgramSetGenerator(init_ref_set_file, q_gram_frequency_file,
                                                                      must_swap, seed)

    reference_q_gram_sets = RANDOM_GENERATOR.generate_random_q_gram_sets()
    print("Generated %d reference q-gram sets" % len(reference_q_gram_sets))

    signature_gen_start = time.time()
    initial_ls = (k + 1) * min_q_gram_length

    input1_smallest_k, record_store1 = gen_init_int_signature(data_dic1, reference_q_gram_sets, initial_ls)
    input2_smallest_k, record_store2 = gen_init_int_signature(data_dic2, reference_q_gram_sets, initial_ls)

    num_1_bits = min(input1_smallest_k, input2_smallest_k)
    print("Number of 1-bits to set is %d" % num_1_bits)

    print("======= Encoding dataset a =======")
    processed_records_1, zero_f_qs_r_1 = extract_signatures(reference_q_gram_sets, record_store1, num_1_bits)

    print("======= Encoding dataset b =======")
    processed_records_2, zero_f_qs_r_2 = extract_signatures(reference_q_gram_sets, record_store2, num_1_bits)
