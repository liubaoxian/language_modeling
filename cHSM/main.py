import time

from rnnlm import *
from utils import TextIterator
from lmkit.utils import load_model, save_model

import logging
from logging.config import fileConfig

fileConfig('../logging_config.ini')
logger = logging.getLogger()
from argparse import ArgumentParser
import sys
import os

lr = 0.001
p = 0.1
NEPOCH = 6

n_input = 50
n_hidden = 50

optimizer = 'adam'

argument = ArgumentParser(usage='it is usage tip', description='no')
argument.add_argument('--model_dir', default='./model/parameters.pkl', type=str,
                      help='trained model file as checkpoints')
argument.add_argument('--reload_dumps', default=0, type=int, help='reload trained model')
argument.add_argument('--train_file', default='../data/wikitext-2/idx_wiki.train.tokens', type=str, help='train dir')
argument.add_argument('--valid_file', default='../data/wikitext-2/idx_wiki.valid.tokens', type=str, help='valid dir')
argument.add_argument('--test_file', default='../data/wikitext-2/idx_wiki.test.tokens', type=str, help='test dir')
argument.add_argument('--node_mask_path', default='node_mask.pkl', type=str, help='node mask pickle file')
argument.add_argument('--prefix_path', default='prefix.pkl', type=str,
                      help='classes and words prefix configures pickle file.')


argument.add_argument('--vocab_size', default=33287, type=int, help='vocab size')
argument.add_argument('--batch_size', default=5, type=int, help='batch size')
argument.add_argument('--rnn_cell', default='gru', type=str, help='recurrent unit type')
argument.add_argument("--save_freq", default=0xffffffff, type=int, help="save frequency")
argument.add_argument('--mode', default='train', type=str, help='train/valid/test')

args = argument.parse_args()

train_datafile = args.train_file
valid_datafile = args.valid_file
test_datafile = args.test_file
n_batch = args.batch_size
vocab_size = args.vocab_size
rnn_cell = args.rnn_cell
prefix_path = args.prefix_path
node_mask_path = args.node_mask_path
model_dir = args.model_dir
reload_dumps = args.reload_dumps

disp_freq = 4
valid_freq = 1000
test_freq = 2000
save_freq = args.save_freq
clip_freq = 9000
pred_freq = 20000


def evaluate(test_data, model):
    cost = 0
    index = 0
    for x, x_mask, y, y_mask in test_data:
        index += 1
        cost += model.test(x, x_mask, y, y_mask, x.shape[1])
    return cost / index


def train(lr):
    # Load data
    logger.info('loading dataset...')

    train_data = TextIterator(train_datafile, prefix_path=prefix_path, n_batch=n_batch)
    valid_data = TextIterator(valid_datafile, prefix_path=prefix_path, n_batch=n_batch)
    test_data = TextIterator(test_datafile, prefix_path=prefix_path, n_batch=n_batch)

    logger.info('building model...')
    model = RNNLM(n_input, n_hidden, vocab_size, rnn_cell=rnn_cell, optimizer=optimizer, p=p,
                  n_class=train_data.n_class, node_maxlen=train_data.node_maxlen, node_mask_path=node_mask_path)

    if os.path.exists(model_dir) and reload_dumps == 1:
        logger.info('loading parameters from: %s' % model_dir)
        model = load_model(model_dir, model)
    else:
        print "init parameters...."
    start = time.time()
    idx = 0
    logger.info('training start...')
    for epoch in xrange(NEPOCH):
        error = 0
        for x, x_mask, y_node, y_mask in train_data:
            idx += 1
            print x.shape
            print x_mask.shape
            print y_node.shape
            print y_mask.shape
            cost,outputlayer = model.train(x, x_mask, y_node, y_mask, lr)
            print cost
            print outputlayer.shape
            print outputlayer
            error += cost
            if np.isnan(cost) or np.isinf(cost):
                print 'NaN Or Inf detected!'
                return -1
            if idx % disp_freq == 0:
                logger.info('epoch: %d idx: %d cost: %f ppl: %f' % (
                epoch, idx, error / disp_freq, np.exp(error / (1.0 * disp_freq))))  # ,'lr:',lr
                error = 0
            if idx % save_freq == 0:
                print 'dumping...'
                save_model('./model/parameters_%.2f.pkl' % (time.time() - start), model)
            if idx % valid_freq == 0:
                logger.info('validing....')
                valid_cost = evaluate(valid_data, model)
                logger.info('valid_cost: %f perplexity: %f' % (valid_cost, np.exp(valid_cost)))
            if idx % test_freq == 0:
                logger.info('testing...')
                test_cost = evaluate(test_data, model)
                logger.info('test cost: %f perplexity: %f' % (test_cost, np.exp(test_cost)))
                # if idx % pred_freq==0:
                # print 'predicting...'
                # prediction=model.predict(x,x_mask,x.shape[1])
                # print prediction[:100]
            '''
            if idx%clip_freq==0 and lr >=1e-2:
                print 'cliping learning rate:',
                lr=lr*0.9
                print lr
            '''
        sys.stdout.flush()

    print "Finished. Time = " + str(time.time() - start)


def test():
    valid_data = TextIterator(valid_datafile, prefix_filepath=prefix_filepath, n_batch=n_batch)
    test_data = TextIterator(test_datafile, prefix_filepath=prefix_filepath, n_batch=n_batch)
    model = RNNLM(n_input, n_hidden, vocabulary_size, cell, optimizer, p, )
    if os.path.isfile(args.model_dir):
        print 'loading pretrained model:', args.model_dir
        model = load_model(args.model_dir, model)
    else:
        print args.model_dir, 'not found'
    mean_cost = evaluate(valid_data, model)
    print 'valid cost:', mean_cost, 'perplexity:', np.exp(mean_cost)  # ,"word_error_rate:",mean_wer
    mean_cost = evaluate(test_data, model)
    print 'test cost:', mean_cost, 'perplexity:', np.exp(mean_cost)


if __name__ == '__main__':
    if args.mode == 'train':
        train(lr=lr)
    elif args.mode == 'testing':
        test()