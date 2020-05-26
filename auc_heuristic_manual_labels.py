import os
import numpy as np

BASE = './results'

models = ['reside_original', 'pcnnatt_original', 'pcnn_original', 'cnnatt_original', 'cnn_original', 'bgwa_original']

rankings_original = {}
rankings_real = {}

models_output = []
with open('results/AUCs_orig.txt', 'w+') as writer_h,open('results/AUCs_manual.txt', 'w+') as writer_manuals:
    writer_manuals.write("{},{}\n".format("model", "AUC"))
    writer_h.write("{},{}\n".format("model", "AUC"))
    for model in models:
        precs = []
        recalls = []
        f1s = []
        aucs = []
        precs_orig = []
        recalls_orig = []
        f1s_orig = []
        aucs_orig = []
        for i in range(42):
            file_orig = ''
            file = ''
            area_original = 0
            area_real = 0
            #Creando los arreglos
            if i not in rankings_original:
                rankings_original[i] = []
                rankings_real[i] = []
            #Si es la iteracion 0 no tiene numero
            if i == 0:
                file_orig = os.path.join(BASE, model, 'True_final_values.txt')
                file = os.path.join(BASE, model, 'False_final_values.txt')
            else:
                file_orig = os.path.join(BASE, model + '_' + str(i), 'True_final_values.txt')
                file = os.path.join(BASE, model + '_' + str(i), 'False_final_values.txt')
            try:
                with open(file, 'r') as reader:
                    metrics = reader.readlines()[0].strip().split('|')
                    prec = float(metrics[0].split('Prec:')[1])
                    rec = float(metrics[1].split('Rec:')[1])
                    f1 = float(metrics[2].split('F1:')[1])
                    area_real = float(metrics[3].split('Area:')[1])
                precs.append(prec)
                recalls.append(rec)
                f1s.append(f1)
                aucs.append(area_real)
            except:
                print("Error 1")
            try:
                with open(file_orig, 'r') as reader:
                    metrics = reader.readlines()[0].strip().split('|')
                    prec = float(metrics[0].split('Prec:')[1])
                    rec = float(metrics[1].split('Rec:')[1])
                    f1 = float(metrics[2].split('F1:')[1])
                    area_original = float(metrics[3].split('Area:')[1])
                precs_orig.append(prec)
                recalls_orig.append(rec)
                f1s_orig.append(f1)
                aucs_orig.append(area_original)
            except:
                print("Error 2")
            models_output.append([model, area_original, area_real])
            rankings_original[i].append([model,area_original])
            rankings_real[i].append([model,area_real])
        print(len(precs_orig), len(precs))
        print(len(f1s_orig), len(f1s))

        for value in aucs_orig:
            writer_h.write("{},{}\n".format(model.split('_')[0].upper(),value))

        for value in aucs:
            writer_manuals.write("{},{}\n".format(model.split('_')[0].upper(),value))
        print(
            'Model {} --- AUC --> Cleaned: {:.3}+-{:.3}   Original: {:.3}+-{:.3}'.format(model, np.mean(aucs), np.std(aucs),
                                                                                         np.mean(aucs_orig),
                                                                                         np.std(aucs_orig)))

models = ['reside_original', 'pcnnatt_original', 'pcnn_original', 'cnnatt_original', 'cnn_original', 'bgwa_original']
rankings_ord_original = {}
rankings_ord_real = {}

for i,values in rankings_original.items():
    aux = sorted(values, key=lambda x: -x[1])
    ordered = []
    for model in models:
        for j,x in enumerate(aux):
            if model==x[0]:
                break
        ordered.append(j+1)
    rankings_ord_original[i]=ordered

for i,values in rankings_real.items():
    aux = sorted(values, key=lambda x: -x[1])
    ordered = []
    for model in models:
        for j,x in enumerate(aux):
            if model==x[0]:
                break
        ordered.append(j+1)
    rankings_ord_real[i]=ordered

out = ''

for key,values_orig in rankings_ord_original.items():
    for i,value_orig in enumerate(values_orig):
       out+='{},{},'.format(value_orig,rankings_ord_real[key][i])
print(len(out.split(',')))
print(out)
