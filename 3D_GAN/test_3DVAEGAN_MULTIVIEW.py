import torch
from torch import optim
from torch import  nn
from collections import OrderedDict
from utils import make_hyparam_string, save_new_pickle, read_pickle, SavePloat_Voxels, generateZ
import os


from utils import ShapeNetMultiviewDataset, var_or_cuda
from model import _G, _D, _E_MultiView
from lr_sh import  MultiStepLR

import numpy as np
np.random.seed(0)
torch.manual_seed(0)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

def test_3DVAEGAN_MULTIVIEW(args):
    # datset define
    dsets_path = args.input_dir + args.data_dir + "test/"
    print(dsets_path)
    dsets = ShapeNetMultiviewDataset(dsets_path, args)
    dset_loaders = torch.utils.data.DataLoader(dsets, batch_size=args.batch_size, shuffle=True, num_workers=1)

    # model define
    E = _E_MultiView(args)
    G = _G(args)

    G_solver = optim.Adam(G.parameters(), lr=args.g_lr, betas=args.beta)
    E_solver = optim.Adam(E.parameters(), lr=args.g_lr, betas=args.beta)

    if torch.cuda.is_available():
        print("using cuda")
        G.cuda()
        E.cuda()

    pickle_path = "." + args.pickle_dir + '3DVAEGAN_MULTIVIEW_MAX'
    read_pickle(pickle_path, G, G_solver, G, G_solver,E,E_solver)
    recon_loss_total = 0
    for i, (images, model_3d) in enumerate(dset_loaders):

        X = var_or_cuda(model_3d)

        Z_vae, z_mus, z_vars = E(images)
        G_vae = G(Z_vae)

        recon_loss = torch.sum(torch.pow((G_vae - X), 2),dim=(1,2,3))
        print(recon_loss.size())
        print("RECON LOSS ITER: " ,i," - ", torch.mean(recon_loss))
        recon_loss_total+=(recon_loss)
        samples = G_vae.cpu().data[:8].squeeze().numpy()

        image_path = args.output_dir + args.image_dir + '3DVAEGAN_MULTIVIEW_MAX_test'
        if not os.path.exists(image_path):
            os.makedirs(image_path)

        SavePloat_Voxels(samples, image_path, i)
    #print("AVERAGE RECON LOSS: ", recon_loss_total / i)