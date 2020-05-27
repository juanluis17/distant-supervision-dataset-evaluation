#!/bin/bash


END=41

for i in $(seq 0 $END);
do
  echo $i
  python reside.py -data ./data/riedel_train.pkl -name reside_original_$i
  python pcnnatt.py -data ./data/riedel_train.pkl -name pcnnatt_original_$i -attn
  python pcnnatt.py -data ./data/riedel_train.pkl -name pcnn_original_$i
  python cnnatt.py -data ./data/riedel_train.pkl -name cnnatt_original_$i -attn
  python cnnatt.py -data ./data/riedel_train.pkl -name cnn_original_$i
  python bgwa.py -data ./data/riedel_train.pkl -name bgwa_original_$i
done
