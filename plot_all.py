import os
import argparse

import torch
import matplotlib.pyplot as plt

from model import get_model
from train import n_class, data_dir, model_dir, get_model
from attack import get_attack, ATTACK_METHODS
from util.MF_dataset import MF_dataset, MF_dataset_extd
from util.util import visual_and_plot, channel_filename


def main():
    print('| testing %s on GPU #%d with pytorch' % (args.model_name, args.gpu))
    model = get_model(args.model_name, n_class, args.channels)
    print('| loading model file %s... ' % final_model_file, end='')
    model.load_state_dict(torch.load(final_model_file, map_location='cpu'))
    if args.gpu >= 0: model.cuda(args.gpu)
    model = model.eval()
    print('done!')

    assert args.split in ['train', 'val', 'test'], 'split must be "train"|"val"|"test"'
    MF_set   = MF_dataset_extd(data_dir, args.split, have_label=True, img_dir=os.path.join('data', 'MF'))
    MMIF_set = MF_dataset_extd(data_dir, args.split, have_label=True, img_dir=os.path.join('data', 'MMIF'))
    DF_set   = MF_dataset_extd(data_dir, args.split, have_label=True, img_dir=os.path.join('data', 'DIF'))

    images, labels, names = MF_set.get_train_item(args.single)
    images = images.unsqueeze(0)
    labels = labels.unsqueeze(0)

    if args.gpu >= 0:
        images = images.cuda(args.gpu)
        labels = labels.cuda(args.gpu)

    atk_single = get_attack(args, model)
    images_atk = atk_single(images, labels)
    
    logits = model(images)
    logits_atk = model(images_atk)   
    pred = logits.argmax(1)
    pred_atk = logits_atk.argmax(1)

    images = images.to('cpu').squeeze(0)
    
    img_rgb = images[:3].permute(1, 2, 0).detach().numpy()
    img_inf = images[3].detach().numpy()
    
    images = images.permute(1, 2, 0).detach().numpy()

    img_mmif = MMIF_set.get_train_item(args.single)[0].to('cpu').squeeze(0).detach().numpy()
    img_df = DF_set.get_train_item(args.single)[0].to('cpu').squeeze(0).permute(1, 2, 0).detach().numpy()
    
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    ax[0].imshow(images)
    ax[0].set_title('Original Image')
    ax[1].imshow(img_mmif, cmap='gray')
    ax[1].set_title('MMIF Image')
    ax[2].imshow(img_df)
    ax[2].set_title('DF Image')
    plt.show()
    
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    ax[0].imshow(images)
    ax[0].set_title('Original Image')
    ax[1].imshow(img_rgb)
    ax[1].set_title('RGB Image')
    ax[2].imshow(img_inf, cmap='inferno')
    ax[2].set_title('Infrared Image')
    plt.show()
    
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    ax[0].imshow(images)
    ax[0].set_title('Original Image')
    ax[1].imshow(images_atk.to('cpu').squeeze(0).permute(1, 2, 0).detach().numpy())
    ax[1].set_title('Adversarial Image')
    plt.show()
    
    visual_and_plot(images, pred, pred_atk)
    visual_and_plot(images, pred, labels)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run demo with pytorch')
    parser.add_argument('--model_name',  '-M',  type=str, default='SegNet')
    parser.add_argument('--dataset',     '-D',  type=str, default='MF', choices=['MF', 'MMIF', 'DIF'])
    parser.add_argument('--split',       '-sp', type=str, default='test')
    parser.add_argument('--channels',    '-c',  type=int, default=4)
    parser.add_argument('--batch_size',  '-B',  type=int, default=1)
    parser.add_argument('--gpu',         '-G',  type=int, default=0)
    parser.add_argument('--num_workers', '-j',  type=int, default=0)
    parser.add_argument('--single',      '-s',  type=int, default=0)
    parser.add_argument('--shuffle',            action='store_true')
    parser.add_argument('--without_g',          action='store_true')
    parser.add_argument('-atk',           action='store_true')
    parser.add_argument('--method',       type=str,   default='MIFGSM', choices=ATTACK_METHODS)
    parser.add_argument('--eps',          type=float, default=8/255)
    parser.add_argument('--alpha',        type=float, default=1/255)
    parser.add_argument('--steps',        type=int,   default=16)
    parser.add_argument('--mask_channel', type=int,   default=[], nargs='+', help='channels to mask, list of int')
    parser.add_argument('--adv_train',    action='store_true')
    args = parser.parse_args()

    model_dir = os.path.join(model_dir, args.model_name)
    tmp_model, tmp_optim, final_model, log_name = channel_filename(args.channels, adv_train=args.adv_train, set_name=args.dataset, no_g=args.without_g)
    final_model_file = os.path.join(model_dir, final_model)
    if args.model_name != 'DeepLabV3':
        assert os.path.exists(final_model_file), 'model file `%s` do not exist' % (final_model_file)
    
    main()
