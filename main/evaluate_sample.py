'''
MiMSI Evalution Utility

Used to evaluate (test) a sample or samples for MSI status based on a tumor/normal vector

@author: John Ziegler
Memorial Sloan Kettering Cancer Center 
Nov. 2018

zieglerj@mskcc.org

(c) 2018 Memorial Sloan Kettering Cancer Center.  This program is free software: you may use, redistribute, 
and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, 
either version 3 or later. See the LICENSE file for details

'''

import numpy as np

import argparse
import torch
import torch.utils.data as data_utils
import torch.optim as optim
from torch.autograd import Variable
from sklearn import metrics

from data.data_loader import MSIBags
from model.mi_msi_model import MSIModel

def evaluate(model, eval_loader, cuda, save, name):
    model.eval()
    result_list = []

    with torch.no_grad():
        for batch_idx, (data, label, _, sample_id) in enumerate(eval_loader):
             
            # Since we're evaluating here we're just using a default label
            # of -1 and ignoring the loss
            bag_label = torch.tensor(int(label[0]))
            if cuda:
                bag_label = bag_label.cuda()
                Variable(bag_label)

            repeat_results = []
            for bag in data:
                if cuda:
                    bag = bag.cuda()
                    bag = Variable(bag)

                # Evaluate the sample
                _, Y_prob, Y_hat = model.calculate_objective(bag, bag_label)

                # Record the result as a probability 
                Y_prob = Y_prob.item()
                repeat_results.append(Y_prob)
             
            result_list.append([sample_id[0], repeat_results])
            
            print(sample_id[0] + "\t" + str(repeat_results) + "\n")

    if save:
        if len(result_list) == 1:
            np.save('./' + sample_id[0] + '_results.npy', repeat_results)
        else:
            np.save('./' + name + '_results.npy', result_list)


def main(saved_model, vector_location, no_cuda, seed, save, name, coverage):
    cuda = not no_cuda and torch.cuda.is_available()

    torch.manual_seed(seed)
    if cuda:
        print('\nGPU is Enabled!')

    print('Evaluating Samples, Lets go!!!')
    loader_kwargs = {'num_workers': 1, 'pin_memory': True} if cuda else {}

    eval_loader = data_utils.DataLoader(MSIBags(vector_location, 100, False, False),
                                                batch_size=1,
                                                shuffle=False,
                                                **loader_kwargs)
    
    model = MSIModel(coverage)
    if cuda:
        model.cuda()
    
    model.load_state_dict(torch.load(saved_model))
    evaluate(model, eval_loader, cuda, save, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MiMSI Sample(s) Evalution Utility')
    parser.add_argument('--no-cuda', action='store_true', default=False, help='Disables CUDA for use off GPU, if this is not specified the utility will check availability of torch.cuda')
    parser.add_argument('--saved-model', default="mimsi_mskcc_impact.model", help='name of the saved model weights to load')
    parser.add_argument('--vector-location', default="./eval", help='location of generated vectors to evaluate')
    parser.add_argument('--save', default=False, action='store_true', help='save the results of the evaluation to a numpy array')
    parser.add_argument('--name', default="test_run_001", help='name of the run, this will be the filename for any saved results')
    parser.add_argument('--seed', type=int, default=2, metavar='S', help='Random Seed (default: 2)')
    parser.add_argument('--coverage', default=50, help="Required coverage for both the tumor and the normal. Any coverage in excess of this limit will be randomly downsampled")


    args = parser.parse_args()
    main(args.saved_model, args.vector_location, args.no_cuda, args.seed, args.save, args.name, args.coverage)
