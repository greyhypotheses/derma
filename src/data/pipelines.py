"""Module pipelines"""
import typing

import pandas as pd
import tensorflow as tf

import config


class Pipelines:
    """
    Class Pipelines

    Decodes the images that will be fed to a model, and instantiates the image delivery pipeline.  There are 2 options:
    Tensorflow's DataSets and Keras' ImageDataGenerator.  Google's performance exercise suggests that the former is
    much more efficient.
    """

    def __init__(self, rescale: float = 1. / 255):
        """
        :param rescale: image integers scaling factor
        """
        self.rescale = rescale

        variables = config.Config().variables()
        self.rows = variables['images']['rows']
        self.columns = variables['images']['columns']
        self.batch_size = variables['modelling']['batch_size']

    @staticmethod
    def image_decoder(img):
        """
        Image decoder

        :param img:
        :return:
        """

        # Convert the compressed image to a 3D uint8 tensor
        img = tf.image.decode_png(contents=img, channels=3)

        # Use `convert_image_dtype` to convert to floats in the [0,1] range.
        img = tf.image.convert_image_dtype(img, tf.float32)

        # Hence
        return img

    def image_label_pairs(self, filename: str, labelname: str = None):
        """
        Create image & label pairs

        :param filename:
        :param labelname:
        :return:
        """
        img = tf.io.read_file(filename)
        img = self.image_decoder(img)

        if labelname is None:
            return img
        else:
            return img, labelname

    def generator_tensorflow(self, data: pd.DataFrame, labels: typing.List = None):
        """
        Create image delivery pipeline

        :param data: The metadata table of the images
        :param labels: The label columns
        :return:
        """

        # The names of the image files
        filenames = data['url'].values

        # During prediction exercises the input data frame should not include ground truth data
        if labels is None:
            matrices = filenames
        else:
            labelnames = data[labels].values
            matrices = (filenames, labelnames)

        # Hence
        # 'cache/.../log'
        dataset = tf.data.Dataset.from_tensor_slices(matrices)
        dataset = dataset.map(self.image_label_pairs, num_parallel_calls=tf.data.experimental.AUTOTUNE)
        dataset = dataset.cache()        
        dataset = dataset.batch(batch_size=self.batch_size, drop_remainder=False)
        dataset = dataset.repeat()
        dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

        return dataset

    def generator_keras(self, data: pd.DataFrame, labels: typing.List):
        """
        Create image delivery pipeline

        :param data: The metadata table of the images
        :param labels: The label columns
        :return:
        """
        base = tf.keras.preprocessing.image.ImageDataGenerator(rescale=self.rescale)
        return base.flow_from_dataframe(dataframe=data,
                                        directory=None,
                                        x_col='url',
                                        y_col=labels,
                                        target_size=(self.rows, self.columns),
                                        color_mode='rgb',
                                        class_mode='raw',
                                        batch_size=self.batch_size)
