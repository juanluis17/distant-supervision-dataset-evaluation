from base import Model
from helper import *
import tensorflow as tf

"""
Abbreviations used in variable names:
	Type:  Entity type side informatoin
	ProbY, RelAlias: Relation alias side information
Recommendation: View this file with tab size 8.
"""


class RESIDE(Model):

    def getBatches(self, data, shuffle=True):
        """
            Generates batches of multiple bags

            Parameters
            ----------
            data:		Data to be usedº for creating batches. Dataset as list of bags where each bag is a dictionary
            shuffle:	Decides whether to shuffle the data or not.

            Returns
            -------
            Generator for creating batches.
            """
        if shuffle: random.shuffle(data)

        for chunk in getChunks(data, self.p.batch_size):  # chunk = batch
            batch = ddict(list)

            num = 0
            for i, bag in enumerate(chunk):
                batch['X'] += bag['X']
                batch['Pos1'] += bag['Pos1']
                batch['Pos2'] += bag['Pos2']
                batch['DepEdges'] += bag['DepEdges']
                batch['ProbY'] += bag['ProbY']

                batch['SubType'].append(bag['SubType'])
                batch['ObjType'].append(bag['ObjType'])

                batch['Y'].append(bag['Y'])
                old_num = num
                num += len(bag['X'])

                batch['sent_num'].append([old_num, num, i])

            yield batch

    def add_placeholders(self):
        """
        Defines the placeholder required for the model
        """

        self.input_x = tf.placeholder(tf.int32, shape=[None, None], name='input_data')  # Tokens ids of sentences
        self.input_y = tf.placeholder(tf.int32, shape=[None, None], name='input_labels')  # Actual relation of the bag
        self.input_pos1 = tf.placeholder(tf.int32, shape=[None, None], name='input_pos1')  # Position ids wrt entity 1
        self.input_pos2 = tf.placeholder(tf.int32, shape=[None, None], name='input_pos2')  # Position ids wrt entity 2

        # Entity Type Side Information
        self.input_subtype = tf.placeholder(tf.int32, shape=[None, None],
                                            name='input_subtype')  # Entity type information of entity 1
        self.input_objtype = tf.placeholder(tf.int32, shape=[None, None],
                                            name='input_objtype')  # Entity type information of entity 2
        self.input_subtype_len = tf.placeholder(tf.float32, shape=[None],
                                                name='input_subtype_len')  # Max number of types of entity 1
        self.input_objtype_len = tf.placeholder(tf.float32, shape=[None],
                                                name='input_objtype_len')  # Max number of types of entity 2

        # Relation Alias Side Information
        self.input_proby_ind = tf.placeholder(tf.int32, shape=[None, None],
                                              name='input_prob_ind')  # Relation Alias information Indices
        self.input_proby_len = tf.placeholder(tf.float32, shape=[None],
                                              name='input_prob_len')  # Max number of relations per bag for the entire batch

        self.x_len = tf.placeholder(tf.int32, shape=[None], name='input_len')  # Number of words in sentences in a batch
        self.sent_num = tf.placeholder(tf.int32, shape=[None, 3],
                                       name='sent_num')  # Stores which sentences belong to which bag | [start_index, end_index, bag_number]
        self.seq_len = tf.placeholder(tf.int32, shape=(),
                                      name='seq_len')  # Max number of tokens in sentences in a batch
        self.total_bags = tf.placeholder(tf.int32, shape=(), name='total_bags')  # Total number of bags in a batch
        self.total_sents = tf.placeholder(tf.int32, shape=(),
                                          name='total_sents')  # Total number of sentences in a batch

        self.de_adj_ind = tf.placeholder(tf.int64, shape=[self.num_deLabel, None, None, 2],
                                         name='de_adj_ind')  # Dependency graph indices
        self.de_adj_data = tf.placeholder(tf.float32, shape=[self.num_deLabel, None, None],
                                          name='de_adj_data')  # Dependency graph data

        self.dropout = tf.placeholder_with_default(self.p.dropout, shape=(),
                                                   name='dropout')  # Dropout used in GCN Layer
        self.rec_dropout = tf.placeholder_with_default(self.p.rec_dropout, shape=(),
                                                       name='rec_dropout')  # Dropout used in Bi-LSTM

    def pad_dynamic(self, X, pos1, pos2, sub_type, obj_type, rel_alias):
        """
        Pads each batch during runtime.

        Parameters
        ----------
        X:		For each sentence in the bag, list of words
        pos1:		For each sentence in the bag, list position of words with respect to subject
        pos2:		For each sentence in the bag, list position of words with respect to object
        sub_type:	For each sentence in the bag, Entity type information of the subject
        obj_type:	For each sentence in the bag, Entity type information of the object
        rel_aliaes:	For each sentence in the bag, Relation Alias information

        Returns
        -------
        x_pad		Padded words
        x_len		Number of sentences in each sentence,
        pos1_pad	Padded position 1
        pos2_pad	Padded position 2
        seq_len 	Maximum sentence length in the batch
        subtype 	Padded subject entity type information
        subtype_len 	Number of entity type for each bag in the batch
        objtype 	Padded objective entity type information
        objtype_len 	Number of entity type for each bag in the batch
        rel_alias_ind 	Padded relation aliasses for each bag in the batch
        rel_alias_len	Number of relation aliases
        """
        seq_len, max_et, max_type, max_proby = 0, 0, 0, 0
        subtype_len, objtype_len, rel_alias_len = [], [], []

        x_len = np.zeros((len(X)), np.int32)

        for py in rel_alias:
            rel_alias_len.append(len(py))
            max_proby = max(max_proby, len(py))

        for typ in sub_type:
            subtype_len.append(len(typ))
            max_type = max(max_type, len(typ))

        for typ in obj_type:
            objtype_len.append(len(typ))
            max_type = max(max_type, len(typ))

        for i, x in enumerate(X):
            seq_len = max(seq_len, len(x))
            x_len[i] = len(x)

        x_pad, _ = self.padData(X, seq_len)
        pos1_pad, _ = self.padData(pos1, seq_len)
        pos2_pad, _ = self.padData(pos2, seq_len)
        subtype, _ = self.padData(sub_type, max_type)
        objtype, _ = self.padData(obj_type, max_type)
        rel_alias_ind, _ = self.padData(rel_alias, max_proby)

        return x_pad, x_len, pos1_pad, pos2_pad, seq_len, subtype, subtype_len, objtype, objtype_len, rel_alias_ind, rel_alias_len

    def create_feed_dict(self, batch, wLabels=True, split='train'):
        """
        Creates a feed dictionary for the batch

        Parameters
        ----------
        batch:		contains a batch of bags
        wLabels:	Whether batch contains labels or not
        split:		Indicates the split of the data - train/valid/test

        Returns
        -------
        feed_dict	Feed dictionary to be fed during sess.run
        """
        X, Y, pos1, pos2, sent_num, sub_type, obj_type, rel_alias = batch['X'], batch['Y'], batch['Pos1'], batch[
            'Pos2'], batch['sent_num'], batch['SubType'], batch['ObjType'], batch['ProbY']
        total_sents = len(batch['X'])
        total_bags = len(batch['Y'])
        x_pad, x_len, pos1_pad, pos2_pad, seq_len, subtype, subtype_len, objtype, objtype_len, rel_alias_ind, rel_alias_len = self.pad_dynamic(
            X, pos1, pos2, sub_type, obj_type, rel_alias)

        y_hot = self.getOneHot(Y, self.num_class)
        proby = self.getOneHot(rel_alias, self.num_class - 1, isprob=True)  # -1 because NA cannot be in proby

        feed_dict = {}
        feed_dict[self.input_x] = np.array(x_pad)
        feed_dict[self.input_pos1] = np.array(pos1_pad)
        feed_dict[self.input_pos2] = np.array(pos2_pad)
        feed_dict[self.input_subtype] = np.array(subtype)
        feed_dict[self.input_objtype] = np.array(objtype)
        feed_dict[self.x_len] = np.array(x_len)
        feed_dict[self.seq_len] = seq_len
        feed_dict[self.total_sents] = total_sents
        feed_dict[self.total_bags] = total_bags
        feed_dict[self.sent_num] = sent_num
        feed_dict[self.input_subtype_len] = np.array(subtype_len) + self.p.eps
        feed_dict[self.input_objtype_len] = np.array(objtype_len) + self.p.eps
        feed_dict[self.input_proby_ind] = np.array(rel_alias_ind)
        feed_dict[self.input_proby_len] = np.array(rel_alias_len) + self.p.eps

        if wLabels: feed_dict[self.input_y] = y_hot

        feed_dict[self.de_adj_ind], \
        feed_dict[self.de_adj_data] = self.get_adj(batch['DepEdges'], total_sents, seq_len, self.num_deLabel)

        if split != 'train':
            feed_dict[self.dropout] = 1.0
            feed_dict[self.rec_dropout] = 1.0
        else:
            feed_dict[self.dropout] = self.p.dropout
            feed_dict[self.rec_dropout] = self.p.rec_dropout

        return feed_dict

    def get_adj(self, edgeList, batch_size, max_nodes, max_labels):
        """
        Stores the adjacency matrix as indices and data for feeding to TensorFlow

        Parameters
        ----------
        edgeList:	List of list of edges
        batch_size:	Number of bags in a batch
        max_nodes:	Maximum number of nodes in the graph
        max_labels:	Maximum number of edge labels in the graph

        Returns
        -------
        adj_mat_ind 	indices of adjacency matrix
        adj_mat_data	data of adjacency matrix
        """
        max_edges = 0
        for edges in edgeList:
            max_edges = max(max_edges, len(edges))

        adj_mat_ind = np.zeros((max_labels, batch_size, max_edges, 2), np.int64)
        adj_mat_data = np.zeros((max_labels, batch_size, max_edges), np.float32)

        for lbl in range(max_labels):
            for i, edges in enumerate(edgeList):
                in_ind_temp, in_data_temp = [], []
                for j, (src, dest, _, _) in enumerate(edges):
                    adj_mat_ind[lbl, i, j] = (src, dest)
                    adj_mat_data[lbl, i, j] = 1.0

        return adj_mat_ind, adj_mat_data

    def GCNLayer(self, gcn_in, in_dim, gcn_dim, batch_size, max_nodes, max_labels, adj_ind, adj_data, w_gating=True,
                 num_layers=1, name="GCN"):
        """
        GCN Layer Implementation

        Parameters
        ----------
        gcn_in:		Input to GCN Layer
        in_dim:		Dimension of input to GCN Layer
        gcn_dim:	Hidden state dimension of GCN
        batch_size:	Batch size
        max_nodes:	Maximum number of nodes in graph
        max_labels:	Maximum number of edge labels
        adj_ind:	Adjacency matrix indices
        adj_data:	Adjacency matrix data (all 1's)
        w_gating:	Whether to include gating in GCN
        num_layers:	Number of GCN Layers
        name 		Name of the layer (used for creating variables, keep it different for different layers)

        Returns
        -------
        out		List of output of different GCN layers with first element as input itself, i.e., [gcn_in, gcn_layer1_out, gcn_layer2_out ...]
        """

        out = []
        out.append(gcn_in)

        for layer in range(num_layers):
            gcn_in = out[
                -1]  # out contains the output of all the GCN layers, intitally contains input to first GCN Layer
            if len(out) > 1: in_dim = gcn_dim  # After first iteration the in_dim = gcn_dim

            with tf.name_scope('%s-%d' % (name, layer)):
                act_sum = tf.zeros([batch_size, max_nodes, gcn_dim])
                for lbl in range(max_labels):

                    # Defining the layer and label specific parameters
                    with tf.variable_scope('label-%d_name-%s_layer-%d' % (lbl, name, layer)) as scope:
                        w_in = tf.get_variable('w_in', [in_dim, gcn_dim],
                                               initializer=tf.contrib.layers.xavier_initializer(),
                                               regularizer=self.regularizer)
                        w_out = tf.get_variable('w_out', [in_dim, gcn_dim],
                                                initializer=tf.contrib.layers.xavier_initializer(),
                                                regularizer=self.regularizer)
                        w_loop = tf.get_variable('w_loop', [in_dim, gcn_dim],
                                                 initializer=tf.contrib.layers.xavier_initializer(),
                                                 regularizer=self.regularizer)
                        b_in = tf.get_variable('b_in', initializer=np.zeros([1, gcn_dim]).astype(np.float32),
                                               regularizer=self.regularizer)
                        b_out = tf.get_variable('b_out', initializer=np.zeros([1, gcn_dim]).astype(np.float32),
                                                regularizer=self.regularizer)

                        if w_gating:
                            w_gin = tf.get_variable('w_gin', [in_dim, 1],
                                                    initializer=tf.contrib.layers.xavier_initializer(),
                                                    regularizer=self.regularizer)
                            w_gout = tf.get_variable('w_gout', [in_dim, 1],
                                                     initializer=tf.contrib.layers.xavier_initializer(),
                                                     regularizer=self.regularizer)
                            w_gloop = tf.get_variable('w_gloop', [in_dim, 1],
                                                      initializer=tf.contrib.layers.xavier_initializer(),
                                                      regularizer=self.regularizer)
                            b_gin = tf.get_variable('b_gin', initializer=np.zeros([1]).astype(np.float32),
                                                    regularizer=self.regularizer)
                            b_gout = tf.get_variable('b_gout', initializer=np.zeros([1]).astype(np.float32),
                                                     regularizer=self.regularizer)

                    # Activation from in-edges
                    with tf.name_scope('in_arcs-%s_name-%s_layer-%d' % (lbl, name, layer)):
                        inp_in = tf.tensordot(gcn_in, w_in, axes=[2, 0]) + tf.expand_dims(b_in, axis=0)

                        def map_func1(i):
                            adj_mat = tf.SparseTensor(adj_ind[lbl, i], adj_data[lbl, i],
                                                      [tf.cast(max_nodes, tf.int64), tf.cast(max_nodes, tf.int64)])
                            adj_mat = tf.sparse_transpose(adj_mat)
                            return tf.sparse_tensor_dense_matmul(adj_mat, inp_in[i])

                        in_t = tf.map_fn(map_func1, tf.range(batch_size), dtype=tf.float32)

                        if self.p.dropout != 1.0: in_t = tf.nn.dropout(in_t, keep_prob=self.p.dropout)

                        if w_gating:
                            inp_gin = tf.tensordot(gcn_in, w_gin, axes=[2, 0]) + tf.expand_dims(b_gin, axis=0)

                            def map_func2(i):
                                adj_mat = tf.SparseTensor(adj_ind[lbl, i], adj_data[lbl, i],
                                                          [tf.cast(max_nodes, tf.int64), tf.cast(max_nodes, tf.int64)])
                                adj_mat = tf.sparse_transpose(adj_mat)
                                return tf.sparse_tensor_dense_matmul(adj_mat, inp_gin[i])

                            in_gate = tf.map_fn(map_func2, tf.range(batch_size), dtype=tf.float32)
                            in_gsig = tf.sigmoid(in_gate)
                            in_act = in_t * in_gsig
                        else:
                            in_act = in_t

                    # Activation from out-edges
                    with tf.name_scope('out_arcs-%s_name-%s_layer-%d' % (lbl, name, layer)):
                        inp_out = tf.tensordot(gcn_in, w_out, axes=[2, 0]) + tf.expand_dims(b_out, axis=0)

                        def map_func3(i):
                            adj_mat = tf.SparseTensor(adj_ind[lbl, i], adj_data[lbl, i],
                                                      [tf.cast(max_nodes, tf.int64), tf.cast(max_nodes, tf.int64)])
                            return tf.sparse_tensor_dense_matmul(adj_mat, inp_out[i])

                        out_t = tf.map_fn(map_func3, tf.range(batch_size), dtype=tf.float32)
                        if self.p.dropout != 1.0: out_t = tf.nn.dropout(out_t, keep_prob=self.p.dropout)

                        if w_gating:
                            inp_gout = tf.tensordot(gcn_in, w_gout, axes=[2, 0]) + tf.expand_dims(b_gout, axis=0)

                            def map_func4(i):
                                adj_mat = tf.SparseTensor(adj_ind[lbl, i], adj_data[lbl, i],
                                                          [tf.cast(max_nodes, tf.int64), tf.cast(max_nodes, tf.int64)])
                                return tf.sparse_tensor_dense_matmul(adj_mat, inp_gout[i])

                            out_gate = tf.map_fn(map_func4, tf.range(batch_size), dtype=tf.float32)
                            out_gsig = tf.sigmoid(out_gate)
                            out_act = out_t * out_gsig
                        else:
                            out_act = out_t

                    # Activation from self-loop
                    with tf.name_scope('self_loop'):
                        inp_loop = tf.tensordot(gcn_in, w_loop, axes=[2, 0])
                        if self.p.dropout != 1.0: inp_loop = tf.nn.dropout(inp_loop, keep_prob=self.p.dropout)

                        if w_gating:
                            inp_gloop = tf.tensordot(gcn_in, w_gloop, axes=[2, 0])
                            loop_gsig = tf.sigmoid(inp_gloop)
                            loop_act = inp_loop * loop_gsig
                        else:
                            loop_act = inp_loop

                    # Aggregating activations
                    act_sum += in_act + out_act + loop_act

                gcn_out = tf.nn.relu(act_sum)
                out.append(gcn_out)

        return out

    def add_model(self):
        """
        Creates the Computational Graph

        Parameters
        ----------

        Returns
        -------
        nn_out:		Logits for each bag in the batch
        accuracy:	accuracy for the entire batch
        """

        in_wrds, in_pos1, in_pos2 = self.input_x, self.input_pos1, self.input_pos2

        with tf.variable_scope('Embeddings') as scope:
            embed_init = getEmbeddings(self.wrd_list, self.p.embed_dim, self.p.embed_loc)
            _wrd_embeddings = tf.get_variable('embeddings', initializer=embed_init, trainable=True,
                                              regularizer=self.regularizer)
            wrd_pad = tf.zeros([1, self.p.embed_dim])
            wrd_embeddings = tf.concat([wrd_pad, _wrd_embeddings], axis=0)

            pos1_embeddings = tf.get_variable('pos1_embeddings', [self.max_pos, self.p.pos_dim],
                                              initializer=tf.contrib.layers.xavier_initializer(), trainable=True,
                                              regularizer=self.regularizer)
            pos2_embeddings = tf.get_variable('pos2_embeddings', [self.max_pos, self.p.pos_dim],
                                              initializer=tf.contrib.layers.xavier_initializer(), trainable=True,
                                              regularizer=self.regularizer)

        with tf.variable_scope('AliasInfo') as scope:
            pad_alias_embed = tf.zeros([1, self.p.alias_dim], dtype=tf.float32, name='alias_pad')
            _alias_embeddings = tf.get_variable('alias_embeddings', [self.num_class - 1, self.p.alias_dim],
                                                initializer=tf.contrib.layers.xavier_initializer(), trainable=True,
                                                regularizer=self.regularizer)
            alias_embeddings = tf.concat([pad_alias_embed, _alias_embeddings], axis=0)

            alias_embed = tf.nn.embedding_lookup(alias_embeddings, self.input_proby_ind)
            alias_av = tf.divide(tf.reduce_sum(alias_embed, axis=1), tf.expand_dims(self.input_proby_len, axis=1))

        wrd_embed = tf.nn.embedding_lookup(wrd_embeddings, in_wrds)
        pos1_embed = tf.nn.embedding_lookup(pos1_embeddings, in_pos1)
        pos2_embed = tf.nn.embedding_lookup(pos2_embeddings, in_pos2)
        embeds = tf.concat([wrd_embed, pos1_embed, pos2_embed], axis=2)

        with tf.variable_scope('Bi-LSTM') as scope:
            fw_cell = tf.contrib.rnn.DropoutWrapper(tf.nn.rnn_cell.GRUCell(self.p.lstm_dim, name='FW_GRU'),
                                                    output_keep_prob=self.rec_dropout)
            bk_cell = tf.contrib.rnn.DropoutWrapper(tf.nn.rnn_cell.GRUCell(self.p.lstm_dim, name='BW_GRU'),
                                                    output_keep_prob=self.rec_dropout)
            val, state = tf.nn.bidirectional_dynamic_rnn(fw_cell, bk_cell, embeds, sequence_length=self.x_len,
                                                         dtype=tf.float32)

            lstm_out = tf.concat((val[0], val[1]), axis=2)
            lstm_out_dim = self.p.lstm_dim * 2

        de_out = self.GCNLayer(gcn_in=lstm_out, in_dim=lstm_out_dim, gcn_dim=self.p.de_gcn_dim,
                               batch_size=self.total_sents, max_nodes=self.seq_len, max_labels=self.num_deLabel,
                               adj_ind=self.de_adj_ind, adj_data=self.de_adj_data, w_gating=self.p.wGate,
                               num_layers=self.p.de_layers, name="GCN_DE")

        de_out = de_out[-1]
        de_out = tf.concat([lstm_out, de_out], axis=2)
        de_out_dim = self.p.de_gcn_dim + lstm_out_dim

        with tf.variable_scope('Word_attention') as scope:
            wrd_query = tf.get_variable('wrd_query', [de_out_dim, 1],
                                        initializer=tf.contrib.layers.xavier_initializer())
            sent_reps = tf.reshape(
                tf.matmul(
                    tf.reshape(
                        tf.nn.softmax(
                            tf.reshape(
                                tf.matmul(
                                    tf.reshape(tf.tanh(de_out), [self.total_sents * self.seq_len, de_out_dim]),
                                    wrd_query),
                                [self.total_sents, self.seq_len]
                            )),
                        [self.total_sents, 1, self.seq_len]),
                    de_out),
                [self.total_sents, de_out_dim]
            )

            sent_reps = tf.concat([sent_reps, alias_av], axis=1)
            de_out_dim += self.p.alias_dim

        with tf.variable_scope('TypeInfo') as scope:
            pad_type_embed = tf.zeros([1, self.p.type_dim], dtype=tf.float32, name='type_pad')
            _type_embeddings = tf.get_variable('type_embeddings', [self.type_num, self.p.type_dim],
                                               initializer=tf.contrib.layers.xavier_initializer(), trainable=True,
                                               regularizer=self.regularizer)
            type_embeddings = tf.concat([pad_type_embed, _type_embeddings], axis=0)

            subtype = tf.nn.embedding_lookup(type_embeddings, self.input_subtype)
            objtype = tf.nn.embedding_lookup(type_embeddings, self.input_objtype)

            subtype_av = tf.divide(tf.reduce_sum(subtype, axis=1), tf.expand_dims(self.input_subtype_len, axis=1))
            objtype_av = tf.divide(tf.reduce_sum(objtype, axis=1), tf.expand_dims(self.input_objtype_len, axis=1))

            type_info = tf.concat([subtype_av, objtype_av], axis=1)

        with tf.variable_scope('Sentence_attention') as scope:
            sent_atten_q = tf.get_variable('sent_atten_q', [de_out_dim, 1],
                                           initializer=tf.contrib.layers.xavier_initializer())

            def getSentAtten(num):
                num_sents = num[1] - num[0]
                bag_sents = sent_reps[num[0]: num[1]]

                sent_atten_wts = tf.nn.softmax(tf.reshape(tf.matmul(tf.tanh(bag_sents), sent_atten_q), [num_sents]))

                bag_rep_ = tf.reshape(
                    tf.matmul(
                        tf.reshape(sent_atten_wts, [1, num_sents]),
                        bag_sents),
                    [de_out_dim]
                )
                return bag_rep_

            bag_rep = tf.map_fn(getSentAtten, self.sent_num, dtype=tf.float32)

        bag_rep = tf.concat([bag_rep, type_info], axis=1)
        de_out_dim = de_out_dim + self.p.type_dim * 2

        with tf.variable_scope('FC1') as scope:
            w_rel = tf.get_variable('w_rel', [de_out_dim, self.num_class],
                                    initializer=tf.contrib.layers.xavier_initializer(), regularizer=self.regularizer)
            b_rel = tf.get_variable('b_rel', initializer=np.zeros([self.num_class]).astype(np.float32),
                                    regularizer=self.regularizer)
            nn_out = tf.nn.xw_plus_b(bag_rep, w_rel, b_rel)

        with tf.name_scope('Accuracy') as scope:
            prob = tf.nn.softmax(nn_out)
            y_pred = tf.argmax(prob, axis=1)
            y_actual = tf.argmax(self.input_y, axis=1)
            accuracy = tf.reduce_mean(tf.cast(tf.equal(y_pred, y_actual), tf.float32))

        ''' Debugging command:
            Put the below command anywhere and get the values of the tensors (Use TF like PyTorch!)
            res  = debug_nn([de_out], self.create_feed_dict( next(self.getBatches(self.data['train'])) ) ); pdb.set_trace()
        '''
        return nn_out, accuracy

    def __init__(self, params):
        """
        Constructor for the main function. Loads data and creates computation graph.

        Parameters
        ----------
        params:		Hyperparameters of the model

        Returns
        -------
        """
        super(RESIDE, self).__init__(params)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Improving Distantly-Supervised Neural Relation Extraction using Side Information')

    parser.add_argument('-data', dest="dataset", required=True, help='Dataset to use')
    parser.add_argument('-gpu', dest="gpu", default='0', help='GPU to use')
    parser.add_argument('-nGate', dest="wGate", action='store_false', help='Include edgewise-gating in GCN')

    parser.add_argument('-lstm_dim', dest="lstm_dim", default=192, type=int, help='Hidden state dimension of Bi-LSTM')
    parser.add_argument('-pos_dim', dest="pos_dim", default=16, type=int, help='Dimension of positional embeddings')
    parser.add_argument('-type_dim', dest="type_dim", default=50, type=int, help='Type dimension')
    parser.add_argument('-alias_dim', dest="alias_dim", default=32, type=int, help='Alias dimension')
    parser.add_argument('-de_dim', dest="de_gcn_dim", default=16, type=int,
                        help='Hidden state dimension of GCN over dependency tree')

    parser.add_argument('-de_layer', dest="de_layers", default=1, type=int,
                        help='Number of layers in GCN over dependency tree')
    parser.add_argument('-drop', dest="dropout", default=0.8, type=float, help='Dropout for full connected layer')
    parser.add_argument('-rdrop', dest="rec_dropout", default=0.8, type=float, help='Recurrent dropout for LSTM')

    parser.add_argument('-lr', dest="lr", default=0.001, type=float, help='Learning rate')
    parser.add_argument('-l2', dest="l2", default=0.001, type=float, help='L2 regularization')
    parser.add_argument('-epoch', dest="max_epochs", default=2, type=int, help='Max epochs')
    parser.add_argument('-batch', dest="batch_size", default=32, type=int, help='Batch size')
    parser.add_argument('-chunk', dest="chunk_size", default=1000, type=int, help='Chunk size')
    parser.add_argument('-restore', dest="restore", action='store_true',
                        help='Restore from the previous best saved model')
    parser.add_argument('-original', dest="original", action='store_true',
                        help='Si es sobre los datos originales')
    parser.add_argument('-only_eval', dest="only_eval", action='store_true',
                        help='Only Evaluate the pretrained model (skip training)')
    parser.add_argument('-opt', dest="opt", default='adam', help='Optimizer to use for training')

    parser.add_argument('-eps', dest="eps", default=0.00000001, type=float, help='Value of epsilon')
    parser.add_argument('-name', dest="name", default='test_' + str(uuid.uuid4()), help='Name of the run')
    parser.add_argument('-seed', dest="seed", default=1234, type=int, help='Seed for randomization')
    parser.add_argument('-logdir', dest="log_dir", default='./log/', help='Log directory')
    parser.add_argument('-config', dest="config_dir", default='./config/', help='Config directory')
    parser.add_argument('-embed_loc', dest="embed_loc", default='./glove/glove.6B.50d.txt',
                        help='Path of word embedding file')
    parser.add_argument('-embed_dim', dest="embed_dim", default=50, type=int, help='Dimension of embedding')
    args = parser.parse_args()

    if not args.restore: args.name = args.name
    args.seed = int(time.time())
    print(args.seed)
    # Set GPU to use
    set_gpu(args.gpu)

    # Set seed
    tf.set_random_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)

    # Create model computational graph
    model = RESIDE(args)

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    with tf.Session(config=config) as sess:
        sess.run(tf.global_variables_initializer())
        model.fit(sess)
