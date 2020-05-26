#!/bin/bash

END=42
python reside.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name reside_original -restore -only_eval
python reside.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name reside_original -restore -only_eval -original
for i in $(seq 1 $END);
do
echo $i
python reside.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name reside_original_$i -restore -only_eval
python reside.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name reside_original_$i -restore -only_eval -original
done

python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name cnnatt_original -restore -only_eval -attn
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name cnnatt_original -restore -only_eval -original -attn
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name cnn_original -restore -only_eval
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name cnn_original -restore -only_eval -original
for i in $(seq 1 $END);
do
echo $i
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name cnnatt_original_$i -restore -only_eval -attn
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name cnnatt_original_$i -restore -only_eval -original -attn
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name cnn_original_$i -restore -only_eval
python cnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name cnn_original_$i -restore -only_eval -original
done

python bgwa.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name bgwa_original -restore -only_eval
python bgwa.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name bgwa_original -restore -only_eval -original
for i in $(seq 1 $END);
do
echo $i
python bgwa.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name bgwa_original_$i -restore -only_eval
python bgwa.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name bgwa_original_$i -restore -only_eval -original
done


python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name pcnnatt_original -restore -only_eval -attn
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name pcnnatt_original -restore -only_eval -original -attn
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name pcnn_original -restore -only_eval
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name pcnn_original_25 -restore -only_eval -original
for i in $(seq 1 $END);
do
echo $i
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name pcnnatt_original_$i -restore -only_eval -attn
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name pcnnatt_original_$i -restore -only_eval -original -attn
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_manually.pkl -name pcnn_original_$i -restore -only_eval
python pcnnatt.py -data data/cleaned/pkl/riedel_train_labeled_heuristic.pkl -name pcnn_original_$i -restore -only_eval -original
done

