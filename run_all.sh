#!/bin/bash


END=41

for i in $(seq 0 $END);
do
  echo $i
  python reside.py -data ./data/riedel_original.pkl -name reside_original_$i
  python pcnnatt.py -data ./data/riedel_original.pkl -name pcnnatt_original_$i -attn
  python pcnnatt.py -data ./data/riedel_original.pkl -name pcnn_original_$i
  python cnnatt.py -data ./data/riedel_original.pkl -name cnnatt_original_$i -attn
  python cnnatt.py -data ./data/riedel_original.pkl -name cnn_original_$i
  python bgwa.py -data ./data/riedel_original.pkl -name bgwa_original_$i
done
