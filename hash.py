import cv2
import numpy as np
from scipy.fft import dctn

def hamming_distance(img1_hash, img2_hash):
    '''
    Count number of bits that are different between two binary hashes. In test.py, we show
    this method is ~ 2.5x faster than the ImageHash version
    :param img1_hash: (int) self.hash_size bit hash of first candidate image. Expects decimal input.
    :param img2_hash: (int) self.hash_size bit hash of second candidate image. Expects decimal input.
    :return: (int) number of bits that are not equal in provided hashes
    '''
    if type(img1_hash) != int or type(img2_hash) != int:
        raise ValueError("arguments must be decimal integers, arguments provided are %s, %s" %(type(img1_hash), type(img2_hash)))
    return np.binary_repr(img1_hash ^ img2_hash).count("1")

def preprocess(images):
    '''
    Short method to apply several transformations before hashing procedure.
    :param images: (list) images to transform
    :return: (list) of transformed images corresponding to passed images
    '''
    return [cv2.equalizeHist(
                cv2.cvtColor(
                np.uint8(
                cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)) ,
                cv2.COLOR_BGR2GRAY)) for img in images]  # or convert) for img in images]


class HashCode():
    """
    Object representation to convert between hash code binary, hex, and int representations and compute distance.
    See https://github.com/JohannesBuchner/imagehash for the open-source implementation that
    this class derives from.

    For some intuition: we want image hashes to be as close together as possible for similar looking images. Identical images
    should always produce the exact same hash output. So what we're really trying to do is define similarity of two images.
    Hashes work by finding a unique binary representation. Let us call h(f) be a criterion h over a pixel intensity value f.
    Because each integer has a unique binary representation, only two images with the same h(f) will output the same hash. Note that
    this does not necessarily mean the images are exactly the same but, we can say for large images, this assumption is reasonable,
    and two images with same h(f). The following methods use different h(f) criterion so that h(f1)-h(f2) is larger if f1 - f2 is large
    and smaller if f1 -f2 is small, where f is generally some information vector about the pixel intensity and possibly its location.
    """

    def __init__(self, binary_array):
        self.hash = binary_array

    def __str__(self):
        pass


class ImageHasher():
    """
    Customized image hashing derived from ImageHash open source library, allowing us to modify for
    Greenstand purposes.
    See https://github.com/JohannesBuchner/imagehash for the open-source implementation.
    """
    def __init__(self, hash_size, ):
        self.size = hash_size



    def binary_array_to_int(self, arr):
        '''
        Helper function to take binary bitmask and return sum of 2 ** x for each index x in the flattened arr
        such that arr[x] = 1.
        :param arr: binary array to
        :return:
        '''
        return int(np.sum(np.exp2(np.flatnonzero(arr))))


    def average_hash(self, img):
        '''
        Averge hashing implementation to return hash of bits greater than average of
        pixel intensities.
        :param img: (np.ndarray) the RGB image to find a difference hash function of
        :return:
        '''
        resized = cv2.resize(img, (self.size, self.size), interpolation=cv2.INTER_AREA)
        # following one liner avoids unnecessary variable assignment. The average hash takes the mean grayscal pixel intensity
        # and generates hash from (flattened) indices greater than the mean
        return self.binary_array_to_int(resized > np.mean(resized))

    def difference_hash(self, img):
        '''
        Credit to https://www.pyimagesearch.com/2017/11/27/image-hashing-opencv-python/
        for implementation tutorial.

        :param img: (np.ndarray) the RGB image to find a difference hash function from
        :param hash_size: (int) the number of bits in the hash (ex. setting to 8 yields 2**8=64 bit address)
        :return: (int) 2 ** hash_size bit image hash function returned as int (not hex or binary)
        '''
        resized = cv2.resize(img, (self.size + 1, self.size), interpolation=cv2.INTER_AREA)
        # following one liner avoids unnecessary variable assignment. The difference hash takes the left-right difference
        # of grayscale pixel intensities and generates a hash from the indices
        return self.binary_array_to_int(resized[:, 1:] > resized[:, :-1])


    def dct_hash(self, img):
        '''
        :param img: (np.ndarray) the RGB image to find a difference hash function of
        :param hash_size: (int) the number of bits in the hash (ex. setting to 8 yields 2**8=64 bit address)
        :return: (int) 2 ** hash_size bit image hash function
        '''
        if self.size != 8:
            raise UserWarning("Original DCT was 8 x 8 so size parameter of ImageHash object may be off")
        dct_matx = dctn(img, type=2)[:self.size,:self.size].flatten() # original algorithm selects top 8x8=64
        return self.binary_array_to_int(dct_matx > np.median(dct_matx))



    def marr_hildreth_hash(self, img, std=3, ksize=3):
        '''

        :param img:
        :param std:
        :param ksize:
        :return:
        '''
        resized = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (self.size, self.size), interpolation=cv2.INTER_AREA)
        img = cv2.Laplacian(cv2.GaussianBlur(img, (std,std), 0), kernel_size=ksize)
        # TODO: Finish marr hildreth edge-based hash if others don't work