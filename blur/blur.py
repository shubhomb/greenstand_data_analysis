import cv2
import os
from scipy.stats import skew, kurtosis
import numpy as np
from data.data_management import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from matplotlib import colors
from tools.viz import image_gallery
from sklearn.cluster import dbscan


class BlurDetection ():
    def __init__(self):
        pass
    def lp_variance_max(self, img):
        '''
        Tutorial from https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
        LoG operator returns edges, so low variance means more blurred due to fewer edges.
        Returns per variance per pixel, allowing larger images to not be penalized as blurry.
        :param img: image to process
        :return:
        '''
        if img.ndim > 2:
            print ("Stats measured in grayscale, converting image to grayscale")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lapl = cv2.Laplacian(img, cv2.CV_64F)
        return lapl.var() / np.prod(img.shape) , np.max(lapl)

    def brenner_focus(self, img):
        if img.ndim > 2:
            print ("Stats measured in grayscale, converting image to grayscale")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = img.astype(np.float32)
        dx = img[1:, :] - img[:-1, :]
        dy = img[:, 1:] - img[:, :-1]
        return np.mean([np.max(np.square(dx)), np.max(np.square(dy))])

    def fft_filter(self, img, bw):
        '''
        Low pass filter using 2D FFT
        :param img: image to process
        :param bw: bw (int) low-pass filter bandwidth = freq.shape - bw * 2
        :return: filtered img in [0-1] intensity range.
        '''
        freq = np.fft.fft2(img / np.max(img)) # normalizes image for numerical stability
        mask = np.zeros(freq.shape)
        mask [bw: -bw, bw: -bw] = 1.0

        # mask [mask.shape[0] // 2 - bw : mask.shape[0] // 2 + bw, mask.shape[1] // 2 - bw : mask.shape[1] // 2 + bw] = 1.0
        freq = np.multiply(freq, mask)
        return np.fft.ifft2(freq)



    def hist_stats(self, img):
        '''
        Returns the skew and kurtosis of the grayscale image
        :param img: image to process
        :return: tuple (float, float) of skew and kurtosis respectively
        '''
        if img.ndim > 2:
            print ("Histogram stats measured in grayscale, converting image to grayscale")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        counts, bars = np.histogram(img.flatten(), bins=np.arange(0,256),density=True)
        sk = skew(counts)
        kr = kurtosis(counts)
        return sk, kr

    def entropy_pp(self, img):
        """
        per pixel entropy of a histogram
        :param img: grayscale image to analyze
        :return:
        """
        if img.ndim > 2:
            print ("Entropy per pixel measured in grayscale, converting image to grayscale")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hist = np.histogram(img.flatten(), bins=np.arange(0,255), density=True)
        return -(hist[0] * np.log(np.abs(hist[0]) + 1e-8)).sum()


def viz_blur_stats(images, ids, threshs=None):
    """
    Scatter plot of blurring statistics (Laplacian variance, Laplacian max, and Brenner focus)

    """
    f = plt.figure()
    ax = f.add_subplot(111, projection='3d')
    ax.set_xlabel("var")
    ax.set_ylabel("max")
    ax.set_zlabel("brenner focus")
    blurrer = BlurDetection()
    for i in range(len(images)):
        var, maxz = blurrer.lp_variance_max(images[i])
        fox = blurrer.brenner_focus(images[i])
        if threshs:
            if var > threshs[0] or maxz > threshs[1] or fox < threshs[2]:
                cc = "red"
                alpha = 0.8
                ax.text(var, maxz, fox, ids[i], size=8, zorder=1, color='k', rotation=45)
            else:
                cc = "green"
                alpha = 0.5
        else:
            cc = "green"
            alpha = 0.5

        ax.scatter(var, maxz, fox, c=cc, alpha=alpha)
    plt.show()


def generate_stats(images, ids, viz=True):
    blurrer = BlurDetection()
    stats = {}
    for j in range(len(images)):
        gray = cv2.cvtColor(images[j], cv2.COLOR_BGR2GRAY)
        var, max = blurrer.lp_variance_max(gray)
        entropy = blurrer.entropy_pp(gray)
        sk, kr = blurrer.hist_stats(gray)
        lapl_gray = cv2.convertScaleAbs(cv2.Laplacian(gray, 3))
        lask, lakr = blurrer.hist_stats(lapl_gray)
        focus = blurrer.brenner_focus(gray)
        stats[ids[j]] = (var, max, entropy, sk, kr, lask, lakr, focus)
    stats = pd.DataFrame(stats).T
    stats.columns = ["laplace_var_pp", "laplace_max", "entropy_pp", "gray_skew", "gray_kurt","laplace_skew", "laplace_kurt", "brenner_foc"]
    if viz:
        f, axarr = plt.subplots(len(stats.columns), figsize=(20,10))
        for c in range(len(stats.columns)):
            axarr[c].boxplot(stats.iloc[:,c], vert=False)
            axarr[c].set_title(stats.columns[c])
        plt.show()
    return stats

if __name__=="__main__":
    # homepath = os.getcwd()[:-4]
    # data = GreenstandDataset('nov11data.csv')
    # random_ids = np.loadtxt(os.path.join(homepath, "data/onepercentids.txt"))
    # images = [data.read_image_from_db(os.path.join(homepath, 'data/random_zeroone_percent_db/'), key=int(r)) for r in
    #            random_ids] # len 20
    # titles = [int(idd) for idd in random_ids]
    images = []
    titles = []
    for data_dir in ["jaipur_hanuman_temple_india"]:
        dd = os.path.join(os.path.dirname(os.getcwd()), "data", data_dir)
        extensions = [".jpg", ".png"]
        for f, _, d in os.walk(dd):
            for fil in d:
                fullpath = os.path.join(f, fil)
                if os.path.splitext(fullpath)[1] in extensions:
                    im = cv2.imread(fullpath)
                    images.append(im)
                    titles.append(fil)

    threshs = [0.1, 1000, 5000] # variance max, max min, focus min

    # The thresholds [0.1, 1000, 5000] produce reasonable results. In particular, <0.1 is a "good quality" resolution, 0.1-0.5 seems "ok quality",
    # and greater than that seems a lot
    image_gallery(images, titles)
    viz_blur_stats(images, titles, threshs=threshs)
    stats = generate_stats(images, titles, viz=False)
    # gray excess kurtosis > 3 indicates lighting/shade
    shades = stats[(stats['gray_kurt'] > 3)]["gray_kurt"]
    blurs = stats[(stats['laplace_var_pp'] > threshs[0]) | (stats['brenner_foc'] < threshs[2])]
    print ("Shading Problems:")
    print (shades)
    print ("Blurring Problems:")
    print (blurs)


