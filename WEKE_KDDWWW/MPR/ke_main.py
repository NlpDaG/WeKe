# coding:utf-8
from ke_preprocess import filter_text, normalized_token, read_file
from weighted_pagerank import wpr
from ke_postprocess import get_phrases
import csv
import sys
import os

csv.field_size_limit(sys.maxsize)


def read_sg(path, standard=True):
    """
    read vec: word, 1, 3, 4, ....
    return word:[1,...] dict
    """
    vec_dict = {}
    with open(path, encoding='utf-8') as file:
        # 标准csv使用','隔开，有的文件使用空格，所以要改变reader中的delimiter参数
        if standard:
            table = csv.reader(file)
        else:
            table = csv.reader(file, delimiter=' ')
        for row in table:
            try:
                vec_dict[normalized_token(row[0])] = list(
                    float(i) for i in row[1:])
            except:
                continue
    return vec_dict


def evaluate_extraction(dataset, method_name, ngrams=2, damping=0.85, omega=None, phi=None,
                        alter_topn=None, alter_edge=None, alter_node=None):
    """
    评价实验结果

    omega,phi, [0]代表不适用任何特征，权重设置为1。None为所有特征的简单加和。[-1]只用最后一个特征。
    """
    if dataset == 'KDD':
        abstr_dir = 'data/KDD/abstracts/'
        out_dir = 'result/'
        gold_dir = 'data/KDD/gold/'
        edge_dir = 'data/KDD/edge_features/'
        node_dir = 'data/KDD/node_features/'
        file_names = read_file('./data/KDD/abstract_list').split(',')
        topn = 4
    elif dataset == 'WWW':
        abstr_dir = 'data/WWW/abstracts/'
        out_dir = 'result/'
        gold_dir = 'data/WWW/gold/'
        edge_dir = 'data/WWW/edge_features/'
        node_dir = 'data/WWW/node_features/'
        file_names = read_file('data/WWW/abstract_list').split(',')
        topn = 5
    else:
        print('wrong dataset name')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if alter_edge:
        edge_dir = alter_edge
    if alter_node:
        node_dir = alter_node
    if alter_topn:
        topn = alter_topn

    count = 0
    gold_count = 0
    extract_count = 0
    mrr = 0
    prcs_micro = 0
    recall_micro = 0

    for file_name in file_names:
        pr, graph = wpr(edge_dir + file_name, node_dir +
                        file_name, omega=omega, phi=phi, d=damping)

        gold = read_file(gold_dir + file_name)
        pl2 = 0.62
        pl3 = 0.3
        if dataset == "WWW":
            pl2 = 0.55
        keyphrases = get_phrases(pr, graph, abstr_dir,
                                 file_name, ng=ngrams, pl2=pl2, pl3=pl3)
        top_phrases = []
        for phrase in keyphrases:
            if phrase[0] not in str(top_phrases):
                top_phrases.append(phrase[0])
            if len(top_phrases) == topn:
                break
        golds = gold.split('\n')
        if golds[-1] == '':
            golds = golds[:-1]
        golds = list(' '.join(list(normalized_token(w)
                                   for w in g.split())) for g in golds)
        count_micro = 0
        position = []
        for phrase in top_phrases:
            if phrase in golds:
                count += 1
                count_micro += 1
                position.append(top_phrases.index(phrase))
        if position != []:
            mrr += 1 / (position[0] + 1)
        gold_count += len(golds)
        extract_count += len(top_phrases)
        if len(top_phrases) != 0:
            prcs_micro += count_micro / len(top_phrases)
        recall_micro += count_micro / len(golds)
        # 记录每个文档关键词提取的详细结果
        # prcs_single = count_micro / len(top_phrases)
        # recall_single = count_micro / len(golds)
        # output_single = str(file_name) + ',' + str(prcs_single) + ',' + str(recall_single) + ','\
        #               + ','.join(phrase for phrase in top_phrases) + '\n'
        # with open(out_dir + dataset + 'DETAILS.csv', mode='a', encoding='utf8') as f:
        #     f.write(output_single)
    prcs = count / extract_count
    recall = count / gold_count
    f1 = 2 * prcs * recall / (prcs + recall)
    mrr /= len(file_names)
    prcs_micro /= len(file_names)
    recall_micro /= len(file_names)
    f1_micro = 2 * prcs_micro * recall_micro / (prcs_micro + recall_micro)
    print(prcs, recall, f1, mrr)

    tofile_result = method_name + ',' + \
        str(prcs) + ',' + str(recall) + ',' + str(f1) + ',' + str(mrr) + '\n'
    with open(out_dir + dataset + ".result", mode='a', encoding='utf8') as f:
        f.write(tofile_result)
