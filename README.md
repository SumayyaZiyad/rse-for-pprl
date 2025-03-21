# rse-for-pprl
This repository contains the implementation of the novel Reference Set based Encoding (RSE) technique proposed for PPRL, alongside the anonymised data sets used for evaluation. This work has been submitted to the journal of Information Systems and is currently under review.

* The `data` directory contains the sets of q-grams used in our experimental setups, for all data sets and attribute combinations. Please note that the entity IDs have been anonymised for privacy reasons.
* The `ref-set-generator` directory contains the script to generate the initial set of references (independent of the data sets to be encoded - requiring only the alphabet, `k`, and the length of the sets to be generated).
* The `encoder` directory contains the script that encodes the q-gram sets to bit arrays, alongside the `ref_set_processor.py` script that processes the initial reference sets using frequency-based q-gram swapping.
