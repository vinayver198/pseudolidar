
"""
This file has been taken from official repo of pseudo lidar
and has been modified as per needs

"""
import argparse
import os
import numpy as np
import kitti_util


def project_disp_to_points(calib, disp, max_high):
    disp[disp < 0] = 0
    baseline = 5.4
    mask = disp > 0
    depth = baseline / (disp + 1. - mask)
    rows, cols = depth.shape
    c, r = np.meshgrid(np.arange(cols), np.arange(rows))
    points = np.stack([c, r, depth])
    points = points.reshape((3, -1))
    points = points.T
    points = points[mask.reshape(-1)]
    cloud = calib.project_image_to_velo(points)
    valid = (cloud[:, 0] >= 0) & (cloud[:, 2] < max_high)
    return cloud[valid]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Lidar ')
    parser.add_argument('--calib_dir', type=str,
                        default='~/kitti_data/training/calib')
    parser.add_argument('--disparity_dir', type=str,
                        default='~/kitti_data/training/disparity')
    parser.add_argument('--save_dir', type=str,
                        default='~/kitti_data/training/pseudo-lidar_velodyne')
    parser.add_argument('--max_high', type=int, default=1)

    args = parser.parse_args()

    assert os.path.isdir(args.disparity_dir)
    assert os.path.isdir(args.calib_dir)

    if not os.path.isdir(args.save_dir):
        os.makedirs(args.save_dir)

    disps = [x for x in os.listdir(args.disparity_dir) if x[-3:] == 'npy']
    disps = sorted(disps)

    for fn in disps:
        predix = fn[:-4]
        calib_file = '{}/{}.txt'.format(args.calib_dir, predix)
        calib = kitti_util.Calibration(calib_file)

        if fn[-3:] == 'npy':
            disp_map = np.load(args.disparity_dir + '/' + fn)
        else:
            assert False

        disp_map = (disp_map*256).astype(np.uint16)/256.
        lidar = project_disp_to_points(calib, disp_map, args.max_high)

        # pad 1 in the indensity dimension
        lidar = np.concatenate([lidar, np.ones((lidar.shape[0], 1))], 1)
        lidar = lidar.astype(np.float32)
        lidar.tofile('{}/{}.bin'.format(args.save_dir, predix))
        print('Finish Depth {}'.format(predix))