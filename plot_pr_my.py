import numpy as np, argparse, pickle
import matplotlib;
import os

data={}

matplotlib.use('agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score, auc
import pdb


def loadData(path):
    preds = pickle.load(open(path, 'rb'))
    y_hot = np.array(preds['y_hot'])
    logit_list = np.array(preds['logit_list'])
    y_hot_new = np.reshape(np.array([x[1:] for x in y_hot]), (-1))
    logit_list_new = np.reshape(np.array([x[1:] for x in logit_list]), (-1))
    return y_hot_new, logit_list_new


def plotPR(model, original=True):
    global  data
    y_true, y_scores = loadData('./results/{}/{}_precision_recall.pkl'.format(model, original))
    precision, recall, threshold = precision_recall_curve(y_true, y_scores)
    area_under = auc(x=recall, y=precision)
    print('Area under the curve: {} ---> {:.3}'.format(model,area_under))
    label = '{}: {:.3}'.format(model.split('_')[0],area_under)
    data[model] = [area_under,precision,recall]
    #plt.plot(recall[:], precision[:], label=label, color=color, lw=1, markevery=0.1, ms=6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-original', default='pretrained_reside')
    args = parser.parse_args()
    plt.ylim([0.0, 1.01])
    plt.xlim([0.0, 1.01])
    BASE_DIR = './results'
    color = ['purple', 'darkorange', 'green', 'xkcd:azure', 'orchid', 'cornflowerblue', 'blue', 'yellow']

    directory = os.fsencode(BASE_DIR)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        #if index >= len(color):
        #    index = 0
        if 'original_' not in filename:
            plotPR(model=filename, original=args.original)#, color=color[index])
        #    index += 1
    data = {k: v for k, v in sorted(data.items(), key=lambda item: -item[1][0])}

    index = 0
    for key,value in data.items():
        if index >= len(color):
            index = 0
        label = '{}: {:.3}'.format(key.split('_')[0], value[0])
        recall = value[2]
        precision = value[1]
        plt.plot(recall[:], precision[:], label=label, color=color[index], lw=1, markevery=0.1, ms=6)
        index+=1

    plt.xlabel('Recall', fontsize=14)
    plt.ylabel('Precision', fontsize=14)
    plt.legend(loc="upper right", prop={'size': 12})
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    plot_path = './{}_plot_pr.png'.format(args.original)
    plt.savefig(plot_path)
    print('Precision-Recall plot saved at: {}'.format(plot_path))
