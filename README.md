##A critical look of the evaluation measures for Distant Supervision in Relation Extraction


Source code for paper: [A critical look of the evaluation measures for Distant Supervision in Relation Extraction]. The code is based on that developed by [Vashishth _et. al._ (2018)](https://github.com/malllabiisc/RESIDE). Includes implementation of [RESIDE](http://aclweb.org/anthology/D18-1157), [PCNN](http://www.emnlp2015.org/proceedings/EMNLP/pdf/EMNLP203.pdf), [PCNN+ATT](https://www.aclweb.org/anthology/P16-1200), [CNN](https://www.aclweb.org/anthology/C14-1220), CNN+ATT, and [BGWA](https://arxiv.org/pdf/1804.06987.pdf) models.

### Dependencies

- Compatible with TensorFlow 1.x and Python 3.6
- Dependencies can be installed using `requirements.txt`.

### Dataset:

- We use [Riedel NYT](http://iesl.cs.umass.edu/riedel/ecml/) for train models. To evaluate the models during training, [Riedel NYT's](http://iesl.cs.umass.edu/riedel/ecml/) test partition was used, removing 324 instances. 
 
 -We built an test partition by selecting 324 instances of partition [Riedel NYT's](http://iesl.cs.umass.edu/riedel/ecml/) test partition. These instances have two labels, the ones generated by the distant supervision heuristic and the other generated by manual revision.  

- The processed version of the datasets can be downloaded from [RiedelNYT](https://drive.google.com/file/d/1UD86c_6O_NSBn2DYirk6ygaHy_fTL-hN/view?usp=sharing) and [GIDS](https://drive.google.com/file/d/1UMS4EmWv5SWXfaSl_ZC4DcT3dk3JyHeq/view?usp=sharing). The structure of the processed input data is as follows.

  ```java
  {
      "voc2id":   {"w1": 0, "w2": 1, ...},
      "type2id":  {"type1": 0, "type2": 1 ...},
      "rel2id":   {"NA": 0, "/location/neighborhood/neighborhood_of": 1, ...}
      "max_pos": 123,
      "train": [
          {
              "X":        [[s1_w1, s1_w2, ...], [s2_w1, s2_w2, ...], ...],
              "Y":        [bag_label],
              "Pos1":     [[s1_p1_1, sent1_p1_2, ...], [s2_p1_1, s2_p1_2, ...], ...],
              "Pos2":     [[s1_p2_1, sent1_p2_2, ...], [s2_p2_1, s2_p2_2, ...], ...],
              "SubPos":   [s1_sub, s2_sub, ...],
              "ObjPos":   [s1_obj, s2_obj, ...],
              "SubType":  [s1_subType, s2_subType, ...],
              "ObjType":  [s1_objType, s2_objType, ...],
              "ProbY":    [[s1_rel_alias1, s1_rel_alias2, ...], [s2_rel_alias1, ... ], ...]
              "DepEdges": [[s1_dep_edges], [s2_dep_edges] ...]
          },
          {}, ...
      ],
      "test":  { same as "train"},
      "valid": { same as "train"},
  }
  ```

  * `voc2id` is the mapping of word to its id
  * `type2id` is the maping of entity type to its id.
  * `rel2id` is the mapping of relation to its id. 
  * `max_pos` is the maximum position to consider for positional embeddings.
  * Each entry of `train`, `test` and `valid` is a bag of sentences, where
    * `X` denotes the sentences in bag as the list of list of word indices.
    * `Y` is the relation expressed by the sentences in the bag.
    * `Pos1` and `Pos2` are position of each word in sentences wrt to target entity 1 and entity 2.
    * `SubPos` and `ObjPos` contains the position of the target entity 1 and entity 2 in each sentence.
    * `SubType` and `ObjType` contains the target entity 1 and entity 2 type information obtained from KG.
    * `ProbY` is the relation alias side information (refer paper) for the bag.
    * `DepEdges` is the edgelist of dependency parse for each sentence (required for GCN).

### Training from scratch:
- Execute `setup.sh` for downloading GloVe embeddings.
- For training **RESIDE** run:
  ```shell
  python reside.py -data data/riedel_processed.pkl -name new_run
  ```

* The above model needs to be further trained with SGD optimizer for few epochs to match the performance reported in the paper. For that execute

  ```shell
  python reside.py -name new_run -restore -opt sgd -lr 0.001 -l2 0.0 -epoch 4
  ```

* Finally, run `python plot_pr.py -name new_run` to get the plot.

### Baselines:

* The repository also includes code for [PCNN](http://www.emnlp2015.org/proceedings/EMNLP/pdf/EMNLP203.pdf), [PCNN+ATT](https://www.aclweb.org/anthology/P16-1200), [CNN](https://www.aclweb.org/anthology/C14-1220), CNN+ATT, [BGWA](https://arxiv.org/pdf/1804.06987.pdf) models.

* For training **PCNN+ATT**:

  ```shell
  python pcnnatt.py -data data/riedel_processed.pkl -name new_run -attn # remove -attn for PCNN
  ```
 

* Similarly for training **CNN+ATT**:

  ```shell
  python cnnatt.py -data data/riedel_processed.pkl -name new_run # remove -attn for CNN
  ```

* For training **BGWA**:

  ```shell
  python bgwa.py -data data/riedel_processed.pkl -name new_run
  ```

For any clarification, comments, or suggestions please create an issue or contact [juanluis@inaoep.mx](https://github.com/juanluis17).
